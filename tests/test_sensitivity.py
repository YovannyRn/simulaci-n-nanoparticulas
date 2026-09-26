"""Calibración y sensibilidad: barridos, persistencia y reproducibilidad."""

from __future__ import annotations

from pathlib import Path

import pytest

from go_mb.engine import run_simulation
from go_mb.io import load_run, load_study, save_study
from go_mb.sensitivity import (
    analyze_study_records,
    run_record,
    sweep_sigma,
    sweep_sigma_steps_grid,
    sweep_steps,
)


def test_sigma_sweep_persists_runs_and_study(tmp_path: Path) -> None:
    study = sweep_sigma(
        sigmas=[0.0, 1.0],
        seeds=[7],
        n_steps=8,
        output_dir=tmp_path,
    )
    assert study["study"]["kind"] == "sigma_sweep"
    assert study["study"]["n_runs"] == 2
    assert study["provenance"]["no_langmuir_optimization"] is True
    for rec in study["runs"]:
        assert rec["execution_parameters"]["sigma_px"]["status"] == "PENDIENTE"
        assert rec["outcomes"]["mass_conservation_ok"]
        assert Path(rec["paths"]["json"]).exists()
        assert Path(rec["paths"]["csv"]).exists()
        loaded = load_run(rec["paths"]["json"])
        assert loaded["series"]
        assert rec["system_counts"]["N_MB"] == 200
        assert rec["system_counts"]["N_GO"] == 100


def test_steps_sweep_same_seed_and_sigma(tmp_path: Path) -> None:
    study = sweep_steps(
        steps_list=[5, 10],
        seeds=[3],
        sigma_px=1.2,
        output_dir=tmp_path,
    )
    assert study["study"]["n_runs"] == 2
    sigmas = {r["execution_parameters"]["sigma_px"]["value"] for r in study["runs"]}
    seeds = {r["execution_parameters"]["seed"] for r in study["runs"]}
    assert sigmas == {1.2}
    assert seeds == {3}
    steps = sorted(r["execution_parameters"]["n_steps"]["value"] for r in study["runs"])
    assert steps == [5, 10]


def test_sigma_steps_grid(tmp_path: Path) -> None:
    study = sweep_sigma_steps_grid(
        sigmas=[0.5, 1.0],
        steps_list=[4, 6],
        seeds=[1],
        output_dir=tmp_path,
    )
    assert study["study"]["n_runs"] == 4
    assert len(study["analysis"]["by_configuration"]) == 4


def test_study_save_load_roundtrip(tmp_path: Path) -> None:
    study = sweep_sigma(sigmas=[0.5], seeds=[2], n_steps=3, output_dir=tmp_path)
    path = save_study(study, tmp_path, "roundtrip")
    loaded = load_study(path)
    assert loaded["study"]["kind"] == study["study"]["kind"]
    assert loaded["runs"][0]["outcomes"]["n_adsorbed"] == study["runs"][0]["outcomes"]["n_adsorbed"]


def test_run_record_provenance_roles() -> None:
    result = run_simulation(seed=5, sigma_px=0.8, n_steps=6)
    rec = run_record(result)
    assert rec["execution_parameters"]["role"] == "injected_execution_parameter"
    assert rec["role"] == "simulation_outcome"
    assert rec["execution_parameters"]["p_ads"]["implementation_status"] == (
        "DECISIÓN COMPUTACIONAL PROVISIONAL"
    )


def test_reproducibility_same_parameters() -> None:
    kwargs = dict(seed=11, sigma_px=1.1, n_steps=9)
    a = run_simulation(**kwargs)
    b = run_simulation(**kwargs)
    assert a["summary"]["n_adsorbed"] == b["summary"]["n_adsorbed"]
    assert a["summary"]["n_contacts"] == b["summary"]["n_contacts"]


def test_different_seeds_can_differ() -> None:
    common = dict(sigma_px=1.5, n_steps=80)
    nads = [run_simulation(seed=s, **common)["summary"]["n_adsorbed"] for s in range(1, 6)]
    assert len(set(nads)) > 1


def test_mass_conservation_all_study_runs(tmp_path: Path) -> None:
    study = sweep_sigma_steps_grid(
        sigmas=[0.0, 1.5],
        steps_list=[5, 12],
        seeds=[4, 5],
        output_dir=tmp_path,
    )
    for rec in study["runs"]:
        assert rec["outcomes"]["mass_conservation_ok"]
        for row in load_run(rec["paths"]["json"])["series"]:
            assert abs(float(row["m_adsorbed_mg"]) + float(row["m_free_mg"]) - 4.0) < 1e-9


def test_analyze_seed_variability() -> None:
    rec_a = run_record(run_simulation(seed=1, sigma_px=1.0, n_steps=10))
    rec_b = run_record(run_simulation(seed=2, sigma_px=1.0, n_steps=10))
    analysis = analyze_study_records([rec_a, rec_b])
    assert len(analysis["seed_variability"]) == 1
    assert analysis["seed_variability"][0]["n_adsorbed_spread"] >= 0


def test_empty_sigma_list_raises() -> None:
    from go_mb.sensitivity import parse_float_list

    with pytest.raises(ValueError):
        parse_float_list("")
