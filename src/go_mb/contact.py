"""Detección geométrica de contacto. Sin probabilidad de colisión y sin RNG."""

from __future__ import annotations

import numpy as np

from go_mb.state import SimulationState


def contact_pairs(state: SimulationState) -> np.ndarray:
    """Pares (i_mb, j_go) con d ≤ rMB + rA. Solo MB libres.

    Retorna un array (K, 2) de enteros. Función pura de las posiciones.
    """
    free_idx = np.flatnonzero(state.mb_free)
    if free_idx.size == 0 or state.go_xy.shape[0] == 0:
        return np.empty((0, 2), dtype=np.int64)
    mb = state.mb_xy[free_idx]
    go = state.go_xy
    dx = mb[:, None, 0] - go[None, :, 0]
    dy = mb[:, None, 1] - go[None, :, 1]
    dist = np.hypot(dx, dy)
    thresh = state.config.r_mb_px + state.config.r_go_px
    ii, jj = np.nonzero(dist <= thresh + 1e-12)
    if ii.size == 0:
        return np.empty((0, 2), dtype=np.int64)
    return np.column_stack((free_idx[ii], jj)).astype(np.int64)
