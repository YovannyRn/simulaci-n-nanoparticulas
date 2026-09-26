"""Figuras campaña temporal homogénea GO vs AC."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _plot_metric_vs_steps(
    go_agg: list[dict[str, Any]],
    ac_agg: list[dict[str, Any]],
    sigma: float,
    metric_key: str,
    ylabel: str,
    title: str,
    output_path: Path,
) -> str:
    go_pts = sorted([r for r in go_agg if abs(r["sigma_px"] - sigma) < 1e-9], key=lambda x: x["n_steps"])
    ac_pts = sorted([r for r in ac_agg if abs(r["sigma_px"] - sigma) < 1e-9], key=lambda x: x["n_steps"])
    steps = [r["n_steps"] for r in go_pts]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.errorbar(
        steps,
        [r[metric_key]["mean"] for r in go_pts],
        yerr=[r[metric_key]["std"] for r in go_pts],
        fmt="o-",
        capsize=3,
        label="GO (móvil)",
        color="tab:gray",
    )
    ax.errorbar(
        steps,
        [r[metric_key]["mean"] for r in ac_pts],
        yerr=[r[metric_key]["std"] for r in ac_pts],
        fmt="s-",
        capsize=3,
        label="AC (fijo)",
        color="tab:orange",
    )
    ax.set_xlabel("pasos (no minutos)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return str(output_path)


def plot_homogeneous_comparison(
    go_agg: list[dict[str, Any]],
    ac_agg: list[dict[str, Any]],
    output_dir: Path,
) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    metrics = [
        ("n_adsorbed", "Nads (media ± σ entre seeds)", "Nads vs pasos"),
        ("percent_adsorbed", "% adsorbido", "% adsorbido vs pasos"),
        ("qt_mg_g", "qt (mg/g)", "qt vs pasos"),
        ("n_contacts", "contactos acumulados", "Contactos vs pasos (≠ Nads)"),
    ]
    for sigma in sorted({r["sigma_px"] for r in go_agg}):
        tag = str(sigma).replace(".", "_")
        for key, ylab, title in metrics:
            p = _plot_metric_vs_steps(
                go_agg,
                ac_agg,
                sigma,
                key,
                ylab,
                f"{title} — σ={sigma:g}",
                output_dir / f"homogeneous_{key}_sigma_{tag}.png",
            )
            paths.append(p)
    return paths
