"""Campaña temporal homogénea GO vs AC (misma malla σ×P×seeds).

Caracterización computacional; no validación experimental.
"""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any, Literal

from go_mb.config import (
    GEOMETRY_LEGACY_NOTE,
    HOMOGENEOUS_LEGACY_DIR,
    HOMOGENEOUS_WIAM_DIR,
    WIAM_AC_SIDE_PX,
    WIAM_GO_SIDE_PX,
    WIAM_MB_SIDE_PX,
    SimulationConfig,
    ac_config,
    geometry_snapshot,
)
from go_mb.io import save_study
from go_mb.sensitivity import (
    STUDY_CLASSIFICATION,
    analyze_study_records,
    sweep_sigma_steps_grid,
)

GeometryEra = Literal["legacy_geometry", "wiam_geometry"]

HOMOGENEOUS_CLASSIFICATION = "homogeneous_temporal_characterization_not_experimental_validation"
WIAM_HOMOGENEOUS_CLASSIFICATION = (
    "homogeneous_temporal_wiam_geometry_not_experimental_validation"
)

DEFAULT_SIGMAS = [1.0, 1.5]
DEFAULT_STEPS = [200, 400, 600, 800, 1000, 1500, 2000]
DEFAULT_SEEDS = [1, 2, 3, 4, 5]


def expected_run_count(
    sigmas: list[float] | None = None,
    steps: list[int] | None = None,
    seeds: list[int] | None = None,
) -> int:
    s = sigmas or DEFAULT_SIGMAS
    p = steps or DEFAULT_STEPS
    sd = seeds or DEFAULT_SEEDS
    return len(s) * len(p) * len(sd)


def _wiam_geometry_block() -> dict[str, Any]:
    return {
        "geometry_era": "wiam_geometry",
        "mb_side_px": WIAM_MB_SIDE_PX,
        "go_side_px": WIAM_GO_SIDE_PX,
        "ac_side_px": WIAM_AC_SIDE_PX,
        "r_mb_px": WIAM_MB_SIDE_PX / 2.0,
        "r_go_px": WIAM_GO_SIDE_PX / 2.0,
        "r_ac_px": WIAM_AC_SIDE_PX / 2.0,
        "contact_threshold_mb_go_px": WIAM_MB_SIDE_PX / 2.0 + WIAM_GO_SIDE_PX / 2.0,
        "contact_threshold_mb_ac_px": WIAM_MB_SIDE_PX / 2.0 + WIAM_AC_SIDE_PX / 2.0,
        "go_movable": True,
        "ac_fixed": True,
        "px_scale_um": 77.4,
        "px_area_um2": 5990.76,
    }


def _provenance_block(
    *,
    sigmas: list[float],
    steps: list[int],
    seeds: list[int],
    geometry_era: GeometryEra,
    wiam_notes: dict[str, str] | None = None,
) -> dict[str, Any]:
    if geometry_era == "wiam_geometry":
        classification = WIAM_HOMOGENEOUS_CLASSIFICATION
        geometry_section: dict[str, Any] = {
            **_wiam_geometry_block(),
            "legacy_reference": {
                "geometry_era": "legacy_geometry",
                "path": HOMOGENEOUS_LEGACY_DIR,
                "note": GEOMETRY_LEGACY_NOTE,
            },
        }
        geometry_note = (
            "Campaña con geometría Wiam confirmada (MB 1×1, GO 7×7, AC 2×2). "
            f"Referencia histórica en {HOMOGENEOUS_LEGACY_DIR}/ (legacy_geometry)."
        )
    else:
        classification = HOMOGENEOUS_CLASSIFICATION
        geometry_section = {
            "geometry_era": "legacy_geometry",
            "note": GEOMETRY_LEGACY_NOTE,
        }
        geometry_note = (
            "Los datos en homogeneous_temporal/ usan geometría legacy MB 5×5, adsorbente 7×7. "
            "Campaña principal actual: homogeneous_temporal_wiam_geometry/."
        )

    block: dict[str, Any] = {
        "homogeneous_temporal_classification": classification,
        "study_classification": STUDY_CLASSIFICATION,
        "not_experimental_validation": True,
        "no_langmuir_optimization": True,
        "steps_are_not_minutes": True,
        "no_physical_p_ads": True,
        "symmetric_design": {
            "sigma_px": sigmas,
            "n_steps": steps,
            "seeds": seeds,
            "materials": ["GO", "AC"],
            "runs_per_material": expected_run_count(sigmas, steps, seeds),
            "total_runs": 2 * expected_run_count(sigmas, steps, seeds),
        },
        "geometry": geometry_section,
        "geometry_note": geometry_note,
        "concentration_note": (
            "Co operativo del motor: 4 mg / 0,04 L = 100 mg/L. "
            "Unidad/frase «100 mg/g» comunicada por Wiam pendiente de confirmación. "
            "No se alteró Co en esta campaña."
        ),
    }
    if wiam_notes:
        block["wiam_documentation"] = wiam_notes
    return block


def aggregate_configuration_stats(study: dict[str, Any]) -> list[dict[str, Any]]:
    """Medias y dispersión por (sigma, steps) sobre seeds."""
    groups: dict[tuple[float, int], list[dict[str, Any]]] = {}
    for row in study.get("analysis", {}).get("rows", []):
        key = (float(row["sigma_px"]), int(row["n_steps"]))
        groups.setdefault(key, []).append(row)

    out: list[dict[str, Any]] = []
    for (sigma, steps), items in sorted(groups.items()):
        n_ads = [int(it["n_adsorbed"]) for it in items]
        pct = [float(it["percent_adsorbed"]) for it in items]
        qt = [float(it["qfinal_mg_g"]) for it in items]
        contacts = [int(it["n_contacts"]) for it in items]
        mass_ok = all(it.get("mass_conservation_ok", True) for it in items)

        def stats(vals: list[float]) -> dict[str, float]:
            return {
                "mean": statistics.mean(vals),
                "std": statistics.stdev(vals) if len(vals) > 1 else 0.0,
                "min": min(vals),
                "max": max(vals),
                "spread": max(vals) - min(vals),
            }

        out.append(
            {
                "sigma_px": sigma,
                "n_steps": steps,
                "n_seeds": len(items),
                "n_adsorbed": stats([float(v) for v in n_ads]),
                "percent_adsorbed": stats(pct),
                "qt_mg_g": stats(qt),
                "n_contacts": stats([float(v) for v in contacts]),
                "mass_conservation_ok_all_seeds": mass_ok,
            }
        )
    return out


def write_aggregated_stats_csv(rows: list[dict[str, Any]], path: Path) -> None:
    """Tabla consolidada: 14 filas (2 σ × 7 P) por material."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sigma_px",
        "n_steps",
        "n_seeds",
        "n_adsorbed_mean",
        "n_adsorbed_std",
        "n_adsorbed_min",
        "n_adsorbed_max",
        "n_adsorbed_spread",
        "percent_mean",
        "percent_std",
        "percent_min",
        "percent_max",
        "percent_spread",
        "qt_mean",
        "qt_std",
        "qt_min",
        "qt_max",
        "qt_spread",
        "contacts_mean",
        "contacts_std",
        "contacts_min",
        "contacts_max",
        "contacts_spread",
        "mass_conservation_ok_all_seeds",
    ]

    def flat(prefix: str, block: dict[str, float]) -> dict[str, float]:
        return {
            f"{prefix}_mean": block["mean"],
            f"{prefix}_std": block["std"],
            f"{prefix}_min": block["min"],
            f"{prefix}_max": block["max"],
            f"{prefix}_spread": block["spread"],
        }

    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            row = {
                "sigma_px": r["sigma_px"],
                "n_steps": r["n_steps"],
                "n_seeds": r["n_seeds"],
                **flat("n_adsorbed", r["n_adsorbed"]),
                **flat("percent", r["percent_adsorbed"]),
                **flat("qt", r["qt_mg_g"]),
                **flat("contacts", r["n_contacts"]),
                "mass_conservation_ok_all_seeds": r["mass_conservation_ok_all_seeds"],
            }
            w.writerow(row)


def _attach_geometry_to_runs(study: dict[str, Any], cfg: SimulationConfig) -> None:
    snap = geometry_snapshot(cfg)
    for rec in study.get("runs", []):
        rec["geometry"] = snap


def run_material_campaign(
    material: str,
    *,
    sigmas: list[float] | None = None,
    steps_list: list[int] | None = None,
    seeds: list[int] | None = None,
    output_dir: Path,
    p_ads: float | None = None,
    geometry_era: GeometryEra = "wiam_geometry",
) -> dict[str, Any]:
    sigmas = sigmas or DEFAULT_SIGMAS
    steps_list = steps_list or DEFAULT_STEPS
    seeds = seeds or DEFAULT_SEEDS
    if material == "AC":
        cfg = ac_config()
    elif material == "GO":
        cfg = SimulationConfig()
    else:
        raise ValueError(f"Material desconocido: {material}")

    output_dir.mkdir(parents=True, exist_ok=True)
    study = sweep_sigma_steps_grid(
        sigmas=sigmas,
        steps_list=steps_list,
        seeds=seeds,
        config=cfg,
        p_ads=p_ads,
        output_dir=str(output_dir),
    )
    _attach_geometry_to_runs(study, cfg)
    study_name = (
        f"study_homogeneous_temporal_wiam_{material.lower()}"
        if geometry_era == "wiam_geometry"
        else f"study_homogeneous_temporal_{material.lower()}"
    )
    study["provenance"] = {
        **study.get("provenance", {}),
        **_provenance_block(
            sigmas=sigmas,
            steps=steps_list,
            seeds=seeds,
            geometry_era=geometry_era,
            wiam_notes={
                "go_visual_px": "7×7 (Wiam)",
                "ac_visual_px": "2×2 (Wiam)",
                "mb_visual_px": "1×1 (Wiam)",
                "px_scale_um": "77,4 µm/px; 5990,76 µm²/px²",
            },
        ),
        "material": material,
        "homogeneous_temporal": True,
    }
    study["study"]["material"] = material
    study["study"]["kind"] = (
        "homogeneous_temporal_wiam_grid"
        if geometry_era == "wiam_geometry"
        else "homogeneous_temporal_grid"
    )
    study["study"]["geometry_era"] = geometry_era
    aggregated = aggregate_configuration_stats(study)
    study_path = save_study(study, output_dir, study_name)
    agg_json = output_dir / "aggregated_stats.json"
    agg_json.write_text(json.dumps(aggregated, indent=2), encoding="utf-8")
    agg_csv = output_dir / "aggregated_stats.csv"
    write_aggregated_stats_csv(aggregated, agg_csv)
    return {
        "material": material,
        "study_path": study_path,
        "aggregated_stats_path": str(agg_json),
        "aggregated_stats_csv": str(agg_csv),
        "n_runs": study["study"]["n_runs"],
        "study": study,
        "aggregated_stats": aggregated,
    }


def build_cross_material_table(
    go_agg: list[dict[str, Any]],
    ac_agg: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ac_by_key = {(r["sigma_px"], r["n_steps"]): r for r in ac_agg}
    rows: list[dict[str, Any]] = []
    for g in go_agg:
        key = (g["sigma_px"], g["n_steps"])
        a = ac_by_key.get(key)
        if not a:
            continue
        rows.append(
            {
                "sigma_px": g["sigma_px"],
                "n_steps": g["n_steps"],
                "GO": g,
                "AC": a,
                "delta_mean_n_adsorbed": g["n_adsorbed"]["mean"] - a["n_adsorbed"]["mean"],
                "delta_mean_percent": g["percent_adsorbed"]["mean"] - a["percent_adsorbed"]["mean"],
                "delta_mean_qt_mg_g": g["qt_mg_g"]["mean"] - a["qt_mg_g"]["mean"],
                "delta_mean_contacts": g["n_contacts"]["mean"] - a["n_contacts"]["mean"],
            }
        )
    return rows


def write_cross_material_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sigma_px",
        "n_steps",
        "GO_n_adsorbed_mean",
        "AC_n_adsorbed_mean",
        "GO_percent_mean",
        "AC_percent_mean",
        "GO_qt_mean",
        "AC_qt_mean",
        "GO_contacts_mean",
        "AC_contacts_mean",
        "delta_n_adsorbed",
        "delta_percent",
        "delta_qt",
        "delta_contacts",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "sigma_px": r["sigma_px"],
                    "n_steps": r["n_steps"],
                    "GO_n_adsorbed_mean": r["GO"]["n_adsorbed"]["mean"],
                    "AC_n_adsorbed_mean": r["AC"]["n_adsorbed"]["mean"],
                    "GO_percent_mean": r["GO"]["percent_adsorbed"]["mean"],
                    "AC_percent_mean": r["AC"]["percent_adsorbed"]["mean"],
                    "GO_qt_mean": r["GO"]["qt_mg_g"]["mean"],
                    "AC_qt_mean": r["AC"]["qt_mg_g"]["mean"],
                    "GO_contacts_mean": r["GO"]["n_contacts"]["mean"],
                    "AC_contacts_mean": r["AC"]["n_contacts"]["mean"],
                    "delta_n_adsorbed": r["delta_mean_n_adsorbed"],
                    "delta_percent": r["delta_mean_percent"],
                    "delta_qt": r["delta_mean_qt_mg_g"],
                    "delta_contacts": r["delta_mean_contacts"],
                }
            )


def _load_legacy_aggregated(material: str, legacy_root: Path) -> list[dict[str, Any]] | None:
    path = legacy_root / ("go" if material == "GO" else "ac") / "aggregated_stats.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_legacy_vs_wiam_comparison(
    wiam_go: list[dict[str, Any]],
    wiam_ac: list[dict[str, Any]],
    legacy_root: Path,
) -> dict[str, Any]:
    """Descriptivo: medias legacy vs Wiam por material × σ × P."""
    rows: list[dict[str, Any]] = []
    for material, wiam_agg in (("GO", wiam_go), ("AC", wiam_ac)):
        legacy_agg = _load_legacy_aggregated(material, legacy_root)
        if not legacy_agg:
            continue
        leg_by = {(r["sigma_px"], r["n_steps"]): r for r in legacy_agg}
        for w in wiam_agg:
            key = (w["sigma_px"], w["n_steps"])
            leg = leg_by.get(key)
            if not leg:
                continue
            rows.append(
                {
                    "material": material,
                    "sigma_px": w["sigma_px"],
                    "n_steps": w["n_steps"],
                    "legacy_geometry_n_adsorbed_mean": leg["n_adsorbed"]["mean"],
                    "wiam_geometry_n_adsorbed_mean": w["n_adsorbed"]["mean"],
                    "delta_n_adsorbed_mean": w["n_adsorbed"]["mean"] - leg["n_adsorbed"]["mean"],
                    "legacy_percent_mean": leg["percent_adsorbed"]["mean"],
                    "wiam_percent_mean": w["percent_adsorbed"]["mean"],
                    "legacy_qt_mean": leg["qt_mg_g"]["mean"],
                    "wiam_qt_mean": w["qt_mg_g"]["mean"],
                    "legacy_contacts_mean": leg["n_contacts"]["mean"],
                    "wiam_contacts_mean": w["n_contacts"]["mean"],
                }
            )
    return {
        "note": (
            "Comparación descriptiva de medias agregadas (5 seeds) legacy_geometry vs "
            "wiam_geometry. No validación experimental."
        ),
        "legacy_path": str(legacy_root),
        "rows": rows,
    }


def write_legacy_vs_wiam_csv(comparison: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = comparison.get("rows", [])
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def run_homogeneous_campaign(
    *,
    base_dir: Path | None = None,
    sigmas: list[float] | None = None,
    steps_list: list[int] | None = None,
    seeds: list[int] | None = None,
    plot: bool = True,
    run_go: bool = True,
    run_ac: bool = True,
    geometry_era: GeometryEra = "wiam_geometry",
    legacy_root: Path | None = None,
) -> dict[str, Any]:
    if base_dir is None:
        base = (
            Path(HOMOGENEOUS_WIAM_DIR)
            if geometry_era == "wiam_geometry"
            else Path(HOMOGENEOUS_LEGACY_DIR)
        )
    else:
        base = base_dir
    sigmas = sigmas or DEFAULT_SIGMAS
    steps_list = steps_list or DEFAULT_STEPS
    seeds = seeds or DEFAULT_SEEDS
    legacy = legacy_root or Path(HOMOGENEOUS_LEGACY_DIR)

    results: dict[str, Any] = {
        "provenance": _provenance_block(
            sigmas=sigmas,
            steps=steps_list,
            seeds=seeds,
            geometry_era=geometry_era,
            wiam_notes={
                "go_visual_px": "7×7 (Wiam)",
                "ac_visual_px": "2×2 (Wiam)",
                "mb_visual_px": "1×1 (Wiam)",
            },
        ),
        "geometry_era": geometry_era,
        "materials": {},
    }
    go_result: dict[str, Any] | None = None
    ac_result: dict[str, Any] | None = None

    if run_go:
        go_result = run_material_campaign(
            "GO",
            sigmas=sigmas,
            steps_list=steps_list,
            seeds=seeds,
            output_dir=base / "go",
            geometry_era=geometry_era,
        )
        results["materials"]["GO"] = {
            k: go_result[k]
            for k in (
                "study_path",
                "aggregated_stats_path",
                "aggregated_stats_csv",
                "n_runs",
            )
        }
    if run_ac:
        ac_result = run_material_campaign(
            "AC",
            sigmas=sigmas,
            steps_list=steps_list,
            seeds=seeds,
            output_dir=base / "ac",
            geometry_era=geometry_era,
        )
        results["materials"]["AC"] = {
            k: ac_result[k]
            for k in (
                "study_path",
                "aggregated_stats_path",
                "aggregated_stats_csv",
                "n_runs",
            )
        }

    if go_result and ac_result:
        cross = build_cross_material_table(
            go_result["aggregated_stats"],
            ac_result["aggregated_stats"],
        )
        comp_dir = base / "comparison"
        comp_dir.mkdir(parents=True, exist_ok=True)
        json_name = (
            "homogeneous_temporal_wiam_go_vs_ac.json"
            if geometry_era == "wiam_geometry"
            else "homogeneous_temporal_go_vs_ac.json"
        )
        csv_name = json_name.replace(".json", ".csv")
        json_path = comp_dir / json_name
        csv_path = comp_dir / csv_name
        payload = {
            "provenance": results["provenance"],
            "cross_material_by_configuration": cross,
            "note": "Diferencias descriptivas (media GO − media AC). No ranking de materiales.",
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        write_cross_material_csv(cross, csv_path)
        results["comparison"] = {"json": str(json_path), "csv": str(csv_path)}
        if plot:
            from go_mb.homogeneous_viz import plot_homogeneous_comparison

            figs = plot_homogeneous_comparison(
                go_result["aggregated_stats"],
                ac_result["aggregated_stats"],
                comp_dir / "figures",
            )
            results["comparison"]["figures"] = figs

        if geometry_era == "wiam_geometry":
            lv = build_legacy_vs_wiam_comparison(
                go_result["aggregated_stats"],
                ac_result["aggregated_stats"],
                legacy,
            )
            lv_json = comp_dir / "legacy_vs_wiam_geometry_comparison.json"
            lv_csv = comp_dir / "legacy_vs_wiam_geometry_comparison.csv"
            lv_json.write_text(
                json.dumps({**lv, "provenance": results["provenance"]}, indent=2),
                encoding="utf-8",
            )
            write_legacy_vs_wiam_csv(lv, lv_csv)
            results["legacy_vs_wiam"] = {"json": str(lv_json), "csv": str(lv_csv)}

    results["total_runs"] = sum(
        results["materials"][m]["n_runs"] for m in results["materials"]
    )
    return results
