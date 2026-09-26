"""Configuración y motor AC–MB (carbón activo fijo)."""

from pathlib import Path

import numpy as np

from go_mb.config import MaterialKind, RunSettings, SimulationConfig, ac_config
from go_mb.engine import run_simulation
from go_mb.io import save_run
from go_mb.models import langmuir_equilibrium, reference_bundle
from go_mb.motion import move
from go_mb.state import initialize_state


def test_ac_config_magnitudes_wiam() -> None:
    cfg = ac_config()
    assert cfg.material == MaterialKind.AC
    assert cfg.adsorbent_movable is False
    assert cfg.n_mb == 200
    assert cfg.n_go == 100
    assert cfg.peso_mb_mg == 0.02
    assert abs(cfg.peso_go_mg - 0.1) < 1e-12
    assert cfg.c0_mg_l == 100.0
    assert abs(cfg.qmax_mg_g - 412.2) < 1e-9
    assert abs(cfg.kl_l_mg - 0.088) < 1e-9
    assert abs(cfg.cap_go_mg - 0.04122) < 1e-9
    assert abs(cfg.qmax_mg_g * cfg.m_go_g - 4.122) < 1e-9


def test_ac_langmuir_reference_not_forced() -> None:
    cfg = ac_config()
    eq = langmuir_equilibrium(cfg)
    assert abs(eq["ce_mg_l"] - 27.26) < 0.05
    assert abs(eq["qe_mg_g"] - 290.9) < 0.05
    assert abs(eq["m_adsorbed_eq_mg"] - 2.909) < 0.02
    refs = reference_bundle(cfg)
    assert refs["material"] == "AC"
    assert refs["wiam_documented"]["qe_mg_g"] == 290.9
    assert abs(refs["langmuir_vs_wiam"]["delta_qe_mg_g"]) < 0.1


def test_ac_adsorbent_fixed_under_brownian() -> None:
    cfg = ac_config()
    state, rng = initialize_state(cfg, RunSettings(seed=11, sigma_px=2.0, n_steps=1))
    ac0 = state.go_xy.copy()
    for _ in range(40):
        move(state, rng, 2.0)
    assert np.allclose(ac0, state.go_xy)


def test_go_adsorbent_still_movable() -> None:
    cfg = SimulationConfig()
    assert cfg.adsorbent_movable is True
    state, rng = initialize_state(cfg, RunSettings(seed=5, sigma_px=2.0, n_steps=1))
    go0 = state.go_xy.copy()
    move(state, rng, 2.0)
    assert not np.allclose(go0, state.go_xy)


def test_ac_engine_metrics_and_mass_conservation() -> None:
    cfg = ac_config()
    result = run_simulation(config=cfg, seed=7, sigma_px=1.5, n_steps=80)
    s = result["summary"]
    assert result["config"]["material"] == "AC"
    assert s["mass_conservation_ok"]
    assert 0 <= s["n_adsorbed"] <= cfg.n_mb
    assert s["percent_adsorbed"] == (s["n_adsorbed"] / cfg.n_mb) * 100.0
    assert abs(s["qfinal_mg_g"] - s["m_adsorbed_mg"] / cfg.m_go_g) < 1e-12
    assert s["n_contacts"] >= 0
    assert result["summary"]["steps_to_percent_qe_PSO"] is None
    assert result["final_state"]["adsorbent_symbol"] == "AC"
    qe_l = result["reference"]["langmuir"]["qe_mg_g"]
    assert s["qfinal_mg_g"] != qe_l or s["n_steps"] == 0  # no calibración a qe


def test_ac_contact_without_adsorption_possible() -> None:
    """Contacto geométrico acumulado; adsorción depende de capacidad y regla provisional."""
    zero = run_simulation(config=ac_config(), seed=1, sigma_px=0.0, n_steps=5)
    assert zero["summary"]["n_contacts"] == 0
    assert zero["summary"]["n_adsorbed"] == 0


def test_ac_persistence_provenance(tmp_path: Path) -> None:
    result = run_simulation(config=ac_config(), seed=3, sigma_px=1.0, n_steps=25)
    paths = save_run(result, tmp_path, "ac_seed_3")
    assert "ac_seed_3.json" in paths["json"]
    assert result["run"]["not_experimental_validation"] is True
