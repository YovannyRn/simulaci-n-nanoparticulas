"""Bucle científico: mover → contactar → adsorber → registrar.

Langmuir y PSO no participan en la decisión de adsorción.
"""

from __future__ import annotations

from typing import Any

from go_mb.adsorption import apply_adsorption
from go_mb.config import MaterialKind, RunSettings, SimulationConfig
from go_mb.contact import contact_pairs
from go_mb.metrics import alpha_estimates, snapshot, steps_to_percentages, summarize_run
from go_mb.models import reference_bundle
from go_mb.motion import move
from go_mb.state import SimulationState, assert_inside, initialize_state


def advance_step(
    state: SimulationState,
    rng,
    settings: RunSettings,
    prev_qt: float | None,
) -> tuple[dict[str, float | int], int]:
    """Un paso: mover → contactar → adsorber. Única ruta usada por motor y visualización."""
    move(state, rng, settings.sigma_px)
    pairs = contact_pairs(state)
    n_pairs = int(len(pairs))
    state.n_contacts += n_pairs
    n_ads = apply_adsorption(state, pairs, rng, settings.p_ads)
    state.n_adsorption_events += n_ads
    state.step += 1
    snap = snapshot(state, prev_qt)
    return snap, n_pairs


def run_simulation(
    config: SimulationConfig | None = None,
    settings: RunSettings | None = None,
    *,
    seed: int | None = None,
    sigma_px: float | None = None,
    n_steps: int | None = None,
    p_ads: float | None = None,
) -> dict[str, Any]:
    cfg = config or SimulationConfig()
    if settings is None:
        if seed is None or sigma_px is None or n_steps is None:
            raise ValueError("Hace falta seed, sigma_px y n_steps (D y P son PENDIENTE; deben inyectarse)")
        settings = RunSettings(seed=seed, sigma_px=sigma_px, n_steps=n_steps, p_ads=p_ads)
    state, rng = initialize_state(cfg, settings)
    refs = reference_bundle(cfg)
    series: list[dict[str, float | int]] = []
    prev_qt: float | None = 0.0
    series.append(snapshot(state, None))

    for step in range(1, settings.n_steps + 1):
        snap, _ = advance_step(state, rng, settings, prev_qt)
        if step % settings.record_every == 0 or step == settings.n_steps:
            series.append(snap)
            prev_qt = float(snap["qt_mg_g"])

    assert_inside(state)
    summary = summarize_run(cfg, series, refs["langmuir"])
    qt = [float(row["qt_mg_g"]) for row in series]
    if cfg.material == MaterialKind.GO:
        steps_pso = steps_to_percentages(qt, cfg.qe_pso_mg_g)
        summary["steps_to_percent_qe_PSO"] = steps_pso
        summary["alpha_min_per_step_vs_qe_PSO"] = alpha_estimates(
            steps_pso, cfg.k2_example_g_mg_min, cfg.qe_pso_mg_g
        )
    else:
        summary["steps_to_percent_qe_PSO"] = None
        summary["alpha_min_per_step_vs_qe_PSO"] = None
        summary["note_pso_alpha"] = "No calculado para AC–MB en esta fase."
    final_state = {
        "mb_xy": state.mb_xy.tolist(),
        "mb_free": state.mb_free.tolist(),
        "adsorbent_xy": state.go_xy.tolist(),
        "adsorbent_capacity_mg": state.go_capacity_mg.tolist(),
        "adsorbent_symbol": cfg.adsorbent_symbol,
        # Alias histórico GO–MB (misma memoria que adsorbent_*)
        "go_xy": state.go_xy.tolist(),
        "go_capacity_mg": state.go_capacity_mg.tolist(),
    }
    return {
        "config": cfg.to_metadata(),
        "run": settings.metadata(),
        "reference": refs,
        "summary": summary,
        "series": series,
        "final_state": final_state,
    }


def peek_state(config: SimulationConfig, settings: RunSettings) -> SimulationState:
    state, _ = initialize_state(config, settings)
    return state
