"""Figuras comparativas GO vs AC (solo lectura de informes)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from go_mb.compare import ComparisonRow


def _config_labels(table: list[ComparisonRow]) -> list[str]:
    return [f"σ={r.sigma_px:g}\nP={r.n_steps}" for r in table]


def plot_comparison_figures(
    report: dict[str, Any],
    table: list[ComparisonRow],
    output_dir: Path,
) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    labels = _config_labels(table)
    x = np.arange(len(table))
    width = 0.35

    def grouped_bar(go_vals, ac_vals, ylabel: str, title: str, fname: str) -> None:
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.bar(x - width / 2, go_vals, width, label="GO (móvil)", color="tab:gray")
        ax.bar(x + width / 2, ac_vals, width, label="AC (fijo)", color="tab:orange")
        ax.set_xticks(x, labels, fontsize=8)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()
        fig.tight_layout()
        p = output_dir / fname
        fig.savefig(p, dpi=120)
        plt.close(fig)
        paths.append(str(p))

    grouped_bar(
        [r.go.n_adsorbed_mean for r in table],
        [r.ac.n_adsorbed_mean for r in table],
        "Nads (media, 5 seeds)",
        "Comparación descriptiva: Nads",
        "compare_n_adsorbed_mean.png",
    )
    grouped_bar(
        [r.go.percent_adsorbed_mean for r in table],
        [r.ac.percent_adsorbed_mean for r in table],
        "% adsorbido (media)",
        "Comparación descriptiva: % adsorbido",
        "compare_percent_adsorbed_mean.png",
    )
    grouped_bar(
        [r.go.qfinal_mg_g_mean for r in table],
        [r.ac.qfinal_mg_g_mean for r in table],
        "qt final (mg/g, media)",
        "Comparación descriptiva: qt (no objetivo Langmuir)",
        "compare_qt_mean.png",
    )
    go_c = [r.go.n_contacts_mean or 0 for r in table]
    ac_c = [r.ac.n_contacts_mean or 0 for r in table]
    grouped_bar(
        go_c,
        ac_c,
        "Contactos acumulados (media)",
        "Comparación descriptiva: contactos (≠ Nads)",
        "compare_contacts_mean.png",
    )

    # Variabilidad entre seeds
    sv = report.get("seed_variability") or []
    if sv:
        fig, ax = plt.subplots(figsize=(10, 4))
        keys = sorted({(e["sigma_px"], e["n_steps"]) for e in sv})
        xl = [f"σ={s:g}\nP={p}" for s, p in keys]
        for mat, color, offset in (("GO", "tab:gray", -0.15), ("AC", "tab:orange", 0.15)):
            by_key = {(e["sigma_px"], e["n_steps"]): e["n_adsorbed_spread"] for e in sv if e.get("material") == mat}
            spreads = [by_key.get(k, 0) for k in keys]
            ax.bar(np.arange(len(keys)) + offset, spreads, width=0.25, label=mat, color=color)
        ax.set_xticks(range(len(keys)), xl, fontsize=8)
        ax.set_ylabel("Spread Nads (max−min)")
        ax.set_title("Variabilidad entre seeds (GO vs AC)")
        ax.legend()
        fig.tight_layout()
        p = output_dir / "compare_seed_variability_spread.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        paths.append(str(p))

    evo = report.get("temporal_evolution") or {}
    for key, sigma_label in (("sigma_1_0", "σ=1.0"), ("sigma_1_5", "σ=1.5")):
        block = evo.get(key) or {}
        go_pts = block.get("GO") or []
        ac_pts = block.get("AC") or []
        if not go_pts or not ac_pts:
            continue
        fig, axes = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
        for pts, label, color in ((go_pts, "GO", "tab:gray"), (ac_pts, "AC", "tab:orange")):
            steps = [p["n_steps"] for p in pts]
            axes[0].plot(steps, [p["n_adsorbed"] for p in pts], "o-", color=color, label=label)
            axes[1].plot(steps, [p["percent_adsorbed"] for p in pts], "o-", color=color, label=label)
            axes[2].plot(steps, [p["n_contacts"] for p in pts], "o-", color=color, label=label)
        axes[0].set_ylabel("Nads")
        axes[1].set_ylabel("% ads")
        axes[2].set_ylabel("contactos")
        axes[2].set_xlabel("pasos (horizonte simulado, no minutos)")
        axes[0].set_title(f"Evolución vs pasos — {sigma_label}, seed=1")
        for ax in axes:
            ax.legend(fontsize=8)
        fig.tight_layout()
        p = output_dir / f"compare_evolution_steps_{key}.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        paths.append(str(p))

    return paths
