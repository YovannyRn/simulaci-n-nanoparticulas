"""Regla de adsorción posterior al contacto.

No consulta Langmuir ni PSO.
No inventa un P_ads de literatura: por defecto adsorbe un objeto entero
si queda capacidad másica suficiente.
"""

from __future__ import annotations

import numpy as np

from go_mb.state import SimulationState


def apply_adsorption(
    state: SimulationState,
    pairs: np.ndarray,
    rng: np.random.Generator | None = None,
    p_ads: float | None = None,
) -> int:
    """Aplica adsorción a pares de contacto (i_mb, j_go).

    Un MB que contacta varios GO se asigna al más cercano con capacidad.
    Un objeto MB entero (peso_MB) se adsorbe solo si cap_restante ≥ peso_MB.
    Si p_ads no es None, tras pasar el filtro de capacidad se lanza Bernoulli.
    """
    if pairs.size == 0:
        return 0
    peso = state.config.peso_mb_mg
    n_adsorbed_now = 0

    # Agrupar por MB para resolver múltiples GO.
    order = np.argsort(pairs[:, 0], kind="stable")
    pairs = pairs[order]
    mb_ids = pairs[:, 0]
    go_ids = pairs[:, 1]
    splits = np.flatnonzero(np.diff(mb_ids)) + 1
    groups = np.split(np.arange(len(mb_ids)), splits)

    for g in groups:
        i_mb = int(mb_ids[g[0]])
        if not state.mb_free[i_mb]:
            continue
        candidate_go = go_ids[g]
        capable = [
            int(j)
            for j in candidate_go
            if state.go_capacity_mg[int(j)] + 1e-15 >= peso
        ]
        if not capable:
            continue
        mb_xy = state.mb_xy[i_mb]
        d2 = np.sum((state.go_xy[capable] - mb_xy) ** 2, axis=1)
        # Empate: índice de GO menor.
        best_local = int(np.argmin(d2))
        ties = np.flatnonzero(np.isclose(d2, d2[best_local]))
        j_go = min(capable[int(t)] for t in ties)

        if p_ads is not None:
            if rng is None:
                raise ValueError("p_ads estocástico requiere un RNG")
            if not (0.0 <= p_ads <= 1.0):
                raise ValueError("p_ads debe estar en [0, 1]")
            if rng.random() > p_ads:
                continue

        state.mb_free[i_mb] = False
        state.go_capacity_mg[j_go] -= peso
        n_adsorbed_now += 1
    return n_adsorbed_now
