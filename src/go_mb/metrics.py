"""Variables de salida de una corrida. No mezclar Nads adsorbido con N adsorbente."""

from __future__ import annotations

from typing import Any

import numpy as np

from go_mb.config import SimulationConfig
from go_mb.models import pso_time_for_fraction
from go_mb.state import SimulationState


def snapshot(state: SimulationState, prev_qt: float | None) -> dict[str, float | int]:
    cfg = state.config
    m_ads = state.m_adsorbed_mg
    m_free = state.m_free_mg
    qt = state.qt_mg_g
    dq = 0.0 if prev_qt is None else qt - prev_qt
    return {
        "step": state.step,
        "n_adsorbed": state.n_adsorbed,
        "n_free": state.n_free,
        "percent_adsorbed": (state.n_adsorbed / cfg.n_mb) * 100.0,
        "m_adsorbed_mg": m_ads,
        "m_free_mg": m_free,
        "c_pdf_mg_l": m_ads / cfg.volume_l,
        "c_remaining_mg_l": m_free / cfg.volume_l,
        "qt_mg_g": qt,
        "percent_qmax": (qt / cfg.qmax_mg_g) * 100.0,
        "n_contacts": state.n_contacts,
        "n_adsorption_events": state.n_adsorption_events,
        "dqt_per_step": dq,
    }


def steps_to_percentages(qt_series: list[float], q_ref: float) -> dict[str, int | None]:
    """Primer paso en el que qt alcanza f·q_ref, f = 10…100 %. None si no se alcanza."""
    out: dict[str, int | None] = {}
    arr = np.asarray(qt_series, dtype=np.float64)
    for pct in range(10, 101, 10):
        target = q_ref * (pct / 100.0)
        hit = np.flatnonzero(arr >= target - 1e-12)
        out[str(pct)] = int(hit[0]) if hit.size else None
    return out


def alpha_estimates(
    steps_qe_pso: dict[str, int | None],
    k2: float,
    qe_pso: float,
) -> dict[str, float | None]:
    alphas: dict[str, float | None] = {}
    for pct, n_sim in steps_qe_pso.items():
        frac = int(pct) / 100.0
        t_pso = pso_time_for_fraction(k2, qe_pso, frac)
        if n_sim is None or t_pso is None or n_sim <= 0:
            alphas[pct] = None
        else:
            alphas[pct] = t_pso / n_sim
    return alphas


def summarize_run(
    config: SimulationConfig,
    series: list[dict[str, float | int]],
    langmuir: dict[str, float],
) -> dict[str, Any]:
    if not series:
        raise ValueError("serie vacía")
    last = series[-1]
    qt = [float(row["qt_mg_g"]) for row in series]
    steps = [int(row["step"]) for row in series]
    qfinal = float(last["qt_mg_g"])
    n_steps = steps[-1] if steps[-1] > 0 else 1
    return {
        "n_adsorbed": int(last["n_adsorbed"]),
        "n_free": int(last["n_free"]),
        "percent_adsorbed": float(last["percent_adsorbed"]),
        "m_adsorbed_mg": float(last["m_adsorbed_mg"]),
        "m_free_mg": float(last["m_free_mg"]),
        "c_pdf_mg_l": float(last["c_pdf_mg_l"]),
        "c_remaining_mg_l": float(last["c_remaining_mg_l"]),
        "qfinal_mg_g": qfinal,
        "percent_qmax": float(last["percent_qmax"]),
        "n_contacts": int(last["n_contacts"]),
        "n_adsorption_events": int(last.get("n_adsorption_events", last["n_adsorbed"])),
        "contact_to_adsorption_ratio": (
            float(last["n_adsorbed"]) / int(last["n_contacts"])
            if int(last["n_contacts"]) > 0
            else None
        ),
        "mean_speed_q_per_step": qfinal / n_steps,
        "steps_to_percent_qe_L": steps_to_percentages(qt, langmuir["qe_mg_g"]),
        "steps_to_percent_qfinal": steps_to_percentages(qt, qfinal if qfinal > 0 else 1.0),
        "note_percentages": (
            "PENDIENTE en el PDF: 10…100 % respecto a qe_L, qe_PSO, qfinal o qmax. "
            "Se reportan qe_L y qfinal."
        ),
        "note_concentration": (
            "c_pdf_mg_l = m_adsorbed/V (fórmula del PDF). "
            "c_remaining_mg_l = m_free/V (concentración restante)."
        ),
        "mass_conservation_ok": abs(float(last["m_adsorbed_mg"]) + float(last["m_free_mg"]) - config.m_mb_mg) < 1e-9,
        "result_classification": "computational_execution_not_experimental_validation",
    }
