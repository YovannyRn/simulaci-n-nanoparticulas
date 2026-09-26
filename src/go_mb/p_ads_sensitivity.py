"""Sensibilidad computacional a P_ads (no validación física)."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any

from go_mb.config import SimulationConfig, ac_config, geometry_snapshot
from go_mb.engine import run_simulation
from go_mb.io import save_run, save_study

P_ADS_SENSITIVITY_CLASSIFICATION = "p_ads_sensitivity_computational_not_physical_validation"

PADS_VALUES = [0.25, 0.5, 0.75, 1.0]
SIGMAS = [1.0, 1.5]
SEEDS = [1, 2, 3, 4, 5]
N_STEPS = 2000


def provenance_block() -> dict[str, Any]:
    return {
        "classification": P_ADS_SENSITIVITY_CLASSIFICATION,
        "not_experimental_validation": True,
        "p_ads_are_computational_not_physical": True,
        "geometry_era": "wiam_geometry",
        "design": {
            "p_ads_values": PADS_VALUES,
            "sigma_px": SIGMAS,
            "n_steps": N_STEPS,
            "seeds": SEEDS,
            "materials": ["GO", "AC"],
            "runs_total": len(PADS_VALUES) * len(SIGMAS) * len(SEEDS) * 2,
        },
        "note": (
            "P_ads modifica Bernoulli tras contacto+capacidad. "
            "El detector de contacto es geométrico; sin embargo, P_ads<1 consume RNG "
            "y puede alterar trayectorias → comparar contactos vs P_ads en los datos."
        ),
    }


def validate_p_ads(p_ads: float) -> None:
    if not (0.0 <= p_ads <= 1.0):
        raise ValueError(f"p_ads debe estar en [0, 1], recibido: {p_ads}")


def run_record(result: dict[str, Any], paths: dict[str, str] | None = None) -> dict[str, Any]:
    cfg = result["config"]
    run = result["run"]
    summary = result["summary"]
    p_eff = run.get("p_ads_effective", run.get("p_ads"))
    n_contacts = int(summary["n_contacts"])
    n_events = int(summary.get("n_adsorption_events", summary["n_adsorbed"]))
    return {
        "material": cfg.get("material", "GO"),
        "seed": int(run["seed"]),
        "sigma_px": float(run["sigma_px"]),
        "n_steps": int(run["n_steps"]),
        "p_ads": run.get("p_ads"),
        "p_ads_effective": p_eff,
        "geometry_era": "wiam_geometry",
        "geometry": geometry_snapshot(
            SimulationConfig() if cfg.get("material") == "GO" else ac_config()
        ),
        "n_adsorbed": int(summary["n_adsorbed"]),
        "percent_adsorbed": float(summary["percent_adsorbed"]),
        "qfinal_mg_g": float(summary["qfinal_mg_g"]),
        "m_adsorbed_mg": float(summary["m_adsorbed_mg"]),
        "m_free_mg": float(summary["m_free_mg"]),
        "n_contacts": n_contacts,
        "n_adsorption_events": n_events,
        "contact_to_adsorption_efficiency": (
            n_events / n_contacts if n_contacts > 0 else None
        ),
        "mass_conservation_ok": bool(summary["mass_conservation_ok"]),
        "paths": paths or {},
    }


def aggregate_by_cell(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, float, float], list[dict[str, Any]]] = {}
    for r in records:
        key = (r["material"], float(r["sigma_px"]), float(r["p_ads_effective"]))
        groups.setdefault(key, []).append(r)

    def stats(vals: list[float]) -> dict[str, float | None]:
        if not vals:
            return {"mean": None, "std": None, "min": None, "max": None, "cv_percent": None}
        mean = statistics.mean(vals)
        std = statistics.stdev(vals) if len(vals) > 1 else 0.0
        return {
            "mean": mean,
            "std": std,
            "min": min(vals),
            "max": max(vals),
            "cv_percent": (std / mean * 100.0) if mean else None,
        }

    out: list[dict[str, Any]] = []
    for (material, sigma, p_ads), items in sorted(groups.items()):
        row: dict[str, Any] = {
            "material": material,
            "sigma_px": sigma,
            "p_ads": p_ads,
            "n_seeds": len(items),
            "n_adsorbed": stats([float(i["n_adsorbed"]) for i in items]),
            "percent_adsorbed": stats([i["percent_adsorbed"] for i in items]),
            "qfinal_mg_g": stats([i["qfinal_mg_g"] for i in items]),
            "n_contacts": stats([float(i["n_contacts"]) for i in items]),
            "n_adsorption_events": stats([float(i["n_adsorption_events"]) for i in items]),
            "contact_to_adsorption_efficiency": stats(
                [
                    float(i["contact_to_adsorption_efficiency"])
                    for i in items
                    if i["contact_to_adsorption_efficiency"] is not None
                ]
            ),
            "mass_conservation_ok_all_seeds": all(i["mass_conservation_ok"] for i in items),
        }
        out.append(row)
    return out


def run_p_ads_sensitivity_campaign(
    *,
    output_dir: Path | None = None,
    plot: bool = True,
) -> dict[str, Any]:
    out = output_dir or Path("data/sensitivity/p_ads_sensitivity")
    out.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    for material in ("GO", "AC"):
        cfg = SimulationConfig() if material == "GO" else ac_config()
        mat_dir = out / material.lower()
        mat_dir.mkdir(parents=True, exist_ok=True)
        for sigma in SIGMAS:
            for p_ads in PADS_VALUES:
                validate_p_ads(p_ads)
                for seed in SEEDS:
                    result = run_simulation(
                        config=cfg,
                        seed=seed,
                        sigma_px=sigma,
                        n_steps=N_STEPS,
                        p_ads=p_ads,
                    )
                    stem = f"pads_{p_ads:g}_sigma_{sigma:g}_steps_{N_STEPS}_seed_{seed}"
                    prefix = "ac_" if material == "AC" else ""
                    paths = save_run(result, mat_dir, f"{prefix}{stem}")
                    rec = run_record(result, paths)
                    records.append(rec)

    aggregated = aggregate_by_cell(records)
    study = {
        "provenance": provenance_block(),
        "study": {
            "kind": "p_ads_sensitivity",
            "n_runs": len(records),
        },
        "runs": records,
        "aggregated": aggregated,
        "descriptive_note": (
            "Si Nads cae con P_ads bajo pero contactos se mantienen, "
            "la sensibilidad actúa en conversión contacto→adsorción."
        ),
    }
    study_path = save_study(study, out, "study_p_ads_sensitivity")
    agg_json = out / "aggregated_stats.json"
    agg_json.write_text(json.dumps(aggregated, indent=2), encoding="utf-8")
    write_aggregate_csv(aggregated, out / "aggregated_stats.csv")
    write_records_csv(records, out / "per_run_records.csv")

    result_payload = {
        "provenance": study["provenance"],
        "n_runs": len(records),
        "study_path": study_path,
        "aggregated_stats_path": str(agg_json),
        "per_run_csv": str(out / "per_run_records.csv"),
    }
    if plot:
        from go_mb.p_ads_sensitivity_viz import plot_p_ads_sensitivity

        result_payload["figures"] = plot_p_ads_sensitivity(aggregated, records, out / "figures")
    return result_payload


def write_records_csv(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        return
    keys: list[str] = []
    for r in records:
        for k in r:
            if k not in keys and k not in ("geometry", "paths"):
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in records:
            w.writerow({k: r.get(k) for k in keys})


def write_aggregate_csv(aggregated: list[dict[str, Any]], path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for block in aggregated:
        row = {
            "material": block["material"],
            "sigma_px": block["sigma_px"],
            "p_ads": block["p_ads"],
            "n_seeds": block["n_seeds"],
            "mass_conservation_ok_all_seeds": block["mass_conservation_ok_all_seeds"],
        }
        for metric in (
            "n_adsorbed",
            "percent_adsorbed",
            "qfinal_mg_g",
            "n_contacts",
            "n_adsorption_events",
            "contact_to_adsorption_efficiency",
        ):
            for stat in ("mean", "std", "min", "max", "cv_percent"):
                row[f"{metric}_{stat}"] = block[metric][stat]
        rows.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
