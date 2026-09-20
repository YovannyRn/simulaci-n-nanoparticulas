"""Visualización Matplotlib. No altera semillas ni métricas; solo lee resultados."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_run(result: dict[str, Any], output_path: str | Path) -> str:
    series = result["series"]
    steps = [row["step"] for row in series]
    qt = [row["qt_mg_g"] for row in series]
    pct = [row["percent_adsorbed"] for row in series]
    c_rem = [row["c_remaining_mg_l"] for row in series]
    c_pdf = [row["c_pdf_mg_l"] for row in series]
    qe = result["reference"]["langmuir"]["qe_mg_g"]
    ce = result["reference"]["langmuir"]["ce_mg_l"]

    fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
    axes[0].plot(steps, pct, color="tab:blue")
    axes[0].set_ylabel("% MB adsorbido")
    axes[0].set_title("Evolución simulada (pasos, no minutos)")
    axes[1].plot(steps, qt, color="tab:green", label="qt simulada")
    axes[1].axhline(qe, color="tab:green", ls="--", alpha=0.7, label=f"qe Langmuir ref. {qe:.1f}")
    axes[1].set_ylabel("qt (mg/g)")
    axes[1].legend()
    axes[2].plot(steps, c_rem, color="tab:red", label="C restante = m_libre/V")
    axes[2].plot(steps, c_pdf, color="tab:orange", ls=":", label="C PDF = m_ads/V")
    axes[2].axhline(ce, color="tab:red", ls="--", alpha=0.7, label=f"Ce ref. {ce:.2f}")
    axes[2].set_ylabel("C (mg/L)")
    axes[2].set_xlabel("paso")
    axes[2].legend()
    fig.tight_layout()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return str(output_path)


def plot_snapshot(result: dict[str, Any], output_path: str | Path) -> str:
    cfg = result["config"]
    domain = cfg["domain_px"]
    mb = np.asarray(result["final_state"]["mb_xy"])
    go = np.asarray(result["final_state"]["go_xy"])
    free = np.asarray(result["final_state"]["mb_free"], dtype=bool)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, domain)
    ax.set_ylim(0, domain)
    ax.set_aspect("equal")
    go_s = cfg["go_size_px"]
    mb_s = cfg["mb_size_px"]
    ax.scatter(go[:, 0], go[:, 1], s=go_s ** 2, c="black", marker="s", label="GO", zorder=2)
    if np.any(free):
        ax.scatter(mb[free, 0], mb[free, 1], s=mb_s ** 2, c="tab:blue", marker="s", label="MB libre")
    if np.any(~free):
        ax.scatter(mb[~free, 0], mb[~free, 1], s=mb_s ** 2, c="tab:red", marker="s", label="MB adsorbido")
    last_step = result["series"][-1]["step"] if result.get("series") else result["summary"].get("n_adsorbed", "")
    ax.set_title(f"Semilla {result['run']['seed']}  |  paso {last_step}")
    ax.set_xlabel("px")
    ax.set_ylabel("px")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return str(output_path)
