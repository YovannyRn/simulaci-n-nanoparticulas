"""Sensibilidad computacional P_ads."""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pytest

from go_mb.adsorption import apply_adsorption
from go_mb.config import SimulationConfig
from go_mb.engine import run_simulation
from go_mb.p_ads_sensitivity import (
    P_ADS_SENSITIVITY_CLASSIFICATION,
    aggregate_by_cell,
    provenance_block,
    run_p_ads_sensitivity_campaign,
    run_record,
    validate_p_ads,
)
from go_mb.state import SimulationState


def test_validate_p_ads_rejects_invalid() -> None:
    validate_p_ads(0.5)
    with pytest.raises(ValueError):
        validate_p_ads(1.1)
    with pytest.raises(ValueError):
        validate_p_ads(-0.1)


def test_p_ads_zero_no_adsorption_events() -> None:
    cfg = SimulationConfig(n_mb=2, n_go=1)
    state = SimulationState(
        config=cfg,
        seed=0,
        mb_xy=np.array([[1.0, 1.0], [2.0, 2.0]]),
        go_xy=np.array([[1.0, 1.0]]),
        mb_free=np.array([True, True]),
        go_capacity_mg=np.array([cfg.cap_go_mg]),
    )
    pairs = np.array([[0, 0], [1, 0]], dtype=np.int64)
    n = apply_adsorption(state, pairs, rng=np.random.default_rng(0), p_ads=0.0)
    assert n == 0


def test_p_ads_one_matches_none_full_run() -> None:
    kw = dict(seed=11, sigma_px=1.0, n_steps=30)
    a = run_simulation(p_ads=None, **kw)
    b = run_simulation(p_ads=1.0, **kw)
    assert a["summary"]["n_adsorbed"] == b["summary"]["n_adsorbed"]
    assert a["summary"]["n_contacts"] == b["summary"]["n_contacts"]
    assert a["summary"]["n_adsorption_events"] == b["summary"]["n_adsorption_events"]


def test_mass_conservation_with_p_ads() -> None:
    r = run_simulation(seed=3, sigma_px=1.5, n_steps=40, p_ads=0.25)
    assert r["summary"]["mass_conservation_ok"]


def test_run_record_propagates_p_ads() -> None:
    r = run_simulation(seed=1, sigma_px=1.0, n_steps=5, p_ads=0.75)
    rec = run_record(r)
    assert rec["p_ads_effective"] == 0.75
    assert rec["n_adsorption_events"] <= rec["n_contacts"]


def test_provenance() -> None:
    p = provenance_block()
    assert p["classification"] == P_ADS_SENSITIVITY_CLASSIFICATION
    assert p["p_ads_are_computational_not_physical"] is True


def test_aggregate_cv() -> None:
    records = [
        {
            "material": "GO",
            "sigma_px": 1.0,
            "p_ads_effective": 1.0,
            "n_adsorbed": 100,
            "percent_adsorbed": 50.0,
            "qfinal_mg_g": 200.0,
            "n_contacts": 500,
            "n_adsorption_events": 100,
            "contact_to_adsorption_efficiency": 0.2,
            "mass_conservation_ok": True,
        },
        {
            "material": "GO",
            "sigma_px": 1.0,
            "p_ads_effective": 1.0,
            "n_adsorbed": 110,
            "percent_adsorbed": 55.0,
            "qfinal_mg_g": 220.0,
            "n_contacts": 520,
            "n_adsorption_events": 110,
            "contact_to_adsorption_efficiency": 0.21,
            "mass_conservation_ok": True,
        },
    ]
    agg = aggregate_by_cell(records)
    assert agg[0]["n_adsorbed"]["cv_percent"] is not None


def test_small_campaign(tmp_path: Path) -> None:
    from go_mb import p_ads_sensitivity as mod

    old_p = mod.PADS_VALUES
    old_s = mod.SEEDS
    old_sig = mod.SIGMAS
    old_n = mod.N_STEPS
    try:
        mod.PADS_VALUES = [1.0]
        mod.SEEDS = [1]
        mod.SIGMAS = [1.0]
        mod.N_STEPS = 10
        result = run_p_ads_sensitivity_campaign(output_dir=tmp_path / "p", plot=False)
        assert result["n_runs"] == 2
    finally:
        mod.PADS_VALUES = old_p
        mod.SEEDS = old_s
        mod.SIGMAS = old_sig
        mod.N_STEPS = old_n


def test_apply_adsorption_signature_unchanged() -> None:
    sig = inspect.signature(apply_adsorption)
    assert list(sig.parameters) == ["state", "pairs", "rng", "p_ads"]


def test_reproducibility_same_p_ads() -> None:
    kw = dict(seed=42, sigma_px=1.0, n_steps=25, p_ads=0.5)
    a = run_simulation(**kw)
    b = run_simulation(**kw)
    assert a["summary"]["n_adsorbed"] == b["summary"]["n_adsorbed"]
    assert a["summary"]["n_contacts"] == b["summary"]["n_contacts"]
    assert a["summary"]["n_adsorption_events"] == b["summary"]["n_adsorption_events"]
