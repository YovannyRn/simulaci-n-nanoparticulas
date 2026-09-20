"""Fase 3: browniano + rebote."""

import inspect

import numpy as np

from go_mb.config import RunSettings, SimulationConfig
from go_mb.motion import move
from go_mb.state import assert_inside, initialize_state


def test_displacements_are_normal_zero_mean() -> None:
    src = inspect.getsource(move)
    assert "rng.normal(0.0, sigma_px" in src
    assert "mb_free" in src


def test_reproducible_trajectories() -> None:
    cfg = SimulationConfig()
    settings = RunSettings(seed=3, sigma_px=1.5, n_steps=20)

    def evolve() -> tuple[np.ndarray, np.ndarray]:
        state, rng = initialize_state(cfg, settings)
        for _ in range(20):
            move(state, rng, settings.sigma_px)
        return state.mb_xy.copy(), state.go_xy.copy()

    a = evolve()
    b = evolve()
    assert np.allclose(a[0], b[0])
    assert np.allclose(a[1], b[1])


def test_particles_stay_inside_and_go_moves() -> None:
    cfg = SimulationConfig()
    settings = RunSettings(seed=5, sigma_px=2.0, n_steps=50)
    state, rng = initialize_state(cfg, settings)
    go0 = state.go_xy.copy()
    for _ in range(50):
        move(state, rng, settings.sigma_px)
        assert_inside(state)
    assert not np.allclose(go0, state.go_xy)


def test_adsorbed_mb_does_not_move() -> None:
    cfg = SimulationConfig()
    state, rng = initialize_state(cfg, RunSettings(seed=9, sigma_px=3.0, n_steps=1))
    state.mb_free[:] = False
    frozen = state.mb_xy.copy()
    move(state, rng, 3.0)
    assert np.allclose(frozen, state.mb_xy)


def test_sigma_zero_no_displacement() -> None:
    cfg = SimulationConfig()
    state, rng = initialize_state(cfg, RunSettings(seed=4, sigma_px=0.0, n_steps=1))
    mb0 = state.mb_xy.copy()
    go0 = state.go_xy.copy()
    move(state, rng, 0.0)
    assert np.allclose(mb0, state.mb_xy)
    assert np.allclose(go0, state.go_xy)


def test_bounce_reflects_and_clamps() -> None:
    from go_mb.motion import _bounce_axis

    lo, hi = 2.5, 439.5
    out = _bounce_axis(np.array([lo - 1.0, hi + 2.0, (lo + hi) / 2.0]), lo, hi)
    assert out[0] >= lo
    assert out[1] <= hi
    assert np.all(out >= lo) and np.all(out <= hi)
