"""Estado computacional del recinto GO–MB."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from go_mb.config import RunSettings, SimulationConfig


@dataclass
class SimulationState:
    config: SimulationConfig
    seed: int
    mb_xy: np.ndarray
    go_xy: np.ndarray
    mb_free: np.ndarray
    go_capacity_mg: np.ndarray
    step: int = 0
    n_contacts: int = 0
    n_adsorption_events: int = 0
    rng_state: dict[str, object] = field(default_factory=dict)

    @property
    def n_adsorbed(self) -> int:
        return int(np.count_nonzero(~self.mb_free))

    @property
    def n_free(self) -> int:
        return int(np.count_nonzero(self.mb_free))

    @property
    def m_adsorbed_mg(self) -> float:
        return self.n_adsorbed * self.config.peso_mb_mg

    @property
    def m_free_mg(self) -> float:
        return self.config.m_mb_mg - self.m_adsorbed_mg

    @property
    def qt_mg_g(self) -> float:
        return self.m_adsorbed_mg / self.config.m_go_g


def _aabb_overlap(
    xy: np.ndarray,
    half: float,
    others: list[tuple[np.ndarray, float]],
) -> bool:
    x, y = float(xy[0]), float(xy[1])
    for o_xy, o_half in others:
        if abs(x - float(o_xy[0])) < half + o_half and abs(y - float(o_xy[1])) < half + o_half:
            return True
    return False


def _place_group(
    n: int,
    half: float,
    domain: float,
    rng: np.random.Generator,
    occupied: list[tuple[np.ndarray, float]],
    avoid_overlap: bool,
    max_attempts: int,
) -> np.ndarray:
    lo = half
    hi = domain - half
    if hi <= lo:
        raise ValueError("El recinto es demasiado pequeño para el tamaño de partícula")
    out = np.empty((n, 2), dtype=np.float64)
    for i in range(n):
        placed = False
        for _ in range(max_attempts):
            cand = rng.uniform(lo, hi, size=2)
            if avoid_overlap and _aabb_overlap(cand, half, occupied):
                continue
            out[i] = cand
            occupied.append((out[i], half))
            placed = True
            break
        if not placed:
            out[i] = rng.uniform(lo, hi, size=2)
            occupied.append((out[i], half))
    return out


def initialize_state(config: SimulationConfig, settings: RunSettings) -> tuple[SimulationState, np.random.Generator]:
    rng = np.random.default_rng(settings.seed)
    occupied: list[tuple[np.ndarray, float]] = []
    go_xy = _place_group(
        config.n_go,
        config.r_go_px,
        float(config.domain_px),
        rng,
        occupied,
        settings.avoid_overlap,
        settings.max_place_attempts,
    )
    mb_xy = _place_group(
        config.n_mb,
        config.r_mb_px,
        float(config.domain_px),
        rng,
        occupied,
        settings.avoid_overlap,
        settings.max_place_attempts,
    )
    state = SimulationState(
        config=config,
        seed=settings.seed,
        mb_xy=mb_xy,
        go_xy=go_xy,
        mb_free=np.ones(config.n_mb, dtype=bool),
        go_capacity_mg=np.full(config.n_go, config.cap_go_mg, dtype=np.float64),
    )
    return state, rng


def assert_inside(state: SimulationState) -> None:
    domain = float(state.config.domain_px)
    for xy, half in (
        (state.mb_xy, state.config.r_mb_px),
        (state.go_xy, state.config.r_go_px),
    ):
        if np.any(xy[:, 0] < half - 1e-9) or np.any(xy[:, 0] > domain - half + 1e-9):
            raise AssertionError("Objeto fuera del recinto en x")
        if np.any(xy[:, 1] < half - 1e-9) or np.any(xy[:, 1] > domain - half + 1e-9):
            raise AssertionError("Objeto fuera del recinto en y")
