"""Campaña final autorizada GO vs AC (40+40 seeds)."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any

from go_mb.config import SimulationConfig, ac_config
from go_mb.engine import run_simulation
from go_mb.io import load_run, save_run
from go_mb.pso_reference import (
    AC_LANGMUIR,
    AC_PSO,
    BIBLIOGRAPHIC_STICKING_S_STAR,
    EXPERIMENTAL_CONDITIONS,
    GO_LANGMUIR,
    GO_PSO,
)
from go_mb.stats import confidence_interval_95

FINAL_CAMPAIGN_CLASSIFICATION = "final_campaign_wiam_geometry_sigma1.5_P2000_Pads1"

SIGMA_PX = 1.5
N_STEPS = 2000
P_ADS = 1.0
GO_SEEDS = list(range(1, 41))
AC_SEEDS = list(range(1, 41))
N_RUNS = len(GO_SEEDS) + len(AC_SEEDS)

METRICS_FOR_STATS = (
    "n_adsorbed",
    "percent_adsorbed",
    "qfinal_mg_g",
    "n_contacts",
    "n_adsorption_events",
    "contact_to_adsorption_efficiency",
    "m_adsorbed_mg",
    "m_free_mg",
)


def provenance_block() -> dict[str, Any]:
    return {
        "classification": FINAL_CAMPAIGN_CLASSIFICATION,
        "not_experimental_validation": True,
        "computational_final_campaign": True,
        "geometry_era": "wiam_geometry",
        "protocol": {
            "sigma_px": SIGMA_PX,
            "n_steps": N_STEPS,
            "p_ads": P_ADS,
            "p_ads_interpretation": "computational_adsorption_rule_not_experimental_sticking",
            "go_seeds": GO_SEEDS,
            "ac_seeds": AC_SEEDS,
            "n_runs": N_RUNS,
            "mb_units": 200,
            "go_units": 100,
            "ac_units": 100,
            "mb_side_px": 1,
            "go_side_px": 7,
            "ac_side_px": 2,
        },
        "experimental_conditions": EXPERIMENTAL_CONDITIONS,
        "langmuir_reference": {"GO": GO_LANGMUIR.__dict__, "AC": AC_LANGMUIR.__dict__},
        "pso_reference": {
            "GO": {"qe_pso_mg_g": GO_PSO.qe_pso_mg_g, "k2_g_mg_min": GO_PSO.k2_g_mg_min},
            "AC": {"qe_pso_mg_g": AC_PSO.qe_pso_mg_g, "k2_g_mg_min": AC_PSO.k2_g_mg_min},
            "note": "Referencia cinética por material; steps ≠ minutos.",
        },
        "bibliographic_sticking_s_star_context_only": BIBLIOGRAPHIC_STICKING_S_STAR,
        "alpha_status": "exploratory_temporal_scale_not_motor_parameter",
        "steps_are_not_minutes": True,
        "s_star_not_substituted_for_p_ads": True,
    }


def _assert_mass(result: dict[str, Any]) -> None:
    summary = result["summary"]
    if summary.get("mass_conservation_ok", True):
        return
    run = result["run"]
    cfg = result["config"]
    m0 = float(summary.get("m_total_mg", cfg.get("m_mb_mg", 4.0)))
    m1 = float(summary.get("m_adsorbed_mg", 0)) + float(summary.get("m_free_mg", 0))
    raise RuntimeError(
        "Conservación de masa fallida — campaña detenida: "
        f"material={cfg.get('material')} seed={run.get('seed')} "
        f"sigma={run.get('sigma_px')} p_ads={run.get('p_ads_effective', P_ADS)} "
        f"masa_inicial_mg={m0} masa_final_mg={m1} diferencia_mg={m1 - m0}"
    )


def run_record(result: dict[str, Any], paths: dict[str, str] | None = None) -> dict[str, Any]:
    cfg = result["config"]
    run = result["run"]
    summary = result["summary"]
    n_contacts = int(summary["n_contacts"])
    n_events = int(summary.get("n_adsorption_events", summary["n_adsorbed"]))
    material = str(cfg.get("material", "GO"))
    return {
        "material": material,
        "seed": int(run["seed"]),
        "sigma_px": float(run["sigma_px"]),
        "n_steps": int(run["n_steps"]),
        "p_ads": run.get("p_ads"),
        "p_ads_effective": float(run.get("p_ads_effective", P_ADS)),
        "temperature_c": EXPERIMENTAL_CONDITIONS["temperature_c"],
        "ph": EXPERIMENTAL_CONDITIONS["ph"],
        "m_mb_initial_mg": EXPERIMENTAL_CONDITIONS["m_mb_mg"],
        "m_adsorbent_mg": EXPERIMENTAL_CONDITIONS["m_adsorbent_mg"],
        "volume_ml": EXPERIMENTAL_CONDITIONS["volume_ml"],
        "c0_mg_l": EXPERIMENTAL_CONDITIONS["c0_mg_l"],
        "n_adsorbed": int(summary["n_adsorbed"]),
        "n_free": int(summary.get("n_free", 200 - summary["n_adsorbed"])),
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
        "final_state": {
            "n_adsorbed": int(summary["n_adsorbed"]),
            "percent_adsorbed": float(summary["percent_adsorbed"]),
            "qfinal_mg_g": float(summary["qfinal_mg_g"]),
        },
        "provenance_classification": FINAL_CAMPAIGN_CLASSIFICATION,
        "json_path": (paths or {}).get("json", ""),
        "series_csv": (paths or {}).get("csv", ""),
    }


def extended_stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "cv_percent": None,
            "percentile_25": None,
            "percentile_75": None,
        }
    mean = statistics.mean(values)
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    qs = statistics.quantiles(values, n=4) if len(values) >= 2 else [values[0], values[0], values[0]]
    out: dict[str, float | None] = {
        "mean": mean,
        "median": statistics.median(values),
        "std": std,
        "min": min(values),
        "max": max(values),
        "cv_percent": (std / mean * 100.0) if mean else None,
        "percentile_25": qs[0] if len(values) >= 2 else values[0],
        "percentile_75": qs[2] if len(values) >= 4 else qs[-1],
    }
    if len(values) >= 2:
        out["ci95"] = confidence_interval_95(values)
    return out


def aggregate_material(records: list[dict[str, Any]], material: str) -> dict[str, Any]:
    sub = [r for r in records if r["material"] == material]
    block: dict[str, Any] = {
        "material": material,
        "n_seeds": len(sub),
        "seeds": sorted(r["seed"] for r in sub),
        "mass_conservation_ok_all": all(r["mass_conservation_ok"] for r in sub),
    }
    for metric in METRICS_FOR_STATS:
        vals = [float(r[metric]) for r in sub if r.get(metric) is not None]
        block[metric] = extended_stats(vals)
    return block


def comparison_go_ac(agg_go: dict[str, Any], agg_ac: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in METRICS_FOR_STATS:
        g = agg_go.get(metric, {})
        a = agg_ac.get(metric, {})
        rows.append(
            {
                "metric": metric,
                "go_mean": g.get("mean"),
                "ac_mean": a.get("mean"),
                "go_std": g.get("std"),
                "ac_std": a.get("std"),
                "go_cv_percent": g.get("cv_percent"),
                "ac_cv_percent": a.get("cv_percent"),
                "go_median": g.get("median"),
                "ac_median": a.get("median"),
                "go_min": g.get("min"),
                "go_max": g.get("max"),
                "ac_min": a.get("min"),
                "ac_max": a.get("max"),
                "go_p25": g.get("percentile_25"),
                "go_p75": g.get("percentile_75"),
                "ac_p25": a.get("percentile_25"),
                "ac_p75": a.get("percentile_75"),
                "delta_mean_go_minus_ac": (
                    (g.get("mean") or 0) - (a.get("mean") or 0)
                    if g.get("mean") is not None and a.get("mean") is not None
                    else None
                ),
                "note": "Comparación descriptiva; no ranking causal.",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys and not isinstance(r[k], (dict, list)):
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def flatten_aggregate_csv(agg: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "material": agg["material"],
        "n_seeds": agg["n_seeds"],
        "mass_conservation_ok_all": agg["mass_conservation_ok_all"],
    }
    for metric in METRICS_FOR_STATS:
        st = agg.get(metric, {})
        for k, v in st.items():
            if k == "ci95" and isinstance(v, dict):
                for ck, cv in v.items():
                    row[f"{metric}_ci95_{ck}"] = cv
            elif k not in ("ci95",):
                row[f"{metric}_{k}"] = v
    return row


def run_final_campaign(
    *,
    output_dir: Path | None = None,
    plot: bool = True,
    go_seeds: list[int] | None = None,
    ac_seeds: list[int] | None = None,
) -> dict[str, Any]:
    out = output_dir or Path("data/final_campaign")
    out.mkdir(parents=True, exist_ok=True)
    go_seeds = go_seeds if go_seeds is not None else GO_SEEDS
    ac_seeds = ac_seeds if ac_seeds is not None else AC_SEEDS

    records: list[dict[str, Any]] = []
    run_paths: list[tuple[str, Path]] = []

    for material, seeds, cfg in (
        ("GO", go_seeds, SimulationConfig()),
        ("AC", ac_seeds, ac_config()),
    ):
        sub = out / material.lower()
        sub.mkdir(parents=True, exist_ok=True)
        for seed in seeds:
            result = run_simulation(
                config=cfg,
                seed=seed,
                sigma_px=SIGMA_PX,
                n_steps=N_STEPS,
                p_ads=P_ADS,
            )
            _assert_mass(result)
            prefix = "ac_" if material == "AC" else ""
            stem = f"final_sigma_{SIGMA_PX:g}_steps_{N_STEPS}_seed_{seed}"
            paths = save_run(result, sub, f"{prefix}{stem}")
            rec = run_record(result, paths)
            records.append(rec)
            run_paths.append((material, Path(paths["json"])))

    agg_go = aggregate_material(records, "GO")
    agg_ac = aggregate_material(records, "AC")
    cmp_rows = comparison_go_ac(agg_go, agg_ac)

    stats_payload = {
        "provenance": provenance_block(),
        "n_runs": len(records),
        "GO": agg_go,
        "AC": agg_ac,
        "comparison_note": "Descriptivo; no validación experimental.",
    }

    prov_path = out / "provenance.json"
    prov_path.write_text(json.dumps(provenance_block(), indent=2), encoding="utf-8")
    stats_path = out / "statistics.json"
    stats_path.write_text(json.dumps(stats_payload, indent=2, default=str), encoding="utf-8")

    write_csv(out / "per_run_records.csv", records)
    write_csv(
        out / "aggregate_results.csv",
        [flatten_aggregate_csv(agg_go), flatten_aggregate_csv(agg_ac)],
    )
    write_csv(out / "comparison_go_ac.csv", cmp_rows)

    _write_readme(out)

    result: dict[str, Any] = {
        "provenance": provenance_block(),
        "n_runs": len(records),
        "mass_conservation_all_ok": all(r["mass_conservation_ok"] for r in records),
        "outputs": {
            "per_run_records_csv": str(out / "per_run_records.csv"),
            "aggregate_results_csv": str(out / "aggregate_results.csv"),
            "statistics_json": str(stats_path),
            "comparison_go_ac_csv": str(out / "comparison_go_ac.csv"),
            "provenance_json": str(prov_path),
            "readme": str(out / "README.md"),
        },
    }

    if plot:
        from go_mb.final_campaign_viz import plot_final_campaign

        fig_meta = plot_final_campaign(records, run_paths, out / "figures")
        result["outputs"]["figures"] = fig_meta
        _append_figure_section_to_readme(out, fig_meta)

    return result


def _write_readme(out: Path) -> None:
    readme = out / "README.md"
    readme.write_text(
        _readme_body(figure_section="(ver sección final_campaign_figures tras generar figuras)"),
        encoding="utf-8",
    )


def _append_figure_section_to_readme(out: Path, figures: list[dict[str, str]]) -> None:
    body = _readme_body(figure_section=_figures_markdown(figures))
    (out / "README.md").write_text(body, encoding="utf-8")


def _figures_markdown(figures: list[dict[str, str]]) -> str:
    lines = ["## final_campaign_figures", ""]
    for f in figures:
        lines.append(f"- **{f['filename']}** — {f['description']}")
    return "\n".join(lines)


def _readme_body(*, figure_section: str) -> str:
    return f"""# Campaña final computacional GO vs AC

**Clasificación:** `{FINAL_CAMPAIGN_CLASSIFICATION}`  
**not_experimental_validation:** true  
**computational_final_campaign:** true

## Protocolo

| Parámetro | Valor |
|-----------|-------|
| Geometría | Wiam (MB 1×1, GO 7×7, AC 2×2) |
| MB / GO / AC | 200 / 100 / 100 unidades |
| σ | {SIGMA_PX} px/paso |
| Pasos | {N_STEPS} |
| P_ads | {P_ADS} (regla computacional de adsorción; **no** probabilidad experimental de sticking) |
| Seeds GO | 1–40 (40 corridas) |
| Seeds AC | 1–40 (40 corridas) |
| Total | 80 simulaciones |

## Condiciones experimentales (provenance)

- T = 25 °C, pH = 6  
- MB inicial = 4 mg, adsorbente = 10 mg, V = 40 mL  
- **C₀ = 100 mg/L** (confirmado Wiam)

## Langmuir (solo referencia de equilibrio)

- **GO:** qmax=764.7, KL=0.206, qe=380.7 mg/g, Ce=4.81 mg/L  
- **AC:** qmax=412.2, KL=0.088, qe=290.9 mg/g, Ce=27.3 mg/L  

No se fuerza la simulación a alcanzar qe.

## PSO (referencia cinética por material)

- **GO:** qe_PSO=384.6 mg/g, k2=0.0002 g/(mg·min)  
- **AC:** qe_PSO=100.4 mg/g, k2=0.00910 g/(mg·min)  

No usar PSO GO para AC ni viceversa. **Los pasos de simulación no son minutos.**

## S* = 0.55 (contexto bibliográfico)

Referencia de sticking probability en un sistema AC–MB relacionado (Sha'Ato, 2021).  
**No sustituye P_ads=1.0** en esta campaña.

## α (escala temporal)

Exploratorio (`exploratory temporal scale`). No modifica el motor.

## Métricas por corrida

material, seed, σ, steps, P_ads, T, pH, masas, C₀, Nads, % adsorbido, qt, contactos, eventos adsorción, eficiencia contacto→adsorción, conservación de masa, provenance.

## Estadística

Por material: mean, median, std, min, max, CV, percentiles 25/75; IC 95% cuando aplica (`stats.py`).

## Limitaciones

- Modelo 2D discreto; no validación experimental.  
- Comparación GO/AC descriptiva, sin causalidad demostrada.  
- P_ads=1 es decisión computacional provisional, no dato físico.

{figure_section}
"""


def load_campaign_series(run_paths: list[tuple[str, Path]]) -> dict[str, list[tuple[int, list[dict]]]]:
    """material -> [(seed, series), ...]"""
    out: dict[str, list[tuple[int, list[dict]]]] = {"GO": [], "AC": []}
    for material, jpath in run_paths:
        data = load_run(jpath)
        seed = int(data["run"]["seed"])
        series = data.get("series") or []
        out[material].append((seed, series))
    return out
