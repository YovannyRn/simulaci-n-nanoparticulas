"""Tests de magnitudes documentadas y derivadas (Fase 1 / config)."""

from go_mb.config import SimulationConfig, default_config
from go_mb.models import langmuir_equilibrium, pso_qt


def test_experimental_masses_and_counts() -> None:
    cfg = default_config()
    assert cfg.n_mb == 200
    assert cfg.n_go == 100
    assert cfg.peso_mb_mg == 0.02
    assert cfg.peso_go_mg == 0.1
    assert abs(cfg.n_mb * cfg.peso_mb_mg - 4.0) < 1e-12
    assert abs(cfg.n_go * cfg.peso_go_mg - 10.0) < 1e-12


def test_concentrations() -> None:
    cfg = default_config()
    assert cfg.c_go_mg_l == 250.0
    assert cfg.c0_mg_l == 100.0


def test_pixel_geometry() -> None:
    cfg = default_config()
    assert cfg.domain_px == 442
    assert cfg.n_pixels == 195364
    assert abs(cfg.pixel_area_um2 - 5990.76) < 1e-9
    assert abs(cfg.vessel_area_cm2 - 11.6964) < 1e-9
    assert cfg.mb_size_px == 1
    assert cfg.go_size_px == 7
    assert cfg.mb_area_px2 == 200
    assert cfg.go_area_px2 == 4900


def test_capacity_per_go() -> None:
    cfg = default_config()
    assert abs(cfg.cap_go_mg - 0.07647) < 1e-12
    assert abs(cfg.qmax_mg_g * cfg.m_go_g - 7.647) < 1e-9


def test_langmuir_reference_matches_pdf() -> None:
    eq = langmuir_equilibrium(SimulationConfig())
    assert abs(eq["ce_mg_l"] - 4.81) < 0.01
    assert abs(eq["qe_mg_g"] - 380.7) < 0.05
    assert abs(eq["m_adsorbed_eq_mg"] + eq["m_free_eq_mg"] - 4.0) < 1e-9
    assert abs(eq["qe_mg_g"] - eq["qe_langmuir_check_mg_g"]) < 1e-9


def test_pso_example_10_min() -> None:
    cfg = SimulationConfig()
    qt = pso_qt(cfg.k2_example_g_mg_min, cfg.qe_pso_mg_g, 10.0)
    mass = qt * cfg.m_go_g
    assert abs(mass - 1.672) < 0.001
    assert abs(mass / cfg.peso_mb_mg - 83.6) < 0.05


def test_pending_parameters_are_labeled() -> None:
    names = {p.symbol: p.status.value for p in SimulationConfig().parameter_table()}
    assert names["D"] == "PENDIENTE"
    assert names["P"] == "PENDIENTE"
    assert names["P_ads"] == "PENDIENTE"
    assert names["Nrep"] == "PENDIENTE"
    assert names["k2_tabla"] == "PENDIENTE"
