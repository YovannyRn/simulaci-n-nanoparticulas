"""Campaña temporal homogénea GO vs AC."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from go_mb.config import SimulationConfig, ac_config
from go_mb.homogeneous_temporal import (
    DEFAULT_SEEDS,
    DEFAULT_SIGMAS,
    DEFAULT_STEPS,
    HOMOGENEOUS_CLASSIFICATION,
    aggregate_configuration_stats,
    expected_run_count,
    run_homogeneous_campaign,
    run_material_campaign,
)


def test_design_constants() -> None:
    assert DEFAULT_SIGMAS == [1.0, 1.5]
    assert DEFAULT_STEPS == [200, 400, 600, 800, 1000, 1500, 2000]
    assert DEFAULT_SEEDS == [1, 2, 3, 4, 5]
    assert expected_run_count() == 70


def test_go_and_ac_same_grid_small(tmp_path: Path) -> None:
    sigmas = [1.0]
    steps = [5, 10]
    seeds = [1, 2]
    go = run_material_campaign(
        "GO",
        sigmas=sigmas,
        steps_list=steps,
        seeds=seeds,
        output_dir=tmp_path / "go",
        geometry_era="legacy_geometry",
    )
    ac = run_material_campaign(
        "AC",
        sigmas=sigmas,
        steps_list=steps,
        seeds=seeds,
        output_dir=tmp_path / "ac",
        geometry_era="legacy_geometry",
    )
    assert go["n_runs"] == 4
    assert ac["n_runs"] == 4
    for study in (go["study"], ac["study"]):
        assert study["provenance"]["homogeneous_temporal"] is True
        assert (
            study["provenance"]["homogeneous_temporal_classification"]
            == HOMOGENEOUS_CLASSIFICATION
        )
        assert study["provenance"]["not_experimental_validation"] is True
        for rec in study["runs"]:
            assert rec["outcomes"]["mass_conservation_ok"]
            assert rec["execution_parameters"]["sigma_px"]["value"] in sigmas
            assert rec["execution_parameters"]["n_steps"]["value"] in steps
            assert rec["execution_parameters"]["seed"] in seeds
            assert "m_adsorbed_mg" in rec["outcomes"]
            assert "m_free_mg" in rec["outcomes"]
            assert rec["paths"]["json"]
            assert rec["paths"]["csv"]


def test_aggregate_stats_spread(tmp_path: Path) -> None:
    go = run_material_campaign(
        "GO",
        sigmas=[1.5],
        steps_list=[8],
        seeds=[1, 2, 3],
        output_dir=tmp_path / "go",
        geometry_era="legacy_geometry",
    )
    agg = aggregate_configuration_stats(go["study"])
    assert len(agg) == 1
    assert agg[0]["n_seeds"] == 3
    assert agg[0]["n_adsorbed"]["spread"] >= 0


def test_full_campaign_structure(tmp_path: Path) -> None:
    result = run_homogeneous_campaign(
        base_dir=tmp_path / "camp",
        sigmas=[1.0],
        steps_list=[6],
        seeds=[1],
        plot=True,
        run_go=True,
        run_ac=True,
        geometry_era="legacy_geometry",
    )
    assert result["total_runs"] == 2
    assert Path(result["comparison"]["json"]).exists()
    assert Path(result["comparison"]["csv"]).exists()
    assert result["comparison"]["figures"]


def test_motor_does_not_import_matplotlib() -> None:
    engine_path = Path(__file__).resolve().parents[1] / "src" / "go_mb" / "engine.py"
    sens_path = Path(__file__).resolve().parents[1] / "src" / "go_mb" / "sensitivity.py"
    for path in (engine_path, sens_path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] != "matplotlib", f"matplotlib en {path.name}"
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("matplotlib"), f"matplotlib en {path.name}"


def test_go_mobile_ac_fixed_configs() -> None:
    assert SimulationConfig().adsorbent_movable is True
    assert ac_config().adsorbent_movable is False
    assert ac_config().material.value == "AC"
