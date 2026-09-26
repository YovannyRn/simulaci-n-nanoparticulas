"""Análisis protocolo final P=2000 (solo datos existentes)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from go_mb.adsorption import apply_adsorption
from go_mb.final_protocol_analysis import (
    FINAL_PROTOCOL_CLASSIFICATION,
    P2000,
    aggregate_material_sigma,
    alpha_analysis_p2000_go,
    compare_sigma_descriptive,
    fraction_reachability_p2000,
    load_p2000_runs,
    provenance_block,
    run_final_protocol_analysis,
)
def test_p2000_run_count() -> None:
    root = Path("data/sensitivity/homogeneous_temporal_wiam_geometry")
    if not (root / "go").is_dir():
        pytest.skip("Campaña Wiam ausente")
    runs = load_p2000_runs(root)
    assert len(runs) == 20
    for r in runs:
        assert r["n_steps"] == P2000
        assert r["seed"] in (1, 2, 3, 4, 5)
        assert r["sigma_px"] in (1.0, 1.5)


def test_aggregate_stats_cv() -> None:
    root = Path("data/sensitivity/homogeneous_temporal_wiam_geometry")
    if not (root / "go").is_dir():
        pytest.skip("Campaña Wiam ausente")
    agg = aggregate_material_sigma(load_p2000_runs(root))
    assert len(agg) == 4
    go10 = next(a for a in agg if a["material"] == "GO" and a["sigma_px"] == 1.0)
    assert go10["n_adsorbed"]["mean"] is not None
    assert go10["n_adsorbed"]["cv_percent"] is not None


def test_sigma_comparison_descriptive() -> None:
    root = Path("data/sensitivity/homogeneous_temporal_wiam_geometry")
    if not (root / "go").is_dir():
        pytest.skip("Campaña Wiam ausente")
    agg = aggregate_material_sigma(load_p2000_runs(root))
    cmp = compare_sigma_descriptive(agg)
    assert len(cmp) == 2
    assert "relative_delta_percent" in cmp[0]


def test_fraction_reachability() -> None:
    cal = Path("data/analysis/temporal_calibration")
    if not (cal / "fraction_crossings.csv").is_file():
        pytest.skip("Calibración temporal ausente")
    import csv

    with (cal / "fraction_crossings.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    reach = fraction_reachability_p2000(rows)
    assert len(reach) == 20
    assert all(r["n_reached"] + r["n_not_reached"] == 9 for r in reach)


def test_alpha_p2000_go_structure() -> None:
    cal = Path("data/analysis/temporal_calibration")
    if not (cal / "fraction_crossings.csv").is_file():
        pytest.skip("Calibración temporal ausente")
    import csv

    with (cal / "fraction_crossings.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    alpha = alpha_analysis_p2000_go(rows)
    assert alpha["scope"] == "GO_only_pso_reference"
    assert len(alpha["by_sigma_seed"]) == 10


def test_run_final_protocol_reproducible(tmp_path: Path) -> None:
    camp = Path("data/sensitivity/homogeneous_temporal_wiam_geometry")
    cal = Path("data/analysis/temporal_calibration")
    if not camp.is_dir() or not (cal / "fraction_crossings.csv").is_file():
        pytest.skip("Datos fuente ausentes")
    a = run_final_protocol_analysis(
        campaign_root=camp,
        calibration_root=cal,
        output_dir=tmp_path / "a",
        plot=False,
    )
    b = run_final_protocol_analysis(
        campaign_root=camp,
        calibration_root=cal,
        output_dir=tmp_path / "b",
        plot=False,
    )
    assert a["n_p2000_runs"] == b["n_p2000_runs"] == 20


def test_provenance_classification() -> None:
    p = provenance_block(
        campaign_root=Path("x"),
        calibration_root=Path("y"),
    )
    assert p["classification"] == FINAL_PROTOCOL_CLASSIFICATION
    assert p["no_automatic_sigma_selection"] is True


def test_apply_adsorption_unchanged() -> None:
    assert list(inspect.signature(apply_adsorption).parameters) == [
        "state",
        "pairs",
        "rng",
        "p_ads",
    ]


def test_analysis_module_no_matplotlib() -> None:
    path = Path(__file__).resolve().parents[1] / "src" / "go_mb" / "final_protocol_analysis.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] != "matplotlib"
