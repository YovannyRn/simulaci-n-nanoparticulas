"""Figuras análisis protocolo final (P=2000)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from go_mb.io import load_run
from go_mb.temporal_calibration import PSO_QE_MG_G


def _series_for_runs(
    campaign_root: Path,
    material: str,
    sigma: float,
    seeds: list[int],
) -> dict[int, list[dict[str, float | int]]]:
    sub = "go" if material == "GO" else "ac"
    prefix = "ac_" if material == "AC" else ""
    out: dict[int, list[dict[str, float | int]]] = {}
    for seed in seeds:
        path = (
            campaign_root
            / sub
            / f"{prefix}sens_grid_sigma_{sigma:g}_steps_2000_seed_{seed}.json"
        )
        if path.is_file():
            out[seed] = load_run(path)["series"]
    return out


def _mean_std_series(
    by_seed: dict[int, list[dict[str, float | int]]],
    key: str,
) -> tuple[list[int], list[float], list[float]]:
    if not by_seed:
        return [], [], []
    steps = sorted({int(r["step"]) for s in by_seed.values() for r in s})
    means: list[float] = []
    stds: list[float] = []
    for st in steps:
        vals = [
            float(next(r[key] for r in ser if int(r["step"]) == st))
            for ser in by_seed.values()
            if any(int(r["step"]) == st for r in ser)
        ]
        if not vals:
            means.append(float("nan"))
            stds.append(float("nan"))
            continue
        m = sum(vals) / len(vals)
        if len(vals) > 1:
            var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
            sd = var**0.5
        else:
            sd = 0.0
        means.append(m)
        stds.append(sd)
    return steps, means, stds


def plot_final_protocol(
    p2000: list[dict[str, Any]],
    campaign_root: Path,
    crossings: list[dict[str, Any]],
    output_dir: Path,
) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    seeds = sorted({int(r["seed"]) for r in p2000})

    for material in ("GO", "AC"):
        for sigma in (1.0, 1.5):
            by_seed = _series_for_runs(campaign_root, material, sigma, seeds)
            steps, qt_m, qt_s = _mean_std_series(by_seed, "qt_mg_g")
            _, pct_m, pct_s = _mean_std_series(by_seed, "percent_adsorbed")

            fig, ax = plt.subplots(figsize=(8, 4))
            for seed, ser in by_seed.items():
                ax.plot(
                    [int(r["step"]) for r in ser],
                    [float(r["qt_mg_g"]) for r in ser],
                    alpha=0.25,
                    lw=0.6,
                )
            ax.errorbar(steps, qt_m, yerr=qt_s, color="black", capsize=2, label="media ± std")
            ax.set_xlabel("steps (≠ min)")
            ax.set_ylabel("qt (mg/g)")
            ax.set_title(f"{material} σ={sigma} P=2000 — qt vs steps")
            ax.legend(fontsize=8)
            p = output_dir / f"qt_vs_steps_{material.lower()}_sigma_{sigma:g}.png"
            fig.savefig(p, dpi=150, bbox_inches="tight")
            plt.close(fig)
            paths.append(str(p))

            fig, ax = plt.subplots(figsize=(8, 4))
            for seed, ser in by_seed.items():
                ax.plot(
                    [int(r["step"]) for r in ser],
                    [float(r["percent_adsorbed"]) for r in ser],
                    alpha=0.25,
                    lw=0.6,
                )
            ax.errorbar(steps, pct_m, yerr=pct_s, color="black", capsize=2, label="media ± std")
            ax.set_xlabel("steps (≠ min)")
            ax.set_ylabel("Nads (%)")
            ax.set_title(f"{material} σ={sigma} P=2000 — % adsorbido vs steps")
            ax.legend(fontsize=8)
            p = output_dir / f"percent_vs_steps_{material.lower()}_sigma_{sigma:g}.png"
            fig.savefig(p, dpi=150, bbox_inches="tight")
            plt.close(fig)
            paths.append(str(p))

    # alpha vs fraction GO P=2000
    sub = [
        r
        for r in crossings
        if r.get("material") == "GO"
        and int(float(r.get("n_steps_horizon", 0))) == 2000
        and r.get("reach_status") == "reached"
        and r.get("alpha_min_per_step")
    ]
    fig, ax = plt.subplots(figsize=(8, 4))
    for sigma, color in ((1.0, "tab:blue"), (1.5, "tab:orange")):
        by_f: dict[float, list[float]] = {}
        for r in sub:
            if abs(float(r["sigma_px"]) - sigma) > 1e-9:
                continue
            by_f.setdefault(float(r["fraction_of_pso_qe"]), []).append(
                float(r["alpha_min_per_step"])
            )
        fracs = sorted(by_f)
        if not fracs:
            continue
        means = [sum(by_f[f]) / len(by_f[f]) for f in fracs]
        ax.plot([f * 100 for f in fracs], means, "o-", color=color, label=f"σ={sigma}")
    ax.set_xlabel("Fracción qe_PSO (%)")
    ax.set_ylabel("α exploratorio (min/paso)")
    ax.set_title("GO P=2000 — α vs fracción (media seeds)")
    ax.legend()
    p = output_dir / "alpha_vs_fraction_go_p2000.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(str(p))

    return paths
