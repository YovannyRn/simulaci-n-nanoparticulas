"""Campañas de repeticiones. Cada corrida usa su propio RNG y semilla persistida."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from go_mb.config import RunSettings, SimulationConfig
from go_mb.engine import run_simulation
from go_mb.io import save_run
from go_mb.stats import summarize_campaign


def run_campaign(
    *,
    n_rep: int,
    base_seed: int,
    sigma_px: float,
    n_steps: int,
    config: SimulationConfig | None = None,
    p_ads: float | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    if n_rep < 1:
        raise ValueError("n_rep debe ser ≥ 1 (el PDF no unifica 30 vs 40; hay que inyectarlo)")
    cfg = config or SimulationConfig()
    runs: list[dict[str, Any]] = []
    paths: list[dict[str, str]] = []
    for i in range(n_rep):
        seed = base_seed + i
        settings = RunSettings(seed=seed, sigma_px=sigma_px, n_steps=n_steps, p_ads=p_ads)
        result = run_simulation(cfg, settings)
        runs.append(result)
        if output_dir is not None:
            paths.append(save_run(result, output_dir, f"go_seed_{seed}"))
    campaign = {
        "n_rep": n_rep,
        "base_seed": base_seed,
        "seed_scheme": "seed_i = base_seed + i",
        "seed_scheme_status": "DECISIÓN COMPUTACIONAL",
        "stats": summarize_campaign(runs),
        "paths": paths,
        "ca_status": "PENDIENTE: el PDF no parametriza CA; no se ejecuta el sistema 2.",
    }
    return campaign
