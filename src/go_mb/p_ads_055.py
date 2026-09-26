"""Campaña P_ads=0.55 (referencia bibliográfica contextual; no validación física)."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any

from go_mb.config import SimulationConfig, ac_config
from go_mb.engine import run_simulation
from go_mb.io import save_run
from go_mb.p_ads_sensitivity import aggregate_by_cell, run_record, validate_p_ads
from go_mb.pso_reference import PADS_055_CLASSIFICATION

P_ADS_VALUE = 0.55
SIGMAS = [1.0, 1.5]
SEEDS = [1, 2, 3, 4, 5]
N_STEPS = 2000
COMPARE_PADS = [0.5, 0.55, 0.75, 1.0]


def provenance_block() -> dict[str, Any]:
    return {
        "classification": PADS_055_CLASSIFICATION,
        "p_ads": P_ADS_VALUE,
        "not_equal_to_bibliographic_s_star": True,
        "s_star_is_context_only": True,
        "n_runs": len(SIGMAS) * len(SEEDS) * 2,
    }


def _assert_mass(result: dict[str, Any]) -> None:
    summary = result["summary"]
    if summary.get("mass_conservation_ok", True):
        return
    run = result["run"]
    cfg = result["config"]
    raise RuntimeError(
        "Conservación de masa fallida: "
        f"material={cfg.get('material')} seed={run.get('seed')} "
        f"sigma={run.get('sigma_px')} p_ads={run.get('p_ads')} "
        f"m_init={summary.get('m_total_mg')} m_final="
        f"{summary.get('m_adsorbed_mg', 0) + summary.get('m_free_mg', 0)}"
    )


def run_p_ads_055_campaign(
    *,
    output_dir: Path,
    store_json: bool = True,
) -> list[dict[str, Any]]:
    validate_p_ads(P_ADS_VALUE)
    records: list[dict[str, Any]] = []
    run_dir = output_dir / "p_ads_055_runs"
    run_dir.mkdir(parents=True, exist_ok=True)

    for material in ("GO", "AC"):
        cfg = SimulationConfig() if material == "GO" else ac_config()
        sub = run_dir / material.lower()
        sub.mkdir(parents=True, exist_ok=True)
        for sigma in SIGMAS:
            for seed in SEEDS:
                result = run_simulation(
                    config=cfg,
                    seed=seed,
                    sigma_px=sigma,
                    n_steps=N_STEPS,
                    p_ads=P_ADS_VALUE,
                )
                _assert_mass(result)
                paths = None
                if store_json:
                    stem = f"pads_{P_ADS_VALUE:g}_sigma_{sigma:g}_steps_{N_STEPS}_seed_{seed}"
                    prefix = "ac_" if material == "AC" else ""
                    paths = save_run(result, sub, f"{prefix}{stem}")
                records.append(run_record(result, paths))
    return records


def load_historical_p_ads(
    sensitivity_root: Path,
    *,
    p_ads_values: list[float] | None = None,
) -> list[dict[str, Any]]:
    csv_path = sensitivity_root / "per_run_records.csv"
    if not csv_path.is_file():
        return []
    want = set(p_ads_values or COMPARE_PADS)
    rows: list[dict[str, Any]] = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if int(row["n_steps"]) != N_STEPS:
                continue
            p = float(row["p_ads_effective"])
            if p not in want and abs(p - 0.55) > 1e-9:
                continue
            rows.append(
                {
                    "material": row["material"],
                    "seed": int(row["seed"]),
                    "sigma_px": float(row["sigma_px"]),
                    "n_steps": int(row["n_steps"]),
                    "p_ads_effective": p,
                    "n_adsorbed": int(row["n_adsorbed"]),
                    "percent_adsorbed": float(row["percent_adsorbed"]),
                    "qfinal_mg_g": float(row["qfinal_mg_g"]),
                    "n_contacts": int(row["n_contacts"]),
                    "n_adsorption_events": int(row["n_adsorption_events"]),
                    "contact_to_adsorption_efficiency": float(row["contact_to_adsorption_efficiency"])
                    if row.get("contact_to_adsorption_efficiency")
                    else None,
                    "mass_conservation_ok": row.get("mass_conservation_ok", "True") == "True",
                    "source": "historical_p_ads_sensitivity",
                }
            )
    return rows


def merge_comparison_records(
    historical: list[dict[str, Any]],
    new_055: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for r in historical:
        if abs(float(r["p_ads_effective"]) - 0.55) < 1e-9:
            continue
        merged.append(r)
    for r in new_055:
        merged.append(
            {
                "material": r["material"],
                "seed": r["seed"],
                "sigma_px": r["sigma_px"],
                "n_steps": r["n_steps"],
                "p_ads_effective": float(r["p_ads_effective"]),
                "n_adsorbed": r["n_adsorbed"],
                "percent_adsorbed": r["percent_adsorbed"],
                "qfinal_mg_g": r["qfinal_mg_g"],
                "n_contacts": r["n_contacts"],
                "n_adsorption_events": r["n_adsorption_events"],
                "contact_to_adsorption_efficiency": r.get("contact_to_adsorption_efficiency"),
                "mass_conservation_ok": r["mass_conservation_ok"],
                "source": "p_ads_055_campaign",
            }
        )
    return merged


def aggregate_comparison(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Misma forma que aggregate_by_cell pero con p_ads en COMPARE_PADS."""
    adapted = [
        {
            **r,
            "p_ads_effective": r["p_ads_effective"],
        }
        for r in records
    ]
    return aggregate_by_cell(adapted)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
