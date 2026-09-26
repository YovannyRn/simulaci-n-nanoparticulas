"""Calibración temporal exploratoria (PSO referencia GO, sin motor)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from go_mb.adsorption import apply_adsorption
from go_mb.models import pso_qt, pso_time_for_fraction
from go_mb.temporal_calibration import (
    DEFAULT_FRACTIONS,
    PSO_K2_G_MG_MIN,
    PSO_QE_MG_G,
    TEMPORAL_CALIBRATION_CLASSIFICATION,
    first_step_reaching_qt,
    fraction_crossings_for_run,
    load_and_analyze_campaign,
    provenance_header,
    run_temporal_calibration,
)


def test_pso_formula_and_inverse() -> None:
    qe = PSO_QE_MG_G
    k2 = PSO_K2_G_MG_MIN
    t = 10.0
    qt = pso_qt(k2, qe, t)
    assert abs(qt - 167.21) < 0.1
    f = 0.5
    t_back = pso_time_for_fraction(k2, qe, f)
    assert t_back is not None
    assert abs(pso_qt(k2, qe, t_back) - qe * f) < 0.05


def test_pso_time_coherence_roundtrip() -> None:
    for f in (0.1, 0.5, 0.9):
        t = pso_time_for_fraction(PSO_K2_G_MG_MIN, PSO_QE_MG_G, f)
        assert t is not None
        qt = pso_qt(PSO_K2_G_MG_MIN, PSO_QE_MG_G, t)
        assert abs(qt / PSO_QE_MG_G - f) < 0.01


def test_not_reached_without_extrapolation() -> None:
    series = [
        {"step": 0, "qt_mg_g": 0.0},
        {"step": 1, "qt_mg_g": 10.0},
        {"step": 2, "qt_mg_g": 20.0},
    ]
    assert first_step_reaching_qt(series, PSO_QE_MG_G * 0.9, max_step=2) is None


def test_first_step_crossing() -> None:
    target = PSO_QE_MG_G * 0.1
    series = [
        {"step": 0, "qt_mg_g": 0.0},
        {"step": 5, "qt_mg_g": target - 1.0},
        {"step": 6, "qt_mg_g": target},
    ]
    assert first_step_reaching_qt(series, target, max_step=10) == 6


def test_alpha_computed_for_go_only() -> None:
    fake = {
        "run": {"seed": 1, "sigma_px": 1.0, "n_steps": 100},
        "summary": {
            "n_adsorbed": 50,
            "percent_adsorbed": 25,
            "qfinal_mg_g": 200,
            "n_contacts": 10,
            "mass_conservation_ok": True,
        },
        "config": {"material": "GO"},
        "series": [
            {"step": i, "qt_mg_g": i * 5.0} for i in range(0, 101)
        ],
    }
    rows = fraction_crossings_for_run(fake, fractions=[0.1])
    assert rows[0]["reach_status"] == "reached"
    assert rows[0]["t_pso_min"] is not None
    assert rows[0]["alpha_min_per_step"] is not None

    fake_ac = {
        **fake,
        "config": {"material": "AC"},
        "series": [{"step": i, "qt_mg_g": i * 2.0} for i in range(0, 101)],
    }
    rows_ac = fraction_crossings_for_run(fake_ac, fractions=[0.1])
    assert rows_ac[0]["pso_reference_status"] == "ac_pso_reference"
    assert rows_ac[0]["t_pso_min"] is not None
    assert rows_ac[0]["alpha_min_per_step"] is not None


def test_provenance_fields() -> None:
    p = provenance_header(campaign_root=Path("data/x"))
    assert p["classification"] == TEMPORAL_CALIBRATION_CLASSIFICATION
    assert p["steps_are_not_minutes"] is True
    assert p["alpha_status"] == "exploratory_not_definitive"
    assert "pso_reference_ac" in p
    assert p["pso_reference_ac"]["qe_mg_g"] == pytest.approx(100.4)


def test_analyze_wiam_campaign_smoke() -> None:
    root = Path("data/sensitivity/homogeneous_temporal_wiam_geometry")
    if not (root / "go").is_dir():
        pytest.skip("Campaña Wiam no presente en disco")
    analysis = load_and_analyze_campaign(root)
    assert analysis["n_runs"] == 140
    assert len(analysis["fraction_crossings"]) == 140 * len(DEFAULT_FRACTIONS)
    assert analysis["provenance"]["motor_unchanged"] is True


def test_run_temporal_calibration_outputs(tmp_path: Path) -> None:
    root = Path("data/sensitivity/homogeneous_temporal_wiam_geometry")
    if not (root / "go").is_dir():
        pytest.skip("Campaña Wiam no presente")
    result = run_temporal_calibration(
        campaign_root=root,
        output_dir=tmp_path / "out",
        plot=False,
    )
    assert result["n_runs"] == 140
    assert Path(result["outputs"]["json"]).exists()
    assert Path(result["outputs"]["fraction_crossings_csv"]).exists()


def test_apply_adsorption_unchanged() -> None:
    sig = inspect.signature(apply_adsorption)
    assert list(sig.parameters.keys()) == ["state", "pairs", "rng", "p_ads"]


def test_motor_no_matplotlib_in_calibration_module() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "go_mb"
    for name in ("engine.py", "temporal_calibration.py", "adsorption.py"):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] != "matplotlib", name
