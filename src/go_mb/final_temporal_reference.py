"""Referencia temporal GO/AC, PSO confirmado, S* bibliográfico, P_ads=0.55."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any

from go_mb.config import HOMOGENEOUS_WIAM_DIR
from go_mb.p_ads_055 import (
    aggregate_comparison,
    load_historical_p_ads,
    merge_comparison_records,
    provenance_block as pads055_provenance,
    run_p_ads_055_campaign,
    write_csv,
)
from go_mb.pso_reference import (
    AC_LANGMUIR,
    AC_PSO,
    BIBLIOGRAPHIC_STICKING_S_STAR,
    EXPERIMENTAL_CONDITIONS,
    FINAL_TEMPORAL_CLASSIFICATION,
    GO_LANGMUIR,
    GO_PSO,
    pso_curve_samples,
    pso_fraction_table,
)
from go_mb.temporal_calibration import DEFAULT_FRACTIONS, load_and_analyze_campaign


def _stats(vals: list[float]) -> dict[str, float | None]:
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


def provenance_header(*, campaign_root: Path) -> dict[str, Any]:
    return {
        "classification": FINAL_TEMPORAL_CLASSIFICATION,
        "not_experimental_validation": True,
        "steps_are_not_minutes": True,
        "alpha_status": "exploratory_not_definitive",
        "motor_unchanged": True,
        "data_sources": {
            "homogeneous_wiam_geometry": str(campaign_root),
            "prior_temporal_calibration_dir": "data/analysis/temporal_calibration",
            "p_ads_historical": "data/sensitivity/p_ads_sensitivity",
        },
        "experimental_conditions": EXPERIMENTAL_CONDITIONS,
        "langmuir_reference": {
            "GO": GO_LANGMUIR.__dict__,
            "AC": AC_LANGMUIR.__dict__,
            "note": "Referencia equilibrio; no fuerza simulación.",
        },
        "pso_reference": {
            "GO": {"qe_pso_mg_g": GO_PSO.qe_pso_mg_g, "k2_g_mg_min": GO_PSO.k2_g_mg_min},
            "AC": {"qe_pso_mg_g": AC_PSO.qe_pso_mg_g, "k2_g_mg_min": AC_PSO.k2_g_mg_min},
            "separation": "GO PSO solo para GO; AC PSO solo para AC.",
        },
        "bibliographic_sticking_s_star": BIBLIOGRAPHIC_STICKING_S_STAR,
        "p_ads_055_sensitivity": pads055_provenance(),
    }


def split_crossings(crossings: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    go = [r for r in crossings if r["material"] == "GO"]
    ac = [r for r in crossings if r["material"] == "AC"]
    return go, ac


def alpha_rows_from_crossings(crossings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for r in crossings:
        rows.append(
            {
                "material": r["material"],
                "sigma_px": r["sigma_px"],
                "seed": r["seed"],
                "fraction_of_pso_qe": r["fraction_of_pso_qe"],
                "n_steps_horizon": r["n_steps_horizon"],
                "reach_status": r["reach_status"],
                "n_sim": r["n_sim"],
                "t_pso_min": r.get("t_pso_min"),
                "alpha_min_per_step": r.get("alpha_min_per_step"),
                "target_qt_mg_g": r["target_qt_mg_g"],
                "qe_pso_mg_g": r.get("qe_pso_mg_g"),
            }
        )
    return rows


def aggregate_alpha_by_sigma_fraction(
    crossings: list[dict[str, Any]],
    material: str,
) -> list[dict[str, Any]]:
    sub = [r for r in crossings if r["material"] == material and r["reach_status"] == "reached"]
    groups: dict[tuple[float, float], list[float]] = {}
    for r in sub:
        a = r.get("alpha_min_per_step")
        if a is None:
            continue
        key = (float(r["sigma_px"]), float(r["fraction_of_pso_qe"]))
        groups.setdefault(key, []).append(float(a))

    out: list[dict[str, Any]] = []
    for (sigma, frac), vals in sorted(groups.items()):
        out.append(
            {
                "material": material,
                "sigma_px": sigma,
                "fraction_of_pso_qe": frac,
                "n_seeds": len(vals),
                "alpha": _stats(vals),
            }
        )
    return out


def reachability_summary(crossings: list[dict[str, Any]], *, horizon: int = 2000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sub = [r for r in crossings if int(r["n_steps_horizon"]) == horizon]
    keys = sorted({(r["material"], float(r["sigma_px"]), int(r["seed"])) for r in sub})
    for material, sigma, seed in keys:
        cells = [
            r
            for r in sub
            if r["material"] == material
            and abs(float(r["sigma_px"]) - sigma) < 1e-9
            and int(r["seed"]) == seed
        ]
        reached = [float(c["fraction_of_pso_qe"]) for c in cells if c["reach_status"] == "reached"]
        not_reached = [
            float(c["fraction_of_pso_qe"]) for c in cells if c["reach_status"] == "not_reached"
        ]
        rows.append(
            {
                "material": material,
                "sigma_px": sigma,
                "seed": seed,
                "n_steps_horizon": horizon,
                "fractions_reached": reached,
                "fractions_not_reached": not_reached,
                "n_reached": len(reached),
                "n_not_reached": len(not_reached),
            }
        )
    return rows


def candidate_final_protocol() -> dict[str, Any]:
    return {
        "status": "prepared_for_human_review_not_executed",
        "final_campaign_size": {"GO_replicates": 40, "AC_replicates": 40, "executed": False},
        "geometry_era": "wiam_geometry",
        "mb": {"count": 200, "side_px": 1},
        "go": {"count": 100, "side_px": 7, "movable": True},
        "ac": {"count": 100, "side_px": 2, "movable": False},
        "execution_parameters_still_human_choice": [
            "sigma_px (candidatos explorados: 1.0, 1.5)",
            "n_steps (P=2000 analizado; no elegido automáticamente)",
            "Nrep (40+40 propuesto; no ejecutado)",
            "P_ads (provisional 1.0; sensibilidad 0.5–1.0 y 0.55 contextual)",
            "alpha (exploratorio; no convertir steps↔minutos sin decisión)",
        ],
        "reference_layers": {
            "langmuir": "equilibrio GO/AC confirmado Wiam",
            "pso": "cinética separada GO vs AC",
            "s_star_0_55": "contexto bibliográfico AC; ≠ P_ads",
        },
        "metrics_to_record_in_final_campaign": [
            "n_adsorbed",
            "percent_adsorbed",
            "qfinal_mg_g",
            "n_contacts",
            "n_adsorption_events",
            "mass_conservation_ok",
            "series_qt_vs_step",
            "seed",
            "sigma_px",
            "p_ads_effective",
            "provenance",
        ],
        "statistics": ["mean", "std", "min", "max", "cv_percent"],
        "awaiting": "revisión humana de final_temporal_reference antes de lanzar 80 corridas.",
    }


def run_final_temporal_reference(
    *,
    campaign_root: Path | None = None,
    sensitivity_root: Path | None = None,
    output_dir: Path | None = None,
    plot: bool = True,
    run_pads_055: bool = True,
) -> dict[str, Any]:
    camp = campaign_root or Path(HOMOGENEOUS_WIAM_DIR)
    sens = sensitivity_root or Path("data/sensitivity/p_ads_sensitivity")
    out = output_dir or Path("data/analysis/final_temporal_reference")
    out.mkdir(parents=True, exist_ok=True)

    analysis = load_and_analyze_campaign(camp, fractions=DEFAULT_FRACTIONS)
    crossings = analysis["fraction_crossings"]
    go_x, ac_x = split_crossings(crossings)

    pso_go_table = pso_fraction_table("GO", DEFAULT_FRACTIONS)
    pso_ac_table = pso_fraction_table("AC", DEFAULT_FRACTIONS)
    write_csv(out / "pso_go.csv", pso_go_table + pso_curve_samples("GO"))
    write_csv(out / "pso_ac.csv", pso_ac_table + pso_curve_samples("AC"))

    write_csv(out / "fraction_crossings_go.csv", go_x)
    write_csv(out / "fraction_crossings_ac.csv", ac_x)
    write_csv(out / "alpha_go.csv", alpha_rows_from_crossings(go_x))
    write_csv(out / "alpha_ac.csv", alpha_rows_from_crossings(ac_x))

    pads_records: list[dict[str, Any]] = []
    pads_agg: list[dict[str, Any]] = []
    comparison: list[dict[str, Any]] = []
    if run_pads_055:
        pads_records = run_p_ads_055_campaign(output_dir=out, store_json=True)
        write_csv(out / "p_ads_055_records.csv", pads_records)
        pads_agg = aggregate_comparison(pads_records)
        write_csv(out / "p_ads_055_aggregate.csv", _flatten_agg(pads_agg))
        hist = load_historical_p_ads(sens)
        comparison = merge_comparison_records(hist, pads_records)
        write_csv(out / "p_ads_comparison_050_055_075_100.csv", comparison)

    summary: dict[str, Any] = {
        "provenance": provenance_header(campaign_root=camp),
        "n_campaign_runs_analyzed": analysis["n_runs"],
        "fractions": DEFAULT_FRACTIONS,
        "reachability_p2000": reachability_summary(crossings, horizon=2000),
        "alpha_aggregate_go": aggregate_alpha_by_sigma_fraction(crossings, "GO"),
        "alpha_aggregate_ac": aggregate_alpha_by_sigma_fraction(crossings, "AC"),
        "go_ac_alpha_comparison_note": (
            "Diferencias de α entre GO y AC son descriptivas; "
            "no implican validación física de escala temporal."
        ),
        "p_ads_055": {
            "n_runs": len(pads_records),
            "aggregate": pads_agg,
            "comparison_with_historical": {
                "p_ads_values": [0.5, 0.55, 0.75, 1.0],
                "n_records": len(comparison),
            },
            "mass_conservation_all_ok": all(r["mass_conservation_ok"] for r in pads_records)
            if pads_records
            else None,
        },
        "candidate_final_protocol": candidate_final_protocol(),
        "limitations": [
            "α exploratorio; steps ≠ minutos.",
            "S*=0.55 no sustituye P_ads.",
            "PSO GO y AC no intercambiables.",
            "Simulación 2D discreta no fuerza Langmuir/PSO.",
        ],
    }

    json_path = out / "temporal_reference_summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    result = {
        "provenance": summary["provenance"],
        "outputs": {
            "summary_json": str(json_path),
            "pso_go_csv": str(out / "pso_go.csv"),
            "pso_ac_csv": str(out / "pso_ac.csv"),
            "fraction_crossings_go_csv": str(out / "fraction_crossings_go.csv"),
            "fraction_crossings_ac_csv": str(out / "fraction_crossings_ac.csv"),
            "alpha_go_csv": str(out / "alpha_go.csv"),
            "alpha_ac_csv": str(out / "alpha_ac.csv"),
            "p_ads_055_records_csv": str(out / "p_ads_055_records.csv"),
            "p_ads_055_aggregate_csv": str(out / "p_ads_055_aggregate.csv"),
        },
    }

    if plot:
        from go_mb.final_temporal_reference_viz import plot_final_temporal_reference

        result["outputs"]["figures"] = plot_final_temporal_reference(
            crossings,
            comparison,
            camp,
            out / "figures",
        )

    return result


def _flatten_agg(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for block in blocks:
        row = {
            "material": block["material"],
            "sigma_px": block["sigma_px"],
            "p_ads": block["p_ads"],
            "n_seeds": block["n_seeds"],
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
    return rows
