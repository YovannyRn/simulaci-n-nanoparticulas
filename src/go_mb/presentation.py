"""Valores predeterminados de presentación (referencia al protocolo final, sin duplicar física)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from go_mb.final_campaign import N_STEPS, P_ADS, SIGMA_PX

MaterialChoice = Literal["GO", "AC"]


@dataclass(frozen=True)
class PresentationDefaults:
    material: MaterialChoice = "GO"
    seed: int = 1
    sigma_px: float = SIGMA_PX
    n_steps: int = N_STEPS
    p_ads: float = P_ADS
    interval_ms: int = 35
    show_advanced_p_ads: bool = False


def default_presentation() -> PresentationDefaults:
    return PresentationDefaults()
