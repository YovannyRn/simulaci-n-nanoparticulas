"""Movimiento browniano simplificado y rebote en paredes.

Δx, Δy ~ Normal(0, σ²) con σ inyectado (PENDIENTE en el PDF).
El algoritmo de rebote es una decisión computacional documentada.
"""

from __future__ import annotations

import numpy as np

from go_mb.state import SimulationState


def _bounce_axis(coord: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Reflexión del solapamiento y recorte. No es una ley física extraída del PDF."""
    span = hi - lo
    if span <= 0:
        return np.full_like(coord, lo)
    x = coord.astype(np.float64, copy=True)
    # Varias reflexiones si el paso es mayor que el recinto.
    for _ in range(8):
        below = x < lo
        above = x > hi
        if not np.any(below) and not np.any(above):
            break
        x[below] = lo + (lo - x[below])
        x[above] = hi - (x[above] - hi)
    return np.clip(x, lo, hi)


def move(state: SimulationState, rng: np.random.Generator, sigma_px: float) -> None:
    if sigma_px < 0:
        raise ValueError("sigma_px debe ser ≥ 0")
    domain = float(state.config.domain_px)

    free = state.mb_free
    n_free = int(np.count_nonzero(free))
    if n_free:
        delta = rng.normal(0.0, sigma_px, size=(n_free, 2))
        state.mb_xy[free] += delta
        half = state.config.r_mb_px
        state.mb_xy[free, 0] = _bounce_axis(state.mb_xy[free, 0], half, domain - half)
        state.mb_xy[free, 1] = _bounce_axis(state.mb_xy[free, 1], half, domain - half)

    if state.config.adsorbent_movable:
        go_delta = rng.normal(0.0, sigma_px, size=state.go_xy.shape)
        state.go_xy += go_delta
        half_go = state.config.r_go_px
        state.go_xy[:, 0] = _bounce_axis(state.go_xy[:, 0], half_go, domain - half_go)
        state.go_xy[:, 1] = _bounce_axis(state.go_xy[:, 1], half_go, domain - half_go)
