"""Calibración temporal exploratoria: pasos de simulación vs referencia PSO (GO).

No modifica el motor. No fija α definitivo. No validación experimental.
"""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any, Literal

from go_mb.config import HOMOGENEOUS_WIAM_DIR
from go_mb.io import load_run
from go_mb.models import pso_time_for_fraction
from go_mb.pso_reference import (
    AC_PSO,
    GO_PSO,
    PSO_FORMULA,
    PSO_INVERSE,
    pso_for_material,
)

TEMPORAL_CALIBRATION_CLASSIFICATION = (
    "temporal_calibration_exploratory_not_experimental_validation"
)

# Referencia GO (alias; ver pso_reference.py para GO y AC).
PSO_QE_MG_G = GO_PSO.qe_pso_mg_g
PSO_K2_G_MG_MIN = GO_PSO.k2_g_mg_min
PSO_INVERSE_FORMULA = PSO_INVERSE

DEFAULT_FRACTIONS: list[float] = [
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
]

ReachStatus = Literal["reached", "not_reached"]


def provenance_header(*, campaign_root: Path) -> dict[str, Any]:
    return {
        "classification": TEMPORAL_CALIBRATION_CLASSIFICATION,
        "not_experimental_validation": True,
        "steps_are_not_minutes": True,
        "alpha_status": "exploratory_not_definitive",
        "no_langmuir_optimization": True,
        "motor_unchanged": True,
        "data_source": str(campaign_root),
        "geometry_era": "wiam_geometry",
        "geometry": {
            "mb_side_px": 1,
            "go_side_px": 7,
            "ac_side_px": 2,
            "r_mb_px": 0.5,
            "r_go_px": 3.5,
            "r_ac_px": 1.0,
        },
        "pso_reference_go": {
            "qe_mg_g": GO_PSO.qe_pso_mg_g,
            "k2_g_mg_min": GO_PSO.k2_g_mg_min,
            "formula_qt": PSO_FORMULA,
            "formula_inverse_time": PSO_INVERSE_FORMULA,
        },
        "pso_reference_ac": {
            "qe_mg_g": AC_PSO.qe_pso_mg_g,
            "k2_g_mg_min": AC_PSO.k2_g_mg_min,
            "formula_qt": PSO_FORMULA,
            "formula_inverse_time": PSO_INVERSE_FORMULA,
        },
        "fraction_definition": (
            "Fracción f = qt_sim / qe_PSO del material (GO o AC). "
            "n_sim = primer paso con qt >= f * qe_PSO; sin extrapolación."
        ),
    }


def discover_run_json_paths(campaign_root: Path) -> list[tuple[str, Path]]:
    """(material, json_path) excluyendo estudios agregados."""
    out: list[tuple[str, Path]] = []
    for material, sub in (("GO", "go"), ("AC", "ac")):
        folder = campaign_root / sub
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            name = path.name
            if name.startswith("study_") or name.startswith("aggregated_"):
                continue
            if "sens_grid" not in name and "sens_sigma" not in name and "sens_steps" not in name:
                continue
            out.append((material, path))
    return out


def _run_meta(data: dict[str, Any]) -> dict[str, Any]:
    run = data.get("run", {})
    summary = data.get("summary", {})
    cfg = data.get("config", {})
    return {
        "material": cfg.get("material", "GO"),
        "seed": int(run.get("seed", 0)),
        "sigma_px": float(run.get("sigma_px", 0)),
        "n_steps": int(run.get("n_steps", 0)),
        "final_n_adsorbed": int(summary.get("n_adsorbed", 0)),
        "final_percent_adsorbed": float(summary.get("percent_adsorbed", 0)),
        "final_qt_mg_g": float(summary.get("qfinal_mg_g", 0)),
        "final_n_contacts": int(summary.get("n_contacts", 0)),
        "mass_conservation_ok": bool(summary.get("mass_conservation_ok", True)),
        "json_path": data.get("series_csv", ""),
    }


def first_step_reaching_qt(
    series: list[dict[str, float | int]],
    target_qt: float,
    max_step: int,
) -> int | None:
    """Primer paso (entero) con qt >= objetivo; sin interpolación."""
    for row in series:
        step = int(row["step"])
        if step > max_step:
            break
        if float(row["qt_mg_g"]) >= target_qt:
            return step
    return None


def fraction_crossings_for_run(
    data: dict[str, Any],
    fractions: list[float] | None = None,
) -> list[dict[str, Any]]:
    fractions = fractions or DEFAULT_FRACTIONS
    meta = _run_meta(data)
    material = str(meta["material"])
    series = data.get("series") or []
    max_step = int(meta["n_steps"])
    rows: list[dict[str, Any]] = []

    mat = "GO" if material == "GO" else "AC"
    pso = pso_for_material(mat)  # type: ignore[arg-type]
    for f in fractions:
        target_qt = f * pso.qe_pso_mg_g
        n_sim = first_step_reaching_qt(series, target_qt, max_step)
        status: ReachStatus = "reached" if n_sim is not None else "not_reached"
        row: dict[str, Any] = {
            "material": material,
            "seed": meta["seed"],
            "sigma_px": meta["sigma_px"],
            "n_steps_horizon": max_step,
            "fraction_of_pso_qe": f,
            "target_qt_mg_g": target_qt,
            "qe_pso_mg_g": pso.qe_pso_mg_g,
            "k2_g_mg_min": pso.k2_g_mg_min,
            "reach_status": status,
            "n_sim": n_sim,
            "final_qt_mg_g": meta["final_qt_mg_g"],
            "pso_reference_status": f"{mat.lower()}_pso_reference",
            "t_pso_min": None,
            "alpha_min_per_step": None,
        }
        if status == "reached" and n_sim is not None and n_sim > 0:
            t_pso = pso_time_for_fraction(pso.k2_g_mg_min, pso.qe_pso_mg_g, f)
            if t_pso is not None:
                row["t_pso_min"] = t_pso
                row["alpha_min_per_step"] = t_pso / n_sim
        rows.append(row)
    return rows


def alpha_consistency(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Por corrida: material × sigma × seed × n_steps (alphas con fracción alcanzada)."""
    groups: dict[tuple[str, float, int, int], list[float]] = {}
    reach_counts: dict[tuple[str, float, int, int], list[str]] = {}

    for r in rows:
        key = (
            r["material"],
            float(r["sigma_px"]),
            int(r["seed"]),
            int(r["n_steps_horizon"]),
        )
        reach_counts.setdefault(key, []).append(r["reach_status"])
        alpha = r.get("alpha_min_per_step")
        if alpha is not None:
            groups.setdefault(key, []).append(float(alpha))

    out: list[dict[str, Any]] = []
    for key in sorted(reach_counts.keys()):
        material, sigma, seed, n_steps = key
        alphas = groups.get(key, [])
        reached = sum(1 for s in reach_counts[key] if s == "reached")
        total = len(reach_counts[key])
        entry: dict[str, Any] = {
            "material": material,
            "sigma_px": sigma,
            "seed": seed,
            "n_steps_horizon": n_steps,
            "fractions_total": total,
            "fractions_reached": reached,
            "fractions_not_reached": total - reached,
            "pso_reference_status": f"{material.lower()}_pso_reference",
        }
        if alphas:
            entry["alpha_min"] = min(alphas)
            entry["alpha_max"] = max(alphas)
            entry["alpha_mean"] = statistics.mean(alphas)
            entry["alpha_std"] = statistics.stdev(alphas) if len(alphas) > 1 else 0.0
            mean = entry["alpha_mean"]
            entry["coefficient_of_variation"] = (
                entry["alpha_std"] / mean if mean and mean > 0 else None
            )
            entry["n_alpha_points"] = len(alphas)
        else:
            entry["alpha_min"] = None
            entry["alpha_max"] = None
            entry["alpha_mean"] = None
            entry["alpha_std"] = None
            entry["coefficient_of_variation"] = None
            entry["n_alpha_points"] = 0
        out.append(entry)
    return out


def load_and_analyze_campaign(
    campaign_root: Path,
    fractions: list[float] | None = None,
) -> dict[str, Any]:
    paths = discover_run_json_paths(campaign_root)
    all_crossings: list[dict[str, Any]] = []
    run_summaries: list[dict[str, Any]] = []

    for material, jpath in paths:
        data = load_run(jpath)
        data.setdefault("config", {})["material"] = material
        meta = _run_meta(data)
        meta["json_path"] = str(jpath)
        run_summaries.append(meta)
        all_crossings.extend(fraction_crossings_for_run(data, fractions))

    consistency = alpha_consistency(all_crossings)
    return {
        "provenance": provenance_header(campaign_root=campaign_root),
        "n_runs": len(paths),
        "fractions": fractions or DEFAULT_FRACTIONS,
        "run_summaries": run_summaries,
        "fraction_crossings": all_crossings,
        "alpha_consistency": consistency,
        "note": (
            "α = t_PSO / n_sim es exploratorio. Variación entre fracciones no implica "
            "equivalencia steps↔minutos válida sin revisión humana."
        ),
    }


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for r in rows:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def run_temporal_calibration(
    *,
    campaign_root: Path | None = None,
    output_dir: Path | None = None,
    plot: bool = True,
    fractions: list[float] | None = None,
) -> dict[str, Any]:
    root = campaign_root or Path(HOMOGENEOUS_WIAM_DIR)
    out = output_dir or Path("data/analysis/temporal_calibration")
    out.mkdir(parents=True, exist_ok=True)

    analysis = load_and_analyze_campaign(root, fractions=fractions)
    json_path = out / "temporal_calibration_summary.json"
    json_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    crossings_csv = out / "fraction_crossings.csv"
    alpha_csv = out / "alpha_consistency.csv"
    runs_csv = out / "run_summaries.csv"
    write_csv_rows(crossings_csv, analysis["fraction_crossings"])
    write_csv_rows(alpha_csv, analysis["alpha_consistency"])
    write_csv_rows(runs_csv, analysis["run_summaries"])

    result = {
        "provenance": analysis["provenance"],
        "n_runs": analysis["n_runs"],
        "outputs": {
            "json": str(json_path),
            "fraction_crossings_csv": str(crossings_csv),
            "alpha_consistency_csv": str(alpha_csv),
            "run_summaries_csv": str(runs_csv),
        },
    }

    if plot:
        from go_mb.temporal_calibration_viz import plot_temporal_calibration

        figs = plot_temporal_calibration(analysis, root, out / "figures")
        result["outputs"]["figures"] = figs

    return result
