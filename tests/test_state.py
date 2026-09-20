"""Fase 2: dominio, 200 MB, 100 GO, estado inicial reproducible."""

from go_mb.config import RunSettings, SimulationConfig
from go_mb.state import assert_inside, initialize_state


def test_full_counts_and_occupation() -> None:
    cfg = SimulationConfig()
    state, _ = initialize_state(cfg, RunSettings(seed=7, sigma_px=1.0, n_steps=1))
    assert state.mb_xy.shape == (200, 2)
    assert state.go_xy.shape == (100, 2)
    assert state.n_free == 200
    assert state.n_adsorbed == 0
    assert cfg.mb_area_px2 == 5000
    assert cfg.go_area_px2 == 4900
    assert_inside(state)


def test_same_seed_same_initial_positions() -> None:
    cfg = SimulationConfig()
    s1, _ = initialize_state(cfg, RunSettings(seed=11, sigma_px=1.0, n_steps=1))
    s2, _ = initialize_state(cfg, RunSettings(seed=11, sigma_px=1.0, n_steps=1))
    assert (s1.mb_xy == s2.mb_xy).all()
    assert (s1.go_xy == s2.go_xy).all()


def test_seed_is_stored() -> None:
    state, _ = initialize_state(SimulationConfig(), RunSettings(seed=42, sigma_px=1.0, n_steps=1))
    assert state.seed == 42


def test_initial_capacity_is_massic() -> None:
    cfg = SimulationConfig()
    state, _ = initialize_state(cfg, RunSettings(seed=1, sigma_px=1.0, n_steps=1))
    assert abs(float(state.go_capacity_mg[0]) - cfg.cap_go_mg) < 1e-12
