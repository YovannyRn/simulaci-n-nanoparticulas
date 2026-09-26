"""Barridos de calibración y sensibilidad (σ, pasos, matriz σ×pasos).

No optimiza hacia qe Langmuir. No es validación experimental.
Los valores de σ y pasos se inyectan; nunca son defaults científicos del motor.
"""

from __future__ import annotations

from typing import Any, Literal

from go_mb.config import MaterialKind, OriginStatus, RunSettings, SimulationConfig
from go_mb.engine import run_simulation
from go_mb.io import save_run

StudyKind = Literal["sigma_sweep", "steps_sweep", "sigma_steps_grid"]

STUDY_CLASSIFICATION = "computational_sensitivity_not_experimental_validation"
NO_LANGMUIR_OPTIMIZATION = True
STEPS_ARE_NOT_MINUTES = True


def parse_float_list(text: str) -> list[float]:
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        raise ValueError("La lista de valores no puede estar vacía")
    return [float(p) for p in parts]


def parse_int_list(text: str) -> list[int]:
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        raise ValueError("La lista de valores no puede estar vacía")
    return [int(float(p)) for p in parts]


def parse_seed_list(text: str | None, default_seed: int) -> list[int]:
    if text is None or not text.strip():
        return [default_seed]
    return parse_int_list(text)


def _provenance_header() -> dict[str, Any]:
    return {
        "study_classification": STUDY_CLASSIFICATION,
        "not_experimental_validation": True,
        "no_langmuir_optimization": NO_LANGMUIR_OPTIMIZATION,
        "steps_are_not_minutes": STEPS_ARE_NOT_MINUTES,
        "pending_parameters": {
            "D_sigma": OriginStatus.PENDIENTE.value,
            "P_steps": OriginStatus.PENDIENTE.value,
            "P_ads_physical": OriginStatus.PENDIENTE.value,
            "k2_unified": OriginStatus.PENDIENTE.value,
            "Nrep": OriginStatus.PENDIENTE.value,
            "CA": OriginStatus.PENDIENTE.value,
            "alpha_min_per_step": OriginStatus.PENDIENTE.value,
        },
        "computational_decisions": {
            "p_ads_default": "DECISIÓN COMPUTACIONAL PROVISIONAL (equivalente P_ads=1 tras contacto+capacidad)",
            "contact_radii_px": (
                "círculos inscritos: r_MB=lado_MB/2, r_ads=lado_ads/2 "
                "(Wiam: MB 1, GO 7, AC 2 px)"
            ),
            "bounce": "reflexión por eje + recorte",
        },
        "bibliographic_reference_only": (
            "Langmuir y PSO aparecen en reference/ de cada corrida como referencia macroscópica; "
            "no se usan como objetivo de barrido ni condición de parada."
        ),
        "k2_note": (
            "k2 ejemplo 0.0002 y k2 tabla 0.001 siguen PENDIENTES de unificación. "
            "Curvas PSO en reference usan k2_example con etiqueta explícita."
        ),
    }


def _stem_prefix(config: SimulationConfig) -> str:
    return "ac_" if config.material == MaterialKind.AC else ""


def run_record(result: dict[str, Any], paths: dict[str, str] | None = None) -> dict[str, Any]:
    """Fila reproducible con roles de procedencia."""
    cfg = result["config"]
    run = result["run"]
    summary = result["summary"]
    n_mb = int(cfg["n_mb"])
    n_go = int(cfg["n_go"])
    material = cfg.get("material", MaterialKind.GO.value)
    ads_symbol = cfg.get("adsorbent_symbol", "GO" if material == "GO" else "AC")
    return {
        "role": "simulation_outcome",
        "material": material,
        "paths": paths or {},
        "execution_parameters": {
            "role": "injected_execution_parameter",
            "seed": run["seed"],
            "sigma_px": {
                "value": run["sigma_px"],
                "status": run.get("sigma_status", OriginStatus.PENDIENTE.value),
            },
            "n_steps": {
                "value": run["n_steps"],
                "status": run.get("n_steps_status", OriginStatus.PENDIENTE.value),
            },
            "p_ads": {
                "value": run.get("p_ads"),
                "effective": run.get("p_ads_effective"),
                "implementation_status": run.get("p_ads_implementation_status"),
                "status": run.get("p_ads_status", OriginStatus.PENDIENTE.value),
            },
        },
        "system_counts": {
            "N_MB": n_mb,
            "N_GO": n_go,
            "N_adsorbent": n_go,
            "adsorbent_symbol": ads_symbol,
            "status": OriginStatus.DECISION_COMPUTACIONAL.value,
        },
        "outcomes": {
            "n_adsorbed": int(summary["n_adsorbed"]),
            "percent_adsorbed": float(summary["percent_adsorbed"]),
            "m_adsorbed_mg": float(summary["m_adsorbed_mg"]),
            "m_free_mg": float(summary["m_free_mg"]),
            "qfinal_mg_g": float(summary["qfinal_mg_g"]),
            "n_contacts": int(summary["n_contacts"]),
            "mass_conservation_ok": bool(summary["mass_conservation_ok"]),
            "result_classification": summary.get(
                "result_classification",
                "computational_execution_not_experimental_validation",
            ),
        },
        "series_csv": (paths or {}).get("csv"),
    }


def _run_one(
    config: SimulationConfig,
    seed: int,
    sigma_px: float,
    n_steps: int,
    p_ads: float | None,
    output_dir: str | None,
    stem: str,
) -> tuple[dict[str, Any], dict[str, str] | None, dict[str, Any]]:
    settings = RunSettings(seed=seed, sigma_px=sigma_px, n_steps=n_steps, p_ads=p_ads)
    result = run_simulation(config, settings)
    paths: dict[str, str] | None = None
    if output_dir is not None:
        prefix = _stem_prefix(config)
        paths = save_run(result, output_dir, f"{prefix}{stem}" if prefix else stem)
    record = run_record(result, paths)
    record["full_result_keys"] = ["config", "run", "reference", "summary", "series", "final_state"]
    return result, paths, record


def _finalize_study(
    kind: StudyKind,
    records: list[dict[str, Any]],
    fixed: dict[str, Any],
    swept: dict[str, Any],
    *,
    material: str = "GO",
) -> dict[str, Any]:
    analysis = analyze_study_records(records)
    prov = _provenance_header()
    prov["material"] = material
    prov["stage_label"] = "Caracterización AC + visualización inicial" if material == "AC" else prov.get(
        "stage_label", "computational_sensitivity"
    )
    return {
        "provenance": prov,
        "study": {
            "kind": kind,
            "classification": STUDY_CLASSIFICATION,
            "material": material,
            "fixed_parameters": fixed,
            "swept_parameters": swept,
            "n_runs": len(records),
        },
        "runs": records,
        "analysis": analysis,
    }


def analyze_study_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Resumen descriptivo sin conclusión científica."""
    if not records:
        return {"rows": [], "by_configuration": [], "seed_variability": []}

    rows: list[dict[str, Any]] = []
    for rec in records:
        ep = rec["execution_parameters"]
        out = rec["outcomes"]
        rows.append(
            {
                "seed": ep["seed"],
                "sigma_px": ep["sigma_px"]["value"],
                "n_steps": ep["n_steps"]["value"],
                "n_adsorbed": out["n_adsorbed"],
                "percent_adsorbed": out["percent_adsorbed"],
                "qfinal_mg_g": out["qfinal_mg_g"],
                "n_contacts": out["n_contacts"],
                "mass_conservation_ok": out["mass_conservation_ok"],
            }
        )

    # Agrupar por (sigma, steps) para variabilidad entre seeds.
    groups: dict[tuple[float, int], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["sigma_px"], row["n_steps"])
        groups.setdefault(key, []).append(row)

    by_configuration: list[dict[str, Any]] = []
    seed_variability: list[dict[str, Any]] = []
    for (sigma, steps), items in sorted(groups.items()):
        n_ads = [it["n_adsorbed"] for it in items]
        pct = [it["percent_adsorbed"] for it in items]
        qt = [it["qfinal_mg_g"] for it in items]
        contacts = [it["n_contacts"] for it in items]
        entry = {
            "sigma_px": sigma,
            "n_steps": steps,
            "n_seeds": len(items),
            "n_adsorbed_mean": sum(n_ads) / len(n_ads),
            "n_adsorbed_min": min(n_ads),
            "n_adsorbed_max": max(n_ads),
            "percent_adsorbed_mean": sum(pct) / len(pct),
            "qfinal_mg_g_mean": sum(qt) / len(qt),
            "n_contacts_mean": sum(contacts) / len(contacts),
            "all_mass_conserved": all(it["mass_conservation_ok"] for it in items),
        }
        by_configuration.append(entry)
        if len(items) > 1:
            seed_variability.append(
                {
                    "sigma_px": sigma,
                    "n_steps": steps,
                    "seeds": [it["seed"] for it in items],
                    "n_adsorbed_values": n_ads,
                    "n_adsorbed_spread": max(n_ads) - min(n_ads),
                }
            )

    return {
        "purpose": (
            "Caracterizar sensibilidad del modelo computacional. "
            "No es validación experimental ni selección automática de σ o P."
        ),
        "rows": rows,
        "by_configuration": by_configuration,
        "seed_variability": seed_variability,
    }


def sweep_sigma(
    *,
    sigmas: list[float],
    seeds: list[int],
    n_steps: int,
    config: SimulationConfig | None = None,
    p_ads: float | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    cfg = config or SimulationConfig()
    records: list[dict[str, Any]] = []
    for seed in seeds:
        for sigma in sigmas:
            stem = f"sens_sigma_{sigma:g}_steps_{n_steps}_seed_{seed}"
            _, _, record = _run_one(cfg, seed, sigma, n_steps, p_ads, output_dir, stem)
            records.append(record)
    return _finalize_study(
        "sigma_sweep",
        records,
        fixed={"n_steps": n_steps, "p_ads": p_ads, "seeds": seeds},
        swept={"sigma_px": sigmas},
        material=cfg.material.value,
    )


def sweep_steps(
    *,
    steps_list: list[int],
    seeds: list[int],
    sigma_px: float,
    config: SimulationConfig | None = None,
    p_ads: float | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    cfg = config or SimulationConfig()
    records: list[dict[str, Any]] = []
    for seed in seeds:
        for steps in steps_list:
            stem = f"sens_steps_{steps}_sigma_{sigma_px:g}_seed_{seed}"
            _, _, record = _run_one(cfg, seed, sigma_px, steps, p_ads, output_dir, stem)
            records.append(record)
    return _finalize_study(
        "steps_sweep",
        records,
        fixed={"sigma_px": sigma_px, "p_ads": p_ads, "seeds": seeds},
        swept={"n_steps": steps_list},
        material=cfg.material.value,
    )


def sweep_sigma_steps_grid(
    *,
    sigmas: list[float],
    steps_list: list[int],
    seeds: list[int],
    config: SimulationConfig | None = None,
    p_ads: float | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    cfg = config or SimulationConfig()
    records: list[dict[str, Any]] = []
    for seed in seeds:
        for sigma in sigmas:
            for steps in steps_list:
                stem = f"sens_grid_sigma_{sigma:g}_steps_{steps}_seed_{seed}"
                _, _, record = _run_one(cfg, seed, sigma, steps, p_ads, output_dir, stem)
                records.append(record)
    return _finalize_study(
        "sigma_steps_grid",
        records,
        fixed={"p_ads": p_ads, "seeds": seeds},
        swept={"sigma_px": sigmas, "n_steps": steps_list},
        material=cfg.material.value,
    )
