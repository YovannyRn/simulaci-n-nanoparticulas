"""Fase 5: adsorción post-contacto por capacidad másica."""

import inspect

import numpy as np

from go_mb.adsorption import apply_adsorption
from go_mb.config import SimulationConfig
from go_mb.state import SimulationState


def _state(n_mb: int = 4, n_go: int = 1) -> SimulationState:
    # 4 objetos × 0.02 mg y 1 GO de 0.1 mg → cap = 0.07647 mg (3 objetos enteros).
    cfg = SimulationConfig(n_mb=n_mb, n_go=n_go, m_mb_mg=n_mb * 0.02, m_go_g=n_go * 0.0001)
    mb = np.zeros((n_mb, 2))
    go = np.array([[10.0, 10.0]])
    return SimulationState(
        config=cfg,
        seed=0,
        mb_xy=mb,
        go_xy=go,
        mb_free=np.ones(n_mb, dtype=bool),
        go_capacity_mg=np.full(n_go, cfg.cap_go_mg),
    )


def test_no_contact_no_adsorption() -> None:
    state = _state()
    apply_adsorption(state, np.empty((0, 2), dtype=np.int64))
    assert state.n_adsorbed == 0
    assert abs(state.m_adsorbed_mg + state.m_free_mg - state.config.m_mb_mg) < 1e-12


def test_capacity_blocks_fourth_whole_object() -> None:
    """0.07647 mg admite 3 objetos de 0.02 mg, no 4."""
    state = _state(n_mb=4, n_go=1)
    pairs = np.array([[0, 0], [1, 0], [2, 0], [3, 0]], dtype=np.int64)
    apply_adsorption(state, pairs)
    assert state.n_adsorbed == 3
    assert state.n_free == 1
    assert state.go_capacity_mg[0] < state.config.peso_mb_mg
    assert abs(state.m_adsorbed_mg + state.m_free_mg - state.config.m_mb_mg) < 1e-12


def test_mb_not_adsorbed_twice() -> None:
    state = _state(n_mb=1, n_go=1)
    pairs = np.array([[0, 0], [0, 0]], dtype=np.int64)
    apply_adsorption(state, pairs)
    assert state.n_adsorbed == 1


def test_adsorption_module_does_not_use_langmuir() -> None:
    src = inspect.getsource(apply_adsorption).lower()
    assert "qmax" not in src
    assert "kl_l" not in src
    assert "langmuir_equilibrium" not in src
    assert "qe_mg" not in src
