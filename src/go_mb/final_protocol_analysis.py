"""Análisis descriptivo P=2000 y propuesta de protocolo (sin motor, sin re-simular)."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any

from go_mb.config import HOMOGENEOUS_WIAM_DIR
from go_mb.io import load_run
from go_mb.temporal_calibration import (
    DEFAULT_FRACTIONS,
    PSO_QE_MG_G,
    discover_run_json_paths,
)

FINAL_PROTOCOL_CLASSIFICATION = (
    "final_protocol_analysis_descriptive_not_experimental_validation"
)

P2000 = 2000
SIGMAS = [1.0, 1.5]
SEEDS = [1, 2, 3, 4, 5]


def provenance_block(
    *,
    campaign_root: Path,
    calibration_root: Path,
) -> dict[str, Any]:
    return {
        "classification": FINAL_PROTOCOL_CLASSIFICATION,
        "not_experimental_validation": True,
        "steps_are_not_minutes": True,
        "alpha_status": "exploratory_not_definitive",
        "no_automatic_sigma_selection": True,
        "no_automatic_steps_selection": True,
        "no_automatic_alpha_fixation": True,
        "motor_unchanged": True,
        "data_sources": {
            "campaign_wiam_geometry": str(campaign_root),
            "temporal_calibration": str(calibration_root),
        },
        "analysis_horizon_steps": P2000,
        "geometry_era": "wiam_geometry",
    }


def _stats(vals: list[float]) -> dict[str, float | None]:
    if not vals:
        return {
            "mean": None,
            "std": None,
            "min": None,
            "max": None,
            "cv_percent": None,
        }
    mean = statistics.mean(vals)
    std = statistics.stdev(vals) if len(vals) > 1 else 0.0
    cv = (std / mean * 100.0) if mean else None
    return {
        "mean": mean,
        "std": std,
        "min": min(vals),
        "max": max(vals),
        "cv_percent": cv,
    }


def _is_p2000_path(path: Path) -> bool:
    return f"_steps_{P2000}_" in path.name


def load_p2000_runs(campaign_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for material, jpath in discover_run_json_paths(campaign_root):
        if not _is_p2000_path(jpath):
            continue
        data = load_run(jpath)
        run = data["run"]
        summary = data["summary"]
        rows.append(
            {
                "material": material,
                "seed": int(run["seed"]),
                "sigma_px": float(run["sigma_px"]),
                "n_steps": int(run["n_steps"]),
                "n_adsorbed": int(summary["n_adsorbed"]),
                "percent_adsorbed": float(summary["percent_adsorbed"]),
                "qt_mg_g": float(summary["qfinal_mg_g"]),
                "n_contacts": int(summary["n_contacts"]),
                "mass_conservation_ok": bool(summary.get("mass_conservation_ok", True)),
                "json_path": str(jpath),
            }
        )
    return rows


def aggregate_material_sigma(p2000: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for material in ("GO", "AC"):
        for sigma in SIGMAS:
            items = [
                r
                for r in p2000
                if r["material"] == material and abs(r["sigma_px"] - sigma) < 1e-9
            ]
            items.sort(key=lambda x: x["seed"])
            entry: dict[str, Any] = {
                "material": material,
                "sigma_px": sigma,
                "n_steps": P2000,
                "n_seeds": len(items),
                "per_seed": items,
                "n_adsorbed": _stats([float(r["n_adsorbed"]) for r in items]),
                "percent_adsorbed": _stats([r["percent_adsorbed"] for r in items]),
                "qt_mg_g": _stats([r["qt_mg_g"] for r in items]),
                "n_contacts": _stats([float(r["n_contacts"]) for r in items]),
            }
            out.append(entry)
    return out


def compare_sigma_descriptive(aggregated: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for material in ("GO", "AC"):
        g15 = next(
            a for a in aggregated if a["material"] == material and a["sigma_px"] == 1.5
        )
        g10 = next(
            a for a in aggregated if a["material"] == material and a["sigma_px"] == 1.0
        )
        m10 = g10["n_adsorbed"]["mean"]
        m15 = g15["n_adsorbed"]["mean"]
        assert m10 is not None and m15 is not None
        rows.append(
            {
                "material": material,
                "metric": "n_adsorbed",
                "mean_sigma_1_0": m10,
                "mean_sigma_1_5": m15,
                "absolute_delta": m15 - m10,
                "relative_delta_percent": ((m15 - m10) / m10 * 100.0) if m10 else None,
                "qt_delta_mean": (g15["qt_mg_g"]["mean"] or 0) - (g10["qt_mg_g"]["mean"] or 0),
                "contacts_delta_mean": (g15["n_contacts"]["mean"] or 0)
                - (g10["n_contacts"]["mean"] or 0),
                "cv_percent_sigma_1_0_nads": g10["n_adsorbed"]["cv_percent"],
                "cv_percent_sigma_1_5_nads": g15["n_adsorbed"]["cv_percent"],
                "note": "Descriptivo σ=1.5 vs σ=1.0; no ranking automático.",
            }
        )
    return rows


def _load_fraction_crossings(calibration_root: Path) -> list[dict[str, Any]]:
    path = calibration_root / "fraction_crossings.csv"
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fraction_reachability_p2000(crossings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sub = [
        r
        for r in crossings
        if int(float(r["n_steps_horizon"])) == P2000
    ]
    for material in ("GO", "AC"):
        for sigma in SIGMAS:
            for seed in SEEDS:
                cells = [
                    r
                    for r in sub
                    if r["material"] == material
                    and abs(float(r["sigma_px"]) - sigma) < 1e-9
                    and int(r["seed"]) == seed
                ]
                reached = [
                    float(r["fraction_of_pso_qe"])
                    for r in cells
                    if r["reach_status"] == "reached"
                ]
                not_reached = [
                    float(r["fraction_of_pso_qe"])
                    for r in cells
                    if r["reach_status"] == "not_reached"
                ]
                rows.append(
                    {
                        "material": material,
                        "sigma_px": sigma,
                        "seed": seed,
                        "fractions_reached": reached,
                        "fractions_not_reached": not_reached,
                        "n_reached": len(reached),
                        "n_not_reached": len(not_reached),
                    }
                )
    return rows


def alpha_analysis_p2000_go(crossings: list[dict[str, Any]]) -> dict[str, Any]:
    sub = [
        r
        for r in crossings
        if r["material"] == "GO"
        and int(float(r["n_steps_horizon"])) == P2000
        and r["reach_status"] == "reached"
        and r.get("alpha_min_per_step")
    ]
    by_sigma_seed: list[dict[str, Any]] = []
    for sigma in SIGMAS:
        for seed in SEEDS:
            alphas = [
                float(r["alpha_min_per_step"])
                for r in sub
                if abs(float(r["sigma_px"]) - sigma) < 1e-9 and int(r["seed"]) == seed
            ]
            st = _stats(alphas)
            by_sigma_seed.append(
                {
                    "sigma_px": sigma,
                    "seed": seed,
                    "n_alpha_points": len(alphas),
                    **{f"alpha_{k}": v for k, v in st.items()},
                }
            )

    by_sigma_fraction: list[dict[str, Any]] = []
    for sigma in SIGMAS:
        for frac in DEFAULT_FRACTIONS:
            alphas = [
                float(r["alpha_min_per_step"])
                for r in sub
                if abs(float(r["sigma_px"]) - sigma) < 1e-9
                and abs(float(r["fraction_of_pso_qe"]) - frac) < 1e-9
            ]
            st = _stats(alphas)
            by_sigma_fraction.append(
                {
                    "sigma_px": sigma,
                    "fraction_of_pso_qe": frac,
                    "n_alpha_points": len(alphas),
                    **{f"alpha_{k}": v for k, v in st.items()},
                }
            )

    return {
        "scope": "GO_only_pso_reference",
        "horizon_steps": P2000,
        "by_sigma_seed": by_sigma_seed,
        "by_sigma_fraction": by_sigma_fraction,
        "note": "α exploratorio; no umbral CV; no α definitivo.",
    }


def candidate_final_protocol() -> dict[str, Any]:
    return {
        "geometry": "Wiam",
        "mb_count": 200,
        "mb_side_px": 1,
        "go_count": 100,
        "go_side_px": 7,
        "ac_side_px": 2,
        "ac_movable": False,
        "go_movable": True,
        "sigma_candidates": SIGMAS,
        "steps_candidates": [200, 400, 600, 800, 1000, 1500, 2000],
        "seeds_explored": SEEDS,
        "max_horizon_analyzed_steps": P2000,
        "p_ads_status": "provisional_computational_not_physical",
        "alpha_status": "exploratory_only_not_motor_parameter",
        "pso_reference": "GO_only_qe_384.6_k2_0.0002",
        "ac_pso_reference": "PSO_reference_not_available_for_AC",
        "human_decisions_still_required": [
            "sigma definitivo para campaña final",
            "horizonte steps definitivo (P=2000 analizado, no elegido)",
            "Nrep campaña final (30 vs 40 u otro)",
            "P_ads físico/bibliográfico",
            "k2 unificado y validez de α como escala temporal",
            "confirmación unidad Co / 100 mg/g vs 100 mg/L",
            "referencia PSO específica para AC si existe",
        ],
    }


def final_campaign_proposal(
    aggregated: list[dict[str, Any]],
    sigma_compare: list[dict[str, Any]],
    alpha_go: dict[str, Any],
) -> dict[str, Any]:
    """Propuesta de diseño basada en datos existentes; no ejecutar."""
    return {
        "status": "proposal_only_not_executed",
        "based_on": "homogeneous_temporal_wiam_geometry + temporal_calibration",
        "recommended_seed_count_range": {
            "observed": len(SEEDS),
            "note": (
                "CV entre seeds en P=2000 documentado en agregados; "
                "campaña 30/40 sigue pendiente de decisión humana."
            ),
        },
        "sigma_candidates_for_final_design": SIGMAS,
        "steps_candidates_for_final_design": [200, 400, 600, 800, 1000, 1500, 2000],
        "materials": ["GO", "AC"],
        "metrics_to_persist": [
            "n_adsorbed",
            "percent_adsorbed",
            "qt_mg_g",
            "n_contacts",
            "mass_conservation_ok",
            "time_series_csv",
            "geometry_snapshot",
            "provenance",
        ],
        "statistics_to_report": [
            "mean",
            "std",
            "min",
            "max",
            "spread",
            "cv_percent",
        ],
        "descriptive_inputs": {
            "p2000_aggregates": aggregated,
            "sigma_comparison": sigma_compare,
            "alpha_go_p2000": alpha_go,
        },
        "limitations": [
            "No validación experimental",
            "PSO GO no transfiere a AC",
            "steps ≠ minutos",
            "α no constante demostrada",
        ],
    }


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
        for r in rows:
            row = dict(r)
            for k, v in row.items():
                if isinstance(v, list):
                    row[k] = ";".join(str(x) for x in v)
            w.writerow(row)


def run_final_protocol_analysis(
    *,
    campaign_root: Path | None = None,
    calibration_root: Path | None = None,
    output_dir: Path | None = None,
    plot: bool = True,
) -> dict[str, Any]:
    camp = campaign_root or Path(HOMOGENEOUS_WIAM_DIR)
    cal = calibration_root or Path("data/analysis/temporal_calibration")
    out = output_dir or Path("data/analysis/final_protocol")
    out.mkdir(parents=True, exist_ok=True)

    p2000 = load_p2000_runs(camp)
    if len(p2000) != 20:
        raise ValueError(f"Se esperaban 20 corridas P=2000, se encontraron {len(p2000)}")

    aggregated = aggregate_material_sigma(p2000)
    sigma_cmp = compare_sigma_descriptive(aggregated)
    crossings = _load_fraction_crossings(cal)
    reach = fraction_reachability_p2000(crossings)
    alpha_go = alpha_analysis_p2000_go(crossings)

    payload: dict[str, Any] = {
        "provenance": provenance_block(campaign_root=camp, calibration_root=cal),
        "p2000_runs": p2000,
        "p2000_material_sigma_aggregates": aggregated,
        "sigma_comparison": sigma_cmp,
        "fraction_reachability_p2000": reach,
        "alpha_analysis_go_p2000": alpha_go,
        "candidate_final_protocol": candidate_final_protocol(),
        "final_campaign_proposal": final_campaign_proposal(aggregated, sigma_cmp, alpha_go),
        "limitations": [
            "Análisis descriptivo; no selección automática de σ, P ni α.",
            "Referencia PSO solo GO; AC sin curva PSO.",
            "Pasos computacionales no equivalen a minutos sin decisión documentada.",
        ],
    }

    json_path = out / "final_protocol_analysis.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    write_csv(out / "p2000_per_seed.csv", p2000)
    write_csv(out / "p2000_aggregate_by_material_sigma.csv", _summary_rows(aggregated))
    write_csv(out / "sigma_comparison.csv", sigma_cmp)
    write_csv(out / "fraction_reachability_p2000.csv", reach)
    write_csv(out / "alpha_go_by_sigma_seed_p2000.csv", alpha_go["by_sigma_seed"])
    write_csv(out / "alpha_go_by_sigma_fraction_p2000.csv", alpha_go["by_sigma_fraction"])

    result = {
        "provenance": payload["provenance"],
        "n_p2000_runs": len(p2000),
        "outputs": {
            "json": str(json_path),
            "p2000_per_seed_csv": str(out / "p2000_per_seed.csv"),
            "p2000_aggregate_csv": str(out / "p2000_aggregate_by_material_sigma.csv"),
            "sigma_comparison_csv": str(out / "sigma_comparison.csv"),
            "fraction_reachability_csv": str(out / "fraction_reachability_p2000.csv"),
            "alpha_sigma_seed_csv": str(out / "alpha_go_by_sigma_seed_p2000.csv"),
            "alpha_sigma_fraction_csv": str(out / "alpha_go_by_sigma_fraction_p2000.csv"),
        },
    }

    if plot:
        from go_mb.final_protocol_viz import plot_final_protocol

        result["outputs"]["figures"] = plot_final_protocol(
            p2000, camp, crossings, out / "figures"
        )

    return result


def _summary_rows(aggregated: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for block in aggregated:
        row: dict[str, Any] = {
            "material": block["material"],
            "sigma_px": block["sigma_px"],
            "n_steps": P2000,
            "n_seeds": block["n_seeds"],
        }
        for metric in ("n_adsorbed", "percent_adsorbed", "qt_mg_g", "n_contacts"):
            for stat in ("mean", "std", "min", "max", "cv_percent"):
                row[f"{metric}_{stat}"] = block[metric][stat]
        rows.append(row)
    return rows
