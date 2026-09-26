"""Sensibilidad AC–MB: mismo protocolo que GO."""

from __future__ import annotations

from pathlib import Path

from go_mb.config import ac_config
from go_mb.engine import run_simulation
from go_mb.io import load_run, save_study
from go_mb.sensitivity import sweep_sigma, sweep_steps


def test_ac_sigma_sweep_reproducible(tmp_path: Path) -> None:
    cfg = ac_config()
    study = sweep_sigma(
        sigmas=[0.5, 1.0],
        seeds=[4],
        n_steps=12,
        config=cfg,
        output_dir=tmp_path,
    )
    assert study["study"]["material"] == "AC"
    assert study["provenance"]["material"] == "AC"
    assert study["study"]["n_runs"] == 2
    for rec in study["runs"]:
        assert rec["material"] == "AC"
        assert rec["system_counts"]["adsorbent_symbol"] == "AC"
        assert rec["outcomes"]["mass_conservation_ok"]
        assert Path(rec["paths"]["json"]).name.startswith("ac_")

    a = run_simulation(config=cfg, seed=4, sigma_px=1.0, n_steps=12)
    b = run_simulation(config=cfg, seed=4, sigma_px=1.0, n_steps=12)
    assert a["summary"]["n_adsorbed"] == b["summary"]["n_adsorbed"]


def test_ac_steps_sweep_mass_and_provenance(tmp_path: Path) -> None:
    study = sweep_steps(
        steps_list=[10, 20],
        seeds=[1, 2],
        sigma_px=1.5,
        config=ac_config(),
        output_dir=tmp_path,
    )
    assert study["study"]["n_runs"] == 4
    assert len(study["analysis"]["seed_variability"]) >= 1
    path = save_study(study, tmp_path, "ac_roundtrip")
    loaded = __import__("go_mb.io", fromlist=["load_study"]).load_study(path)
    assert loaded["study"]["material"] == "AC"
    rec = study["runs"][0]
    loaded_run = load_run(rec["paths"]["json"])
    assert loaded_run["config"]["material"] == "AC"
    assert loaded_run["summary"]["mass_conservation_ok"]
