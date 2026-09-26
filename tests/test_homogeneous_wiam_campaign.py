"""Campaña homogénea con geometría Wiam (140 corridas — diseño y preflight)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from go_mb.adsorption import apply_adsorption
from go_mb.config import (
    WIAM_AC_SIDE_PX,
    WIAM_GO_SIDE_PX,
    WIAM_MB_SIDE_PX,
    SimulationConfig,
    ac_config,
)
from go_mb.homogeneous_temporal import (
    DEFAULT_SEEDS,
    DEFAULT_SIGMAS,
    DEFAULT_STEPS,
    WIAM_HOMOGENEOUS_CLASSIFICATION,
    expected_run_count,
    run_homogeneous_campaign,
    run_material_campaign,
)


def test_wiam_design_counts() -> None:
    assert len(DEFAULT_SIGMAS) == 2
    assert len(DEFAULT_STEPS) == 7
    assert len(DEFAULT_SEEDS) == 5
    assert expected_run_count() == 70
    assert 2 * expected_run_count() == 140


def test_configs_use_wiam_geometry() -> None:
    go = SimulationConfig()
    ac = ac_config()
    assert go.mb_size_px == WIAM_MB_SIDE_PX == 1
    assert go.go_size_px == WIAM_GO_SIDE_PX == 7
    assert go.r_mb_px == 0.5
    assert go.r_go_px == 3.5
    assert ac.mb_size_px == 1
    assert ac.go_size_px == WIAM_AC_SIDE_PX == 2
    assert ac.r_mb_px == 0.5
    assert ac.r_go_px == 1.0
    assert go.adsorbent_movable is True
    assert ac.adsorbent_movable is False


def test_small_wiam_campaign_preflight(tmp_path: Path) -> None:
    go = run_material_campaign(
        "GO",
        sigmas=[1.0],
        steps_list=[200],
        seeds=[1, 2, 3, 4, 5],
        output_dir=tmp_path / "go",
        geometry_era="wiam_geometry",
    )
    assert go["n_runs"] == 5
    prov = go["study"]["provenance"]
    assert (
        prov["homogeneous_temporal_classification"]
        == WIAM_HOMOGENEOUS_CLASSIFICATION
    )
    assert prov["geometry"]["geometry_era"] == "wiam_geometry"
    assert prov["geometry"]["r_mb_px"] == 0.5
    for rec in go["study"]["runs"]:
        assert rec["geometry"]["mb_side_px"] == 1
        assert rec["geometry"]["adsorbent_side_px"] == 7
        assert rec["geometry"]["r_mb_px"] == 0.5
        assert rec["geometry"]["r_adsorbent_px"] == 3.5
        assert rec["outcomes"]["mass_conservation_ok"]
    assert Path(go["aggregated_stats_csv"]).exists()


def test_apply_adsorption_unchanged() -> None:
    sig = inspect.signature(apply_adsorption)
    assert list(sig.parameters.keys()) == ["state", "pairs", "rng", "p_ads"]


def test_scientific_motor_no_matplotlib() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "go_mb"
    for name in ("engine.py", "homogeneous_temporal.py", "sensitivity.py", "adsorption.py"):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] != "matplotlib", name
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("matplotlib"), name


def test_full_wiam_campaign_structure(tmp_path: Path) -> None:
    result = run_homogeneous_campaign(
        base_dir=tmp_path / "wiam_camp",
        sigmas=[1.0],
        steps_list=[10],
        seeds=[1],
        plot=False,
        geometry_era="wiam_geometry",
    )
    assert result["total_runs"] == 2
    assert result["geometry_era"] == "wiam_geometry"
    assert Path(result["comparison"]["json"]).exists()
    assert Path(result["materials"]["GO"]["aggregated_stats_csv"]).exists()
