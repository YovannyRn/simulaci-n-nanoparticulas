"""Fase 4: contacto geométrico sin RNG."""

import inspect

import numpy as np

from go_mb.config import SimulationConfig
from go_mb import contact as contact_mod
from go_mb.contact import contact_pairs
from go_mb.state import SimulationState


def _state_two_particles(dist: float) -> SimulationState:
    cfg = SimulationConfig(n_mb=1, n_go=1)
    mb = np.array([[20.0, 20.0]])
    go = np.array([[20.0 + dist, 20.0]])
    return SimulationState(
        config=cfg,
        seed=0,
        mb_xy=mb,
        go_xy=go,
        mb_free=np.array([True]),
        go_capacity_mg=np.array([cfg.cap_go_mg]),
    )


def test_threshold_inclusive() -> None:
    cfg = SimulationConfig()
    thresh = cfg.r_mb_px + cfg.r_go_px
    assert len(contact_pairs(_state_two_particles(thresh))) == 1
    assert len(contact_pairs(_state_two_particles(thresh + 1e-6))) == 0
    assert len(contact_pairs(_state_two_particles(thresh - 0.01))) == 1


def test_detector_has_no_rng() -> None:
    src = inspect.getsource(contact_mod)
    assert "default_rng" not in src
    assert "random(" not in src
    assert "langmuir" not in src.lower()
    assert "qe" not in src
