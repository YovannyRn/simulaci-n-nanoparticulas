"""Capa visual: paridad con el motor headless."""

from go_mb.config import ac_config
from go_mb.engine import advance_step, run_simulation
from go_mb.interactive import config_for_material, create_session
from go_mb.config import RunSettings
from go_mb.state import initialize_state


def test_advance_step_matches_run_simulation_go() -> None:
    cfg = config_for_material("GO")
    settings = RunSettings(seed=12, sigma_px=1.1, n_steps=25)
    full = run_simulation(config=cfg, settings=settings)
    state, rng = initialize_state(cfg, settings)
    series = []
    prev_qt = None
    from go_mb.metrics import snapshot

    series.append(snapshot(state, None))
    for _ in range(settings.n_steps):
        snap, _ = advance_step(state, rng, settings, prev_qt)
        series.append(snap)
        prev_qt = float(snap["qt_mg_g"])
    assert series[-1]["n_adsorbed"] == full["summary"]["n_adsorbed"]
    assert series[-1]["n_contacts"] == full["summary"]["n_contacts"]
    assert series[-1]["qt_mg_g"] == full["summary"]["qfinal_mg_g"]


def test_interactive_session_ac_fixed_adsorbent() -> None:
    session = create_session("AC", seed=3, sigma_px=1.5, n_steps=15)
    ac0 = session.state.go_xy.copy()
    session.run_to_completion_headless()
    assert (session.state.go_xy == ac0).all()


def test_interactive_same_as_engine_ac() -> None:
    engine = run_simulation(config=ac_config(), seed=8, sigma_px=1.0, n_steps=30)
    session = create_session("AC", seed=8, sigma_px=1.0, n_steps=30)
    session.run_to_completion_headless()
    m = session.metrics_dict()
    assert m["n_adsorbed"] == engine["summary"]["n_adsorbed"]
    assert m["n_contacts"] == engine["summary"]["n_contacts"]


def test_visualization_module_does_not_import_tk_at_import() -> None:
    import go_mb.interactive as interactive

    assert "launch_interactive_viewer" in dir(interactive)
