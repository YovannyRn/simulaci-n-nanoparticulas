"""Campaña final GO/AC."""

from __future__ import annotations

from pathlib import Path

from go_mb.final_campaign import (
    FINAL_CAMPAIGN_CLASSIFICATION,
    aggregate_material,
    comparison_go_ac,
    extended_stats,
    provenance_block,
    run_final_campaign,
    run_record,
)
from go_mb.engine import run_simulation


def test_provenance_final_campaign() -> None:
    p = provenance_block()
    assert p["classification"] == FINAL_CAMPAIGN_CLASSIFICATION
    assert p["not_experimental_validation"] is True
    assert p["computational_final_campaign"] is True
    assert p["protocol"]["sigma_px"] == 1.5
    assert p["protocol"]["p_ads"] == 1.0
    assert p["s_star_not_substituted_for_p_ads"] is True


def test_extended_stats_percentiles() -> None:
    st = extended_stats([1.0, 2.0, 3.0, 4.0, 5.0])
    assert st["median"] == 3.0
    assert st["percentile_25"] is not None
    assert st["ci95"] is not None


def test_run_record_fields() -> None:
    r = run_simulation(seed=1, sigma_px=1.5, n_steps=5, p_ads=1.0)
    rec = run_record(r)
    assert rec["c0_mg_l"] == 100.0
    assert rec["temperature_c"] == 25.0
    assert rec["provenance_classification"] == FINAL_CAMPAIGN_CLASSIFICATION


def test_comparison_go_ac_smoke() -> None:
    go = aggregate_material(
        [
            {
                "material": "GO",
                "seed": 1,
                "mass_conservation_ok": True,
                "n_adsorbed": 180,
                "percent_adsorbed": 90,
                "qfinal_mg_g": 360,
                "n_contacts": 500,
                "n_adsorption_events": 180,
                "contact_to_adsorption_efficiency": 0.36,
                "m_adsorbed_mg": 3.6,
                "m_free_mg": 0.4,
            }
        ],
        "GO",
    )
    ac = aggregate_material(
        [
            {
                "material": "AC",
                "seed": 1,
                "mass_conservation_ok": True,
                "n_adsorbed": 130,
                "percent_adsorbed": 65,
                "qfinal_mg_g": 260,
                "n_contacts": 300,
                "n_adsorption_events": 130,
                "contact_to_adsorption_efficiency": 0.43,
                "m_adsorbed_mg": 2.6,
                "m_free_mg": 1.4,
            }
        ],
        "AC",
    )
    rows = comparison_go_ac(go, ac)
    assert rows[0]["metric"] == "n_adsorbed"


def test_final_campaign_mini(tmp_path: Path) -> None:
    from go_mb import final_campaign as mod

    old_go, old_ac = mod.GO_SEEDS, mod.AC_SEEDS
    try:
        mod.GO_SEEDS = [1]
        mod.AC_SEEDS = [2]
        result = run_final_campaign(output_dir=tmp_path / "fc", plot=False)
        assert result["n_runs"] == 2
        assert result["mass_conservation_all_ok"]
        assert Path(result["outputs"]["statistics_json"]).exists()
    finally:
        mod.GO_SEEDS, mod.AC_SEEDS = old_go, old_ac
