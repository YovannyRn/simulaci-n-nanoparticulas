"""Geometría Wiam: MB 1×1, GO 7×7, AC 2×2; contacto por radios inscritos."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import numpy as np

from go_mb.adsorption import apply_adsorption
from go_mb.config import (
    MaterialKind,
    SimulationConfig,
    WIAM_AC_SIDE_PX,
    WIAM_GO_SIDE_PX,
    WIAM_MB_SIDE_PX,
    ac_config,
    default_config,
)
from go_mb.contact import contact_pairs
from go_mb.state import SimulationState


def test_mb_go_ac_visual_sizes_and_radii() -> None:
    go_cfg = default_config()
    ac_cfg = ac_config()
    assert go_cfg.mb_size_px == WIAM_MB_SIDE_PX == 1
    assert go_cfg.go_size_px == WIAM_GO_SIDE_PX == 7
    assert ac_cfg.mb_size_px == 1
    assert ac_cfg.go_size_px == WIAM_AC_SIDE_PX == 2
    assert go_cfg.r_mb_px == 0.5
    assert go_cfg.r_go_px == 3.5
    assert ac_cfg.r_mb_px == 0.5
    assert ac_cfg.r_go_px == 1.0


def test_contact_detector_uses_config_radii() -> None:
    src = inspect.getsource(contact_pairs)
    assert "state.config.r_mb_px + state.config.r_go_px" in src

    go_cfg = SimulationConfig(n_mb=1, n_go=1)
    thresh_go = go_cfg.r_mb_px + go_cfg.r_go_px
    mb = np.array([[50.0, 50.0]])
    go = np.array([[50.0 + thresh_go, 50.0]])
    st_go = SimulationState(
        config=go_cfg,
        seed=0,
        mb_xy=mb,
        go_xy=go,
        mb_free=np.array([True]),
        go_capacity_mg=np.array([go_cfg.cap_go_mg]),
    )
    assert len(contact_pairs(st_go)) == 1

    base_ac = ac_config()
    ac_cfg = SimulationConfig(
        material=MaterialKind.AC,
        adsorbent_movable=base_ac.adsorbent_movable,
        n_mb=1,
        n_go=1,
        mb_size_px=WIAM_MB_SIDE_PX,
        go_size_px=WIAM_AC_SIDE_PX,
        qmax_mg_g=base_ac.qmax_mg_g,
    )
    thresh_ac = ac_cfg.r_mb_px + ac_cfg.r_go_px
    assert thresh_ac == 1.5
    ac_pos = np.array([[50.0 + thresh_ac, 50.0]])
    st_ac = SimulationState(
        config=ac_cfg,
        seed=0,
        mb_xy=mb,
        go_xy=ac_pos,
        mb_free=np.array([True]),
        go_capacity_mg=np.array([ac_cfg.cap_go_mg]),
    )
    assert len(contact_pairs(st_ac)) == 1
    assert len(contact_pairs(_shift_state(st_ac, extra=0.01))) == 0


def _shift_state(state: SimulationState, extra: float) -> SimulationState:
    go = state.go_xy.copy()
    go[0, 0] += extra
    return SimulationState(
        config=state.config,
        seed=state.seed,
        mb_xy=state.mb_xy.copy(),
        go_xy=go,
        mb_free=state.mb_free.copy(),
        go_capacity_mg=state.go_capacity_mg.copy(),
    )


def test_go_mobile_ac_fixed() -> None:
    assert default_config().adsorbent_movable is True
    assert ac_config().adsorbent_movable is False


def test_apply_adsorption_source_unchanged_signature() -> None:
    sig = inspect.signature(apply_adsorption)
    assert list(sig.parameters.keys()) == ["state", "pairs", "rng", "p_ads"]


def test_motor_scientific_modules_no_matplotlib() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "go_mb"
    for name in (
        "engine.py",
        "contact.py",
        "motion.py",
        "adsorption.py",
        "state.py",
        "config.py",
    ):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] != "matplotlib", name
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("matplotlib"), name
