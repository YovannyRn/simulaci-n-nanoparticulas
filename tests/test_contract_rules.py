"""Contrato de auditoría: reglas de la spec, sin clavar física inventada."""

from __future__ import annotations

import ast
import inspect
import os
import subprocess
import sys
from pathlib import Path

from go_mb.adsorption import apply_adsorption
from go_mb.config import OriginStatus, RunSettings, SimulationConfig, default_config
from go_mb.contact import contact_pairs
from go_mb.engine import run_simulation
from go_mb.motion import move


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "go_mb"

SCIENTIFIC_MODULES = [
    "config.py",
    "state.py",
    "motion.py",
    "contact.py",
    "adsorption.py",
    "models.py",
    "metrics.py",
    "engine.py",
    "io.py",
    "stats.py",
    "experiments.py",
]


def test_domain_masses_and_graphic_sizes() -> None:
    cfg = default_config()
    assert cfg.domain_px == 442
    assert cfg.n_mb == 200
    assert cfg.n_go == 100
    assert cfg.peso_mb_mg == 0.02
    assert cfg.peso_go_mg == 0.10
    assert cfg.mb_size_px == 5
    assert cfg.go_size_px == 7
    assert cfg.r_mb_px == 2.5
    assert cfg.r_go_px == 3.5
    assert abs(cfg.n_mb * cfg.peso_mb_mg - 4.0) < 1e-12
    assert abs(cfg.n_go * cfg.peso_go_mg - 10.0) < 1e-12


def test_contact_is_distance_threshold_only() -> None:
    src = inspect.getsource(contact_pairs)
    assert "dist <= thresh" in src or "dist <= thresh + 1e-12" in src
    assert "random" not in src
    assert "p_ads" not in src
    assert "langmuir" not in src.lower()


def test_langmuir_and_pso_are_isolated_from_detector_and_adsorption() -> None:
    contact_src = inspect.getsource(contact_pairs).lower()
    ads_src = inspect.getsource(apply_adsorption).lower()
    motion_src = inspect.getsource(move).lower()
    for src in (contact_src, ads_src, motion_src):
        assert "langmuir" not in src
        assert "pso" not in src
        assert "qmax" not in src
        assert "kl_l" not in src
    engine_src = (SRC / "engine.py").read_text()
    assert "apply_adsorption" in engine_src
    assert "reference_bundle" in engine_src
    # Langmuir/PSO se calculan para metadatos, no se pasan a adsorción.
    assert "apply_adsorption(state, pairs, rng, settings.p_ads)" in engine_src


def test_sigma_and_steps_are_injected_not_scientific_defaults() -> None:
    cfg_table = {p.symbol: p for p in SimulationConfig().parameter_table()}
    assert cfg_table["D"].status == OriginStatus.PENDIENTE
    assert cfg_table["P"].status == OriginStatus.PENDIENTE
    assert cfg_table["P_ads"].status == OriginStatus.PENDIENTE
    meta = RunSettings(seed=1, sigma_px=1.5, n_steps=400).metadata()
    assert meta["sigma_status"] == "PENDIENTE"
    assert meta["n_steps_status"] == "PENDIENTE"
    assert meta["sigma_role"] == "injected_execution_parameter"
    assert meta["n_steps_role"] == "injected_execution_parameter"
    assert meta["p_ads_implementation_status"] == "DECISIÓN COMPUTACIONAL PROVISIONAL"
    assert meta["adsorption_rule"] == "provisional_P_ads_eq_1_after_contact_and_capacity"
    assert "P_ads=1" in meta["adsorption_rule_note"]


def test_mass_conserved_every_recorded_step() -> None:
    result = run_simulation(seed=4, sigma_px=1.0, n_steps=25)
    cfg = default_config()
    for row in result["series"]:
        assert abs(float(row["m_adsorbed_mg"]) + float(row["m_free_mg"]) - cfg.m_mb_mg) < 1e-9
        assert int(row["n_adsorbed"]) + int(row["n_free"]) == cfg.n_mb
    assert result["summary"]["mass_conservation_ok"]
    assert result["summary"]["result_classification"] == (
        "computational_execution_not_experimental_validation"
    )


def test_same_seed_reproduces_full_run() -> None:
    kwargs = dict(seed=13, sigma_px=0.8, n_steps=12)
    a = run_simulation(**kwargs)
    b = run_simulation(**kwargs)
    assert a["summary"] == b["summary"]
    assert a["final_state"]["mb_xy"] == b["final_state"]["mb_xy"]
    assert a["final_state"]["go_xy"] == b["final_state"]["go_xy"]
    assert a["final_state"]["mb_free"] == b["final_state"]["mb_free"]


def test_scientific_modules_do_not_import_matplotlib() -> None:
    for name in SCIENTIFIC_MODULES:
        src = (SRC / name).read_text()
        assert "matplotlib" not in src
        assert "go_mb.viz" not in src


def test_cli_imports_viz_only_lazily() -> None:
    tree = ast.parse((SRC / "cli.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "go_mb.viz":
            raise AssertionError("viz no debe importarse en el nivel de cli")
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "matplotlib"


def test_engine_runs_in_process_without_matplotlib() -> None:
    code = (
        "import sys\n"
        "assert not any(m == 'matplotlib' or m.startswith('matplotlib.') for m in sys.modules)\n"
        "from go_mb.engine import run_simulation\n"
        "run_simulation(seed=0, sigma_px=0.0, n_steps=1)\n"
        "assert not any(m == 'matplotlib' or m.startswith('matplotlib.') for m in sys.modules)\n"
        "print('ok')\n"
    )
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "ok" in proc.stdout


def test_tests_do_not_freeze_demo_count_as_scientific_target() -> None:
    for path in (ROOT / "tests").glob("test_*.py"):
        src = path.read_text()
        assert "n_adsorbed == 146" not in src
        assert "146/200" not in src
