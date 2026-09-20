"""Fase 6–8: motor, campañas, persistencia y que la vista no altere números."""

from pathlib import Path

from go_mb.config import SimulationConfig
from go_mb.engine import run_simulation
from go_mb.experiments import run_campaign
from go_mb.io import load_run, save_run
from go_mb.viz import plot_run, plot_snapshot


def test_engine_reproducible_and_conserves_mass() -> None:
    cfg = SimulationConfig()
    kwargs = dict(config=cfg, seed=21, sigma_px=1.0, n_steps=30)
    a = run_simulation(**kwargs)
    b = run_simulation(**kwargs)
    assert a["summary"]["n_adsorbed"] == b["summary"]["n_adsorbed"]
    assert a["summary"]["n_contacts"] == b["summary"]["n_contacts"]
    assert a["series"][-1]["qt_mg_g"] == b["series"][-1]["qt_mg_g"]
    assert a["summary"]["mass_conservation_ok"]
    qe = a["reference"]["langmuir"]["qe_mg_g"]
    assert "qe_mg_g" in a["reference"]["langmuir"]
    assert a["run"]["adsorption_rule"] == "capacity_only_whole_objects"
    assert abs(qe - 380.7) < 0.05


def test_langmuir_not_used_as_stop() -> None:
    result = run_simulation(seed=2, sigma_px=0.0, n_steps=5)
    # sigma 0: poco movimiento; no se fuerza qe.
    qe = result["reference"]["langmuir"]["qe_mg_g"]
    assert abs(qe - 380.7) < 0.05
    assert result["summary"]["qfinal_mg_g"] <= 400.0


def test_campaign_distinct_seeds_and_replay(tmp_path: Path) -> None:
    camp = run_campaign(
        n_rep=3,
        base_seed=100,
        sigma_px=1.2,
        n_steps=15,
        output_dir=tmp_path,
    )
    assert camp["stats"]["seeds"] == [100, 101, 102]
    assert camp["stats"]["n_rep"] == 3
    replay = run_simulation(seed=100, sigma_px=1.2, n_steps=15)
    first = load_run(tmp_path / "go_seed_100.json")
    assert replay["summary"]["n_adsorbed"] == first["summary"]["n_adsorbed"]
    assert replay["summary"]["n_contacts"] == first["summary"]["n_contacts"]


def test_save_load_and_plot_do_not_change_metrics(tmp_path: Path) -> None:
    result = run_simulation(seed=8, sigma_px=1.0, n_steps=10)
    q = result["summary"]["qfinal_mg_g"]
    paths = save_run(result, tmp_path, "run8")
    loaded = load_run(paths["json"])
    assert loaded["summary"]["qfinal_mg_g"] == q
    fig1 = plot_run(loaded, tmp_path / "series.png")
    fig2 = plot_snapshot(loaded, tmp_path / "snap.png")
    assert Path(fig1).exists()
    assert Path(fig2).exists()
    again = load_run(paths["json"])
    assert again["summary"]["qfinal_mg_g"] == q


def test_run_requires_injected_pending_params() -> None:
    try:
        run_simulation(config=SimulationConfig())
    except ValueError as exc:
        assert "PENDIENTE" in str(exc)
    else:
        raise AssertionError("Debió exigir sigma y steps")
