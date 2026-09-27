"""Interfaz de presentación: validación y paridad con headless."""

from __future__ import annotations

import pytest

from go_mb.engine import run_simulation
from go_mb.interactive import create_session
from go_mb.launcher_validation import parse_execution_fields, validate_inputs
from go_mb.presentation import default_presentation
from go_mb.config import ac_config


def test_presentation_defaults_match_final_protocol() -> None:
    d = default_presentation()
    assert d.material == "GO"
    assert d.sigma_px == 1.5
    assert d.n_steps == 2000
    assert d.seed == 1
    assert d.p_ads == 1.0


def test_parse_rejects_text_and_nonpositive_steps() -> None:
    values, err = parse_execution_fields(
        sigma_text="abc",
        steps_text="200",
        seed_text="1",
        interval_text="35",
        p_ads_text="1",
    )
    assert values is None
    assert err is not None
    values, err = parse_execution_fields(
        sigma_text="1.5",
        steps_text="0",
        seed_text="1",
        interval_text="35",
        p_ads_text="1",
    )
    assert values is None
    assert err == "El número de pasos debe ser un entero positivo."
    values, err = parse_execution_fields(
        sigma_text="-1",
        steps_text="10",
        seed_text="1",
        interval_text="35",
        p_ads_text="1.5",
    )
    assert values is None
    values, err = parse_execution_fields(
        sigma_text="1,5",
        steps_text="200",
        seed_text="1",
        interval_text="35",
        p_ads_text="1",
    )
    assert err is None
    assert values is not None
    assert values["sigma_px"] == 1.5


def test_consecutive_sessions_do_not_share_state() -> None:
    go = create_session("GO", seed=1, sigma_px=1.5, n_steps=20, p_ads=1.0)
    go.run_to_completion_headless()
    ac = create_session("AC", seed=1, sigma_px=1.5, n_steps=20, p_ads=1.0)
    ac.run_to_completion_headless()
    assert go.config.qmax_mg_g == 764.7
    assert ac.config.qmax_mg_g == 412.2
    assert go.config.adsorbent_movable is True
    assert ac.config.adsorbent_movable is False
    assert go.config.go_size_px == 7
    assert ac.config.go_size_px == 2


def test_validate_inputs_rejects_bad_values() -> None:
    assert validate_inputs(sigma_px=0, n_steps=10, seed=1, interval_ms=30, p_ads=1.0)
    assert validate_inputs(sigma_px=1.0, n_steps=0, seed=1, interval_ms=30, p_ads=1.0)
    assert validate_inputs(sigma_px=1.0, n_steps=10, seed=-1, interval_ms=30, p_ads=1.0)
    assert validate_inputs(sigma_px=1.0, n_steps=10, seed=1, interval_ms=2, p_ads=1.0)
    assert validate_inputs(sigma_px=1.0, n_steps=10, seed=1, interval_ms=30, p_ads=1.5) is not None
    assert validate_inputs(sigma_px=1.5, n_steps=200, seed=1, interval_ms=30, p_ads=1.0) is None


def _assert_session_matches_engine(material: str, **kwargs: object) -> None:
    if material == "GO":
        engine = run_simulation(**kwargs)
    else:
        engine = run_simulation(config=ac_config(), **kwargs)
    session = create_session(material, **kwargs)  # type: ignore[arg-type]
    session.run_to_completion_headless()
    m = session.metrics_dict()
    s = engine["summary"]
    assert m["n_adsorbed"] == s["n_adsorbed"]
    assert m["n_contacts"] == s["n_contacts"]
    assert m["qt_mg_g"] == s["qfinal_mg_g"]
    assert m["percent_adsorbed"] == pytest.approx(s["percent_adsorbed"])
    assert m["m_adsorbed_mg"] == pytest.approx(s["m_adsorbed_mg"])
    assert m["m_free_mg"] == pytest.approx(s["m_free_mg"])
    assert s["mass_conservation_ok"]
    assert len(session.series) == len(engine["series"])


def test_gui_path_matches_headless_go_presentation_config() -> None:
    _assert_session_matches_engine(
        "GO",
        seed=1,
        sigma_px=1.5,
        n_steps=200,
        p_ads=1.0,
    )


def test_gui_path_matches_headless_ac_presentation_config() -> None:
    _assert_session_matches_engine(
        "AC",
        seed=1,
        sigma_px=1.5,
        n_steps=200,
        p_ads=1.0,
    )


def test_gui_path_other_seeds_and_sigma() -> None:
    _assert_session_matches_engine("GO", seed=17, sigma_px=1.0, n_steps=50, p_ads=1.0)
    _assert_session_matches_engine("AC", seed=5, sigma_px=2.0, n_steps=80, p_ads=None)


def test_pause_does_not_alter_trajectory() -> None:
    kwargs = dict(seed=3, sigma_px=1.2, n_steps=60, p_ads=1.0)
    straight = create_session("GO", **kwargs)
    straight.run_to_completion_headless()
    paused = create_session("GO", **kwargs)
    for _ in range(25):
        paused.step_once()
    paused.paused = True
    for _ in range(10):
        pass  # pausa: la UI no llama step_once
    paused.paused = False
    while paused.step_once():
        pass
    assert paused.metrics_dict()["n_adsorbed"] == straight.metrics_dict()["n_adsorbed"]
    assert paused.metrics_dict()["n_contacts"] == straight.metrics_dict()["n_contacts"]


def test_reset_reproduces_fresh_session() -> None:
    kwargs = dict(seed=9, sigma_px=1.5, n_steps=40, p_ads=1.0)
    a = create_session("GO", **kwargs)
    for _ in range(15):
        a.step_once()
    a.reset()
    while a.step_once():
        pass
    b = create_session("GO", **kwargs)
    b.run_to_completion_headless()
    assert a.metrics_dict()["n_adsorbed"] == b.metrics_dict()["n_adsorbed"]
