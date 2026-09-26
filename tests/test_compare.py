"""Comparación descriptiva GO vs AC desde estudios guardados."""

from __future__ import annotations

from pathlib import Path

import pytest

from go_mb.compare import (
    DEFAULT_CONFIGURATIONS,
    build_comparison_table,
    run_descriptive_comparison,
    stats_for_configuration,
)
from go_mb.io import load_study


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_build_table_matches_documented_means(repo_root: Path) -> None:
    go_path = repo_root / "data/sensitivity/seeds/study_sigma_steps_grid.json"
    ac_path = repo_root / "data/sensitivity/ac/seeds/study_ac_seeds.json"
    if not go_path.exists() or not ac_path.exists():
        pytest.skip("Estudios GO/AC no presentes en el workspace")
    go_study = load_study(go_path)
    ac_study = load_study(ac_path)
    table = build_comparison_table(go_study, ac_study)
    assert len(table) == 4
    row = next(r for r in table if r.sigma_px == 1.0 and r.n_steps == 400)
    assert abs(row.go.n_adsorbed_mean - 115.0) < 1e-9
    assert abs(row.ac.n_adsorbed_mean - 79.8) < 1e-9
    assert row.delta_n_adsorbed_mean == pytest.approx(115.0 - 79.8)
    assert row.go.n_contacts_mean is not None
    assert row.ac.n_contacts_mean is not None


def test_run_descriptive_comparison_writes_outputs(repo_root: Path, tmp_path: Path) -> None:
    go_path = repo_root / "data/sensitivity/seeds/study_sigma_steps_grid.json"
    ac_path = repo_root / "data/sensitivity/ac/seeds/study_ac_seeds.json"
    if not go_path.exists() or not ac_path.exists():
        pytest.skip("Estudios GO/AC no presentes en el workspace")
    result = run_descriptive_comparison(
        go_seeds_study=go_path,
        ac_seeds_study=ac_path,
        output_dir=tmp_path,
        plot=True,
    )
    assert Path(result["json"]).exists()
    assert Path(result["csv"]).exists()
    assert result["figures"]
    prov = result["provenance"]
    assert prov["not_experimental_validation"] is True
    assert prov["no_langmuir_selection"] is True
    assert "GO" in prov["inputs"] and "AC" in prov["inputs"]


def test_stats_spread_from_seeds(repo_root: Path) -> None:
    go_path = repo_root / "data/sensitivity/seeds/study_sigma_steps_grid.json"
    if not go_path.exists():
        pytest.skip("Estudio GO seeds ausente")
    go_study = load_study(go_path)
    st = stats_for_configuration(go_study, "GO", 1.5, 400)
    assert st is not None
    assert st.n_adsorbed_spread == 20
    assert st.n_seeds == 5
