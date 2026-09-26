"""Comparación computacional descriptiva GO–MB vs AC–MB desde estudios JSON existentes.

No reejecuta simulaciones. No es validación experimental. No optimiza Langmuir.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from go_mb.io import load_study

MaterialTag = Literal["GO", "AC"]

COMPARISON_CLASSIFICATION = "computational_descriptive_comparison_not_experimental_validation"

DEFAULT_CONFIGURATIONS: list[tuple[float, int]] = [
    (1.0, 200),
    (1.0, 400),
    (1.5, 200),
    (1.5, 400),
]

DEFAULT_INPUTS = {
    "GO": {
        "seeds_study": Path("data/sensitivity/seeds/study_sigma_steps_grid.json"),
        "steps_study_sigma_1_5": Path("data/sensitivity/steps/study_sigma_1.5_steps.json"),
        "steps_study_sigma_1_0": Path(
            "data/sensitivity/stabilization_exploratory/study_stabilization_exploratory.json"
        ),
    },
    "AC": {
        "seeds_study": Path("data/sensitivity/ac/seeds/study_ac_seeds.json"),
        "steps_study_sigma_1_5": Path("data/sensitivity/ac/steps_sigma_1_5/study_ac_sigma_1_5_steps.json"),
        "steps_study_sigma_1_0": Path("data/sensitivity/ac/steps_sigma_1_0/study_ac_sigma_1_0_steps.json"),
    },
}


@dataclass(frozen=True)
class ConfigurationStats:
    material: MaterialTag
    sigma_px: float
    n_steps: int
    n_seeds: int
    n_adsorbed_mean: float
    n_adsorbed_min: int
    n_adsorbed_max: int
    n_adsorbed_spread: int
    percent_adsorbed_mean: float
    qfinal_mg_g_mean: float
    n_contacts_mean: float | None
    all_mass_conserved: bool


@dataclass(frozen=True)
class ComparisonRow:
    sigma_px: float
    n_steps: int
    go: ConfigurationStats
    ac: ConfigurationStats
    delta_n_adsorbed_mean: float
    delta_percent_adsorbed_mean: float
    delta_qfinal_mg_g_mean: float
    delta_n_contacts_mean: float | None
    relative_delta_n_adsorbed_mean: float | None
    relative_delta_qfinal_mg_g_mean: float | None


def _material_from_study(study: dict[str, Any], fallback: MaterialTag) -> MaterialTag:
    mat = study.get("study", {}).get("material") or study.get("provenance", {}).get("material")
    if mat in ("GO", "AC"):
        return mat  # type: ignore[return-value]
    runs = study.get("runs") or []
    if runs and runs[0].get("material") in ("GO", "AC"):
        return runs[0]["material"]  # type: ignore[return-value]
    return fallback


def _rows_for_config(study: dict[str, Any], sigma: float, steps: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in study.get("analysis", {}).get("rows", []):
        if abs(float(row["sigma_px"]) - sigma) < 1e-9 and int(row["n_steps"]) == steps:
            out.append(row)
    if out:
        return out
    for rec in study.get("runs", []):
        ep = rec["execution_parameters"]
        s = float(ep["sigma_px"]["value"])
        st = int(ep["n_steps"]["value"])
        if abs(s - sigma) < 1e-9 and st == steps:
            o = rec["outcomes"]
            out.append(
                {
                    "seed": ep["seed"],
                    "sigma_px": s,
                    "n_steps": st,
                    "n_adsorbed": o["n_adsorbed"],
                    "percent_adsorbed": o["percent_adsorbed"],
                    "qfinal_mg_g": o["qfinal_mg_g"],
                    "n_contacts": o["n_contacts"],
                    "mass_conservation_ok": o["mass_conservation_ok"],
                }
            )
    return out


def stats_for_configuration(
    study: dict[str, Any],
    material: MaterialTag,
    sigma: float,
    steps: int,
) -> ConfigurationStats | None:
    rows = _rows_for_config(study, sigma, steps)
    if not rows:
        return None
    n_ads = [int(r["n_adsorbed"]) for r in rows]
    pct = [float(r["percent_adsorbed"]) for r in rows]
    qt = [float(r["qfinal_mg_g"]) for r in rows]
    contacts = [int(r["n_contacts"]) for r in rows if "n_contacts" in r]
    return ConfigurationStats(
        material=material,
        sigma_px=sigma,
        n_steps=steps,
        n_seeds=len(rows),
        n_adsorbed_mean=sum(n_ads) / len(n_ads),
        n_adsorbed_min=min(n_ads),
        n_adsorbed_max=max(n_ads),
        n_adsorbed_spread=max(n_ads) - min(n_ads),
        percent_adsorbed_mean=sum(pct) / len(pct),
        qfinal_mg_g_mean=sum(qt) / len(qt),
        n_contacts_mean=(sum(contacts) / len(contacts)) if contacts else None,
        all_mass_conserved=all(r.get("mass_conservation_ok", True) for r in rows),
    )


def _relative_delta(delta: float, base: float) -> float | None:
    if abs(base) < 1e-12:
        return None
    return delta / base


def build_comparison_table(
    go_study: dict[str, Any],
    ac_study: dict[str, Any],
    configurations: list[tuple[float, int]] | None = None,
) -> list[ComparisonRow]:
    configs = configurations or DEFAULT_CONFIGURATIONS
    go_mat = _material_from_study(go_study, "GO")
    ac_mat = _material_from_study(ac_study, "AC")
    rows: list[ComparisonRow] = []
    for sigma, steps in configs:
        go_s = stats_for_configuration(go_study, go_mat, sigma, steps)
        ac_s = stats_for_configuration(ac_study, ac_mat, sigma, steps)
        if go_s is None or ac_s is None:
            continue
        d_n = go_s.n_adsorbed_mean - ac_s.n_adsorbed_mean
        d_p = go_s.percent_adsorbed_mean - ac_s.percent_adsorbed_mean
        d_q = go_s.qfinal_mg_g_mean - ac_s.qfinal_mg_g_mean
        d_c: float | None = None
        if go_s.n_contacts_mean is not None and ac_s.n_contacts_mean is not None:
            d_c = go_s.n_contacts_mean - ac_s.n_contacts_mean
        rows.append(
            ComparisonRow(
                sigma_px=sigma,
                n_steps=steps,
                go=go_s,
                ac=ac_s,
                delta_n_adsorbed_mean=d_n,
                delta_percent_adsorbed_mean=d_p,
                delta_qfinal_mg_g_mean=d_q,
                delta_n_contacts_mean=d_c,
                relative_delta_n_adsorbed_mean=_relative_delta(d_n, ac_s.n_adsorbed_mean),
                relative_delta_qfinal_mg_g_mean=_relative_delta(d_q, ac_s.qfinal_mg_g_mean),
            )
        )
    return rows


def seed_variability_from_study(study: dict[str, Any], material: MaterialTag) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in study.get("analysis", {}).get("seed_variability", []):
        items.append({**entry, "material": material})
    return items


def _steps_series_from_study(
    study: dict[str, Any],
    sigma: float,
    seed: int = 1,
) -> list[dict[str, float | int]]:
    """Serie final vs pasos (una semilla) para evolución temporal."""
    points: list[dict[str, float | int]] = []
    for row in study.get("analysis", {}).get("rows", []):
        if abs(float(row["sigma_px"]) - sigma) < 1e-9 and int(row.get("seed", seed)) == seed:
            points.append(
                {
                    "n_steps": int(row["n_steps"]),
                    "n_adsorbed": int(row["n_adsorbed"]),
                    "percent_adsorbed": float(row["percent_adsorbed"]),
                    "qfinal_mg_g": float(row["qfinal_mg_g"]),
                    "n_contacts": int(row["n_contacts"]),
                }
            )
    if points:
        return sorted(points, key=lambda p: int(p["n_steps"]))
    # Estudio tipo grid (p. ej. estabilización GO): filtrar runs
    for rec in study.get("runs", []):
        ep = rec["execution_parameters"]
        if int(ep["seed"]) != seed:
            continue
        if abs(float(ep["sigma_px"]["value"]) - sigma) > 1e-9:
            continue
        o = rec["outcomes"]
        points.append(
            {
                "n_steps": int(ep["n_steps"]["value"]),
                "n_adsorbed": int(o["n_adsorbed"]),
                "percent_adsorbed": float(o["percent_adsorbed"]),
                "qfinal_mg_g": float(o["qfinal_mg_g"]),
                "n_contacts": int(o["n_contacts"]),
            }
        )
    return sorted(points, key=lambda p: int(p["n_steps"]))


def provenance_header(
    *,
    go_seeds_path: Path,
    ac_seeds_path: Path,
    go_steps_paths: dict[str, Path],
    ac_steps_paths: dict[str, Path],
    seeds: list[int],
) -> dict[str, Any]:
    return {
        "comparison_classification": COMPARISON_CLASSIFICATION,
        "not_experimental_validation": True,
        "descriptive_only": True,
        "no_langmuir_selection": True,
        "steps_are_not_minutes": True,
        "no_material_ranking": (
            "No se interpreta GO ni AC como superior/inferior; solo diferencias numéricas descriptivas."
        ),
        "inputs": {
            "GO": {
                "seeds_study": str(go_seeds_path),
                "steps_studies": {k: str(v) for k, v in go_steps_paths.items()},
            },
            "AC": {
                "seeds_study": str(ac_seeds_path),
                "steps_studies": {k: str(v) for k, v in ac_steps_paths.items()},
            },
        },
        "seeds": seeds,
        "configurations": [{"sigma_px": s, "n_steps": p} for s, p in DEFAULT_CONFIGURATIONS],
        "contact_vs_adsorption": "Contactos y Nads se reportan por separado; contacto ≠ adsorción.",
    }


def comparison_report_to_dict(
    table: list[ComparisonRow],
    provenance: dict[str, Any],
    seed_var: list[dict[str, Any]],
    evolution: dict[str, Any],
) -> dict[str, Any]:
    return {
        "provenance": provenance,
        "comparison_table": [
            {
                "sigma_px": r.sigma_px,
                "n_steps": r.n_steps,
                "GO": asdict(r.go),
                "AC": asdict(r.ac),
                "delta_GO_minus_AC": {
                    "n_adsorbed_mean": r.delta_n_adsorbed_mean,
                    "percent_adsorbed_mean": r.delta_percent_adsorbed_mean,
                    "qfinal_mg_g_mean": r.delta_qfinal_mg_g_mean,
                    "n_contacts_mean": r.delta_n_contacts_mean,
                    "relative_n_adsorbed_mean_vs_AC": r.relative_delta_n_adsorbed_mean,
                    "relative_qfinal_mg_g_mean_vs_AC": r.relative_delta_qfinal_mg_g_mean,
                },
            }
            for r in table
        ],
        "seed_variability": seed_var,
        "temporal_evolution_note": (
            "Curvas por número de pasos finales (barridos steps), semilla 1, σ=1.0 y σ=1.5. "
            "No implica trayectorias continuas sincronizadas paso a paso entre materiales."
        ),
        "temporal_evolution": evolution,
    }


def write_comparison_csv(table: list[ComparisonRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sigma_px",
        "n_steps",
        "GO_n_adsorbed_mean",
        "AC_n_adsorbed_mean",
        "delta_n_adsorbed",
        "relative_delta_n_adsorbed_vs_AC",
        "GO_percent_mean",
        "AC_percent_mean",
        "GO_qt_mean",
        "AC_qt_mean",
        "delta_qt",
        "relative_delta_qt_vs_AC",
        "GO_contacts_mean",
        "AC_contacts_mean",
        "delta_contacts",
        "GO_spread",
        "AC_spread",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in table:
            writer.writerow(
                {
                    "sigma_px": r.sigma_px,
                    "n_steps": r.n_steps,
                    "GO_n_adsorbed_mean": r.go.n_adsorbed_mean,
                    "AC_n_adsorbed_mean": r.ac.n_adsorbed_mean,
                    "delta_n_adsorbed": r.delta_n_adsorbed_mean,
                    "relative_delta_n_adsorbed_vs_AC": r.relative_delta_n_adsorbed_mean,
                    "GO_percent_mean": r.go.percent_adsorbed_mean,
                    "AC_percent_mean": r.ac.percent_adsorbed_mean,
                    "GO_qt_mean": r.go.qfinal_mg_g_mean,
                    "AC_qt_mean": r.ac.qfinal_mg_g_mean,
                    "delta_qt": r.delta_qfinal_mg_g_mean,
                    "relative_delta_qt_vs_AC": r.relative_delta_qfinal_mg_g_mean,
                    "GO_contacts_mean": r.go.n_contacts_mean,
                    "AC_contacts_mean": r.ac.n_contacts_mean,
                    "delta_contacts": r.delta_n_contacts_mean,
                    "GO_spread": r.go.n_adsorbed_spread,
                    "AC_spread": r.ac.n_adsorbed_spread,
                }
            )


def run_descriptive_comparison(
    *,
    go_seeds_study: Path | None = None,
    ac_seeds_study: Path | None = None,
    output_dir: Path | None = None,
    plot: bool = True,
) -> dict[str, Any]:
    """Carga estudios existentes, escribe JSON/CSV y figuras comparativas."""
    go_seeds_path = go_seeds_study or DEFAULT_INPUTS["GO"]["seeds_study"]
    ac_seeds_path = ac_seeds_study or DEFAULT_INPUTS["AC"]["seeds_study"]
    out = output_dir or Path("data/comparison/go_vs_ac")
    out.mkdir(parents=True, exist_ok=True)

    go_study = load_study(go_seeds_path)
    ac_study = load_study(ac_seeds_path)
    table = build_comparison_table(go_study, ac_study)
    if len(table) != len(DEFAULT_CONFIGURATIONS):
        missing = set(DEFAULT_CONFIGURATIONS) - {(r.sigma_px, r.n_steps) for r in table}
        raise ValueError(f"Faltan configuraciones en los estudios: {missing}")

    seeds = list(go_study.get("study", {}).get("fixed_parameters", {}).get("seeds", [1, 2, 3, 4, 5]))
    go_steps_15 = load_study(DEFAULT_INPUTS["GO"]["steps_study_sigma_1_5"])
    go_steps_10 = load_study(DEFAULT_INPUTS["GO"]["steps_study_sigma_1_0"])
    ac_steps_15 = load_study(DEFAULT_INPUTS["AC"]["steps_study_sigma_1_5"])
    ac_steps_10 = load_study(DEFAULT_INPUTS["AC"]["steps_study_sigma_1_0"])

    evolution = {
        "sigma_1_0": {
            "GO": _steps_series_from_study(go_steps_10, 1.0, seed=1),
            "AC": _steps_series_from_study(ac_steps_10, 1.0, seed=1),
        },
        "sigma_1_5": {
            "GO": _steps_series_from_study(go_steps_15, 1.5, seed=1),
            "AC": _steps_series_from_study(ac_steps_15, 1.5, seed=1),
        },
    }

    seed_var = seed_variability_from_study(go_study, "GO") + seed_variability_from_study(ac_study, "AC")
    prov = provenance_header(
        go_seeds_path=go_seeds_path,
        ac_seeds_path=ac_seeds_path,
        go_steps_paths={
            "sigma_1_5": DEFAULT_INPUTS["GO"]["steps_study_sigma_1_5"],
            "sigma_1_0": DEFAULT_INPUTS["GO"]["steps_study_sigma_1_0"],
        },
        ac_steps_paths={
            "sigma_1_5": DEFAULT_INPUTS["AC"]["steps_study_sigma_1_5"],
            "sigma_1_0": DEFAULT_INPUTS["AC"]["steps_study_sigma_1_0"],
        },
        seeds=seeds,
    )
    report = comparison_report_to_dict(table, prov, seed_var, evolution)
    json_path = out / "go_vs_ac_descriptive_comparison.json"
    csv_path = out / "go_vs_ac_descriptive_comparison.csv"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_comparison_csv(table, csv_path)

    figures: list[str] = []
    if plot:
        from go_mb.compare_viz import plot_comparison_figures

        figures = plot_comparison_figures(report, table, out / "figures")

    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "figures": figures,
        "comparison_table": report["comparison_table"],
        "provenance": prov,
    }
