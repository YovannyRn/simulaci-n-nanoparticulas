"""Referencia temporal GO/AC, PSO, P_ads=0.55."""

from __future__ import annotations

from pathlib import Path

import pytest

from go_mb.models import pso_qt, pso_time_for_fraction
from go_mb.p_ads_055 import (
    PADS_055_CLASSIFICATION,
    load_historical_p_ads,
    merge_comparison_records,
    provenance_block,
    run_p_ads_055_campaign,
)
from go_mb.pso_reference import (
    AC_PSO,
    FINAL_TEMPORAL_CLASSIFICATION,
    GO_PSO,
    pso_fraction_table,
)
from go_mb.temporal_calibration import fraction_crossings_for_run


def test_pso_go_ac_separate_parameters() -> None:
    assert GO_PSO.qe_pso_mg_g == 384.6
    assert AC_PSO.qe_pso_mg_g == 100.4
    assert AC_PSO.k2_g_mg_min == 0.00910
    t_go = pso_time_for_fraction(GO_PSO.k2_g_mg_min, GO_PSO.qe_pso_mg_g, 0.5)
    t_ac = pso_time_for_fraction(AC_PSO.k2_g_mg_min, AC_PSO.qe_pso_mg_g, 0.5)
    assert t_go is not None and t_ac is not None
    assert t_go != t_ac


def test_pso_ac_inverse_fraction() -> None:
    f = 0.3
    t = pso_time_for_fraction(AC_PSO.k2_g_mg_min, AC_PSO.qe_pso_mg_g, f)
    assert t is not None
    qt = pso_qt(AC_PSO.k2_g_mg_min, AC_PSO.qe_pso_mg_g, t)
    assert abs(qt / AC_PSO.qe_pso_mg_g - f) < 0.02


def test_fraction_crossings_ac_gets_alpha() -> None:
    fake = {
        "run": {"seed": 1, "sigma_px": 1.0, "n_steps": 500},
        "summary": {
            "n_adsorbed": 50,
            "percent_adsorbed": 25,
            "qfinal_mg_g": 50.0,
            "n_contacts": 10,
            "mass_conservation_ok": True,
        },
        "config": {"material": "AC"},
        "series": [{"step": i, "qt_mg_g": i * 0.5} for i in range(0, 501)],
    }
    rows = fraction_crossings_for_run(fake, fractions=[0.1])
    assert rows[0]["pso_reference_status"] == "ac_pso_reference"
    assert rows[0]["qe_pso_mg_g"] == AC_PSO.qe_pso_mg_g
    if rows[0]["reach_status"] == "reached":
        assert rows[0]["alpha_min_per_step"] is not None


def test_not_reached_ac() -> None:
    fake = {
        "run": {"seed": 1, "sigma_px": 1.0, "n_steps": 5},
        "summary": {"qfinal_mg_g": 1.0, "mass_conservation_ok": True},
        "config": {"material": "AC"},
        "series": [{"step": i, "qt_mg_g": 0.1} for i in range(6)],
    }
    rows = fraction_crossings_for_run(fake, fractions=[0.9])
    assert rows[0]["reach_status"] == "not_reached"
    assert rows[0]["n_sim"] is None


def test_pso_fraction_table_has_t_pso() -> None:
    rows = pso_fraction_table("AC", [0.1, 0.5])
    assert all(r["t_pso_min"] is not None for r in rows)


def test_pads_055_provenance() -> None:
    p = provenance_block()
    assert p["classification"] == PADS_055_CLASSIFICATION
    assert p["not_equal_to_bibliographic_s_star"] is True


def test_pads_055_small_campaign(tmp_path: Path) -> None:
    from go_mb import p_ads_055 as mod

    old_s, old_sig, old_n = mod.SEEDS, mod.SIGMAS, mod.N_STEPS
    try:
        mod.SEEDS = [1]
        mod.SIGMAS = [1.0]
        mod.N_STEPS = 8
        recs = run_p_ads_055_campaign(output_dir=tmp_path, store_json=False)
        assert len(recs) == 2
        assert all(r["mass_conservation_ok"] for r in recs)
        assert recs[0]["p_ads_effective"] == 0.55
    finally:
        mod.SEEDS, mod.SIGMAS, mod.N_STEPS = old_s, old_sig, old_n


def test_merge_historical_with_055() -> None:
    root = Path("data/sensitivity/p_ads_sensitivity")
    if not (root / "per_run_records.csv").is_file():
        pytest.skip("Sin campaña P_ads previa")
    hist = load_historical_p_ads(root)
    assert any(abs(float(r["p_ads_effective"]) - 0.5) < 1e-9 for r in hist)
    merged = merge_comparison_records(hist, [])
    assert not any(abs(float(r["p_ads_effective"]) - 0.55) < 1e-9 for r in merged)


def test_run_final_temporal_reference_smoke(tmp_path: Path) -> None:
    from go_mb.final_temporal_reference import provenance_header, run_final_temporal_reference

    camp = Path("data/sensitivity/homogeneous_temporal_wiam_geometry")
    if not (camp / "go").is_dir():
        pytest.skip("Campaña Wiam ausente")
    p = provenance_header(campaign_root=camp)
    assert p["classification"] == FINAL_TEMPORAL_CLASSIFICATION
    result = run_final_temporal_reference(
        campaign_root=camp,
        output_dir=tmp_path / "out",
        plot=False,
        run_pads_055=True,
    )
    assert Path(result["outputs"]["summary_json"]).exists()
    assert Path(result["outputs"]["pso_ac_csv"]).exists()
