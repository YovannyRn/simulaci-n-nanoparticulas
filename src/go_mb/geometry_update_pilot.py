"""Piloto de alineación geométrica Wiam vs campaña homogénea anterior.

No validación experimental. No re-ejecuta las 140 corridas homogéneas.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from go_mb.config import (
    GEOMETRY_LEGACY_NOTE,
    SimulationConfig,
    WIAM_AC_SIDE_PX,
    WIAM_GO_SIDE_PX,
    WIAM_MB_SIDE_PX,
    ac_config,
)
from go_mb.io import save_study
from go_mb.sensitivity import sweep_sigma_steps_grid

PILOT_CLASSIFICATION = "geometry_alignment_pilot_not_experimental_validation"

DEFAULT_SIGMA = 1.0
DEFAULT_STEPS = 200
DEFAULT_SEEDS = [1, 2, 3]

DEFAULT_LEGACY_HOMOGENEOUS_ROOT = Path("data/sensitivity/homogeneous_temporal")
PILOT_ROOT = Path("data/sensitivity/geometry_update_pilot")


def _pilot_provenance() -> dict[str, Any]:
    return {
        "geometry_alignment_classification": PILOT_CLASSIFICATION,
        "not_experimental_validation": True,
        "no_langmuir_optimization": True,
        "steps_are_not_minutes": True,
        "pilot_design": {
            "sigma_px": DEFAULT_SIGMA,
            "n_steps": DEFAULT_STEPS,
            "seeds": DEFAULT_SEEDS,
            "materials": ["GO", "AC"],
        },
        "motor_geometry_wiam": {
            "mb_side_px": WIAM_MB_SIDE_PX,
            "go_side_px": WIAM_GO_SIDE_PX,
            "ac_side_px": WIAM_AC_SIDE_PX,
            "r_mb_px": WIAM_MB_SIDE_PX / 2.0,
            "r_go_px": WIAM_GO_SIDE_PX / 2.0,
            "r_ac_px": WIAM_AC_SIDE_PX / 2.0,
            "contact_rule": "dist <= r_MB + r_adsorbente",
        },
        "legacy_reference": {
            "path": str(DEFAULT_LEGACY_HOMOGENEOUS_ROOT),
            "geometry": "MB 5×5; adsorbente 7×7 (GO y AC)",
            "note": GEOMETRY_LEGACY_NOTE,
        },
        "adsorption_unchanged": (
            "apply_adsorption y P_ads provisional no modificados en esta etapa."
        ),
    }


def _legacy_run_path(material: str, seed: int, legacy_root: Path) -> Path:
    sub = "go" if material == "GO" else "ac"
    prefix = "ac_" if material == "AC" else ""
    stem = f"{prefix}sens_grid_sigma_{DEFAULT_SIGMA:g}_steps_{DEFAULT_STEPS}_seed_{seed}"
    return legacy_root / sub / f"{stem}.json"


def _load_legacy_outcomes(
    material: str, seed: int, legacy_root: Path
) -> dict[str, Any] | None:
    path = _legacy_run_path(material, seed, legacy_root)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    run = data.get("run", {})
    cfg = data.get("config", {})
    return {
        "source": str(path),
        "geometry_era": "legacy_homogeneous_mb5_ads7",
        "seed": run.get("seed", seed),
        "sigma_px": run.get("sigma_px", DEFAULT_SIGMA),
        "n_steps": run.get("n_steps", DEFAULT_STEPS),
        "mb_size_px": cfg.get("mb_size_px"),
        "adsorbent_size_px": cfg.get("go_size_px"),
        "n_adsorbed": summary.get("n_adsorbed"),
        "percent_adsorbed": summary.get("percent_adsorbed"),
        "qfinal_mg_g": summary.get("qfinal_mg_g"),
        "n_contacts": summary.get("n_contacts"),
        "m_adsorbed_mg": summary.get("m_adsorbed_mg"),
        "m_free_mg": summary.get("m_free_mg"),
        "mass_conservation_ok": summary.get("mass_conservation_ok"),
    }


def _record_from_study_run(rec: dict[str, Any]) -> dict[str, Any]:
    out = rec.get("outcomes", {})
    exec_p = rec.get("execution_parameters", {})
    return {
        "geometry_era": "wiam_aligned",
        "seed": exec_p.get("seed"),
        "sigma_px": exec_p.get("sigma_px", {}).get("value"),
        "n_steps": exec_p.get("n_steps", {}).get("value"),
        "n_adsorbed": out.get("n_adsorbed"),
        "percent_adsorbed": out.get("percent_adsorbed"),
        "qfinal_mg_g": out.get("qfinal_mg_g"),
        "n_contacts": out.get("n_contacts"),
        "m_adsorbed_mg": out.get("m_adsorbed_mg"),
        "m_free_mg": out.get("m_free_mg"),
        "mass_conservation_ok": out.get("mass_conservation_ok"),
        "paths": rec.get("paths"),
    }


def run_geometry_pilot(
    *,
    output_dir: Path | None = None,
    legacy_root: Path | None = None,
) -> dict[str, Any]:
    legacy_dir = legacy_root or DEFAULT_LEGACY_HOMOGENEOUS_ROOT
    base = output_dir or PILOT_ROOT
    base.mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {"provenance": _pilot_provenance(), "materials": {}}

    for material, cfg in (("GO", SimulationConfig()), ("AC", ac_config())):
        mat_dir = base / material.lower()
        study = sweep_sigma_steps_grid(
            sigmas=[DEFAULT_SIGMA],
            steps_list=[DEFAULT_STEPS],
            seeds=DEFAULT_SEEDS,
            config=cfg,
            output_dir=str(mat_dir),
        )
        study["provenance"] = {
            **study.get("provenance", {}),
            **_pilot_provenance(),
            "material": material,
        }
        study_path = save_study(study, mat_dir, f"study_geometry_pilot_{material.lower()}")
        pilot_rows = [_record_from_study_run(r) for r in study["runs"]]
        comparisons: list[dict[str, Any]] = []
        for row in pilot_rows:
            seed = int(row["seed"])
            legacy_row = _load_legacy_outcomes(material, seed, legacy_dir)
            comp: dict[str, Any] = {
                "material": material,
                "seed": seed,
                "sigma_px": DEFAULT_SIGMA,
                "n_steps": DEFAULT_STEPS,
                "new_geometry": row,
                "legacy_geometry": legacy_row,
            }
            if (
                legacy_row
                and row.get("n_adsorbed") is not None
                and legacy_row.get("n_adsorbed") is not None
            ):
                comp["delta_n_adsorbed"] = int(row["n_adsorbed"]) - int(legacy_row["n_adsorbed"])
                comp["delta_percent"] = float(row["percent_adsorbed"]) - float(
                    legacy_row["percent_adsorbed"]
                )
                comp["delta_qt_mg_g"] = float(row["qfinal_mg_g"]) - float(
                    legacy_row["qfinal_mg_g"]
                )
                comp["delta_contacts"] = int(row["n_contacts"]) - int(legacy_row["n_contacts"])
            comparisons.append(comp)

        comp_json = base / "comparison" / f"legacy_vs_wiam_{material.lower()}.json"
        comp_json.parent.mkdir(parents=True, exist_ok=True)
        comp_json.write_text(json.dumps(comparisons, indent=2), encoding="utf-8")

        results["materials"][material] = {
            "study_path": study_path,
            "n_runs": study["study"]["n_runs"],
            "comparison_json": str(comp_json),
            "comparisons": comparisons,
        }

    all_rows: list[dict[str, Any]] = []
    for material in ("GO", "AC"):
        for c in results["materials"][material]["comparisons"]:
            new = c["new_geometry"]
            leg = c.get("legacy_geometry") or {}
            all_rows.append(
                {
                    "material": material,
                    "seed": c["seed"],
                    "legacy_n_adsorbed": leg.get("n_adsorbed"),
                    "new_n_adsorbed": new.get("n_adsorbed"),
                    "delta_n_adsorbed": c.get("delta_n_adsorbed"),
                    "legacy_percent": leg.get("percent_adsorbed"),
                    "new_percent": new.get("percent_adsorbed"),
                    "legacy_qt": leg.get("qfinal_mg_g"),
                    "new_qt": new.get("qfinal_mg_g"),
                    "legacy_contacts": leg.get("n_contacts"),
                    "new_contacts": new.get("n_contacts"),
                    "new_mass_ok": new.get("mass_conservation_ok"),
                }
            )

    summary_csv = base / "comparison" / "geometry_pilot_legacy_vs_wiam.csv"
    fieldnames = list(all_rows[0].keys()) if all_rows else ["material", "seed"]
    with summary_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)

    summary_json = base / "comparison" / "geometry_pilot_summary.json"
    summary_json.write_text(
        json.dumps(
            {
                "provenance": _pilot_provenance(),
                "per_run": all_rows,
                "note": (
                    "Comparación descriptiva piloto σ=1.0, P=200, seeds 1–3. "
                    "No validación experimental ni ranking de materiales."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    results["comparison"] = {
        "csv": str(summary_csv),
        "json": str(summary_json),
    }
    results["total_runs"] = sum(m["n_runs"] for m in results["materials"].values())
    return results
