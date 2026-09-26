"""Figuras calibración temporal (separadas del motor)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from go_mb.models import pso_qt
from go_mb.temporal_calibration import PSO_K2_G_MG_MIN, PSO_QE_MG_G


def _go_crossings(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for r in analysis["fraction_crossings"] if r["material"] == "GO"]


def _filter_go_sigma(crossings: list[dict[str, Any]], sigma: float) -> list[dict[str, Any]]:
    return [
        r
        for r in crossings
        if abs(float(r["sigma_px"]) - sigma) < 1e-9 and r["reach_status"] == "reached"
    ]


def plot_temporal_calibration(
    analysis: dict[str, Any],
    campaign_root: Path,
    output_dir: Path,
) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    go_x = _go_crossings(analysis)

    # 3. PSO qt vs tiempo
    t_vals = [i * 5.0 for i in range(0, 401)]
    qt_vals = [pso_qt(PSO_K2_G_MG_MIN, PSO_QE_MG_G, t) for t in t_vals]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t_vals, qt_vals, color="tab:purple", label="PSO referencia GO")
    ax.axhline(PSO_QE_MG_G * 0.5, color="gray", ls="--", lw=0.8, label="50% qe_PSO")
    ax.set_xlabel("t (min)")
    ax.set_ylabel("qt (mg/g)")
    ax.set_title("Referencia PSO GO (no calibra el motor)")
    ax.legend(fontsize=8)
    p = output_dir / "pso_qt_vs_time_min.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(str(p))

    # 4. alpha vs fracción (GO, medias por sigma)
    for sigma, label in ((1.0, "1_0"), (1.5, "1_5")):
        pts = _filter_go_sigma(go_x, sigma)
        by_f: dict[float, list[float]] = {}
        for r in pts:
            a = r.get("alpha_min_per_step")
            if a is not None:
                by_f.setdefault(float(r["fraction_of_pso_qe"]), []).append(float(a))
        if not by_f:
            continue
        fracs = sorted(by_f)
        means = [sum(by_f[f]) / len(by_f[f]) for f in fracs]
        stds = [
            (sum((x - means[i]) ** 2 for x in by_f[f]) / max(len(by_f[f]) - 1, 1)) ** 0.5
            if len(by_f[f]) > 1
            else 0.0
            for i, f in enumerate(fracs)
        ]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.errorbar(
            [f * 100 for f in fracs],
            means,
            yerr=stds,
            fmt="o-",
            capsize=3,
            label=f"GO σ={sigma}",
        )
        ax.set_xlabel("Fracción de qe_PSO (%)")
        ax.set_ylabel("α exploratorio (min/paso)")
        ax.set_title(f"α vs fracción — GO σ={sigma} (exploratorio)")
        ax.legend(fontsize=8)
        p = output_dir / f"alpha_vs_fraction_go_sigma_{label}.png"
        fig.savefig(p, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(str(p))

    # 5. alpha vs fracción por seed (GO σ=1.0 ejemplo)
    pts = _filter_go_sigma(go_x, 1.0)
    seeds = sorted({int(r["seed"]) for r in pts})
    fig, ax = plt.subplots(figsize=(8, 4))
    for seed in seeds:
        sub = [
            r
            for r in pts
            if int(r["seed"]) == seed and r.get("alpha_min_per_step") is not None
        ]
        sub.sort(key=lambda x: float(x["fraction_of_pso_qe"]))
        if not sub:
            continue
        ax.plot(
            [float(r["fraction_of_pso_qe"]) * 100 for r in sub],
            [float(r["alpha_min_per_step"]) for r in sub],
            "o-",
            label=f"seed {seed}",
            ms=4,
        )
    ax.set_xlabel("Fracción de qe_PSO (%)")
    ax.set_ylabel("α exploratorio (min/paso)")
    ax.set_title("α vs fracción por seed — GO σ=1.0")
    ax.legend(fontsize=7, ncol=2)
    p = output_dir / "alpha_vs_fraction_go_by_seed_sigma_1_0.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(str(p))

    # 6. Comparación sigma 1.0 vs 1.5 (media alpha)
    fig, ax = plt.subplots(figsize=(8, 4))
    for sigma, color in ((1.0, "tab:blue"), (1.5, "tab:orange")):
        pts = _filter_go_sigma(go_x, sigma)
        by_f: dict[float, list[float]] = {}
        for r in pts:
            a = r.get("alpha_min_per_step")
            if a is not None:
                by_f.setdefault(float(r["fraction_of_pso_qe"]), []).append(float(a))
        fracs = sorted(by_f)
        if not fracs:
            continue
        means = [sum(by_f[f]) / len(by_f[f]) for f in fracs]
        ax.plot([f * 100 for f in fracs], means, "o-", color=color, label=f"σ={sigma}")
    ax.set_xlabel("Fracción de qe_PSO (%)")
    ax.set_ylabel("α exploratorio (min/paso)")
    ax.set_title("GO: σ=1.0 vs σ=1.5 (media sobre seeds)")
    ax.legend()
    p = output_dir / "alpha_vs_fraction_go_sigma_compare.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(str(p))

    # 1–2: qt y fracción vs steps (curvas ejemplo desde CSV campaña)
    from go_mb.io import load_run

    for sigma, label in ((1.0, "1_0"), (1.5, "1_5")):
        example = campaign_root / "go" / f"sens_grid_sigma_{sigma:g}_steps_2000_seed_1.json"
        if not example.is_file():
            continue
        data = load_run(example)
        series = data["series"]
        steps = [int(r["step"]) for r in series]
        qt = [float(r["qt_mg_g"]) for r in series]
        frac = [q / PSO_QE_MG_G for q in qt]
        fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
        axes[0].plot(steps, qt, lw=0.8)
        axes[0].set_ylabel("qt (mg/g)")
        axes[0].set_title(f"GO σ={sigma} seed=1 P=2000 (ejemplo)")
        axes[1].plot(steps, [f * 100 for f in frac], lw=0.8, color="tab:green")
        axes[1].set_ylabel("qt / qe_PSO (%)")
        axes[1].set_xlabel("steps (≠ min)")
        p = output_dir / f"sim_qt_and_fraction_vs_steps_go_sigma_{label}_example.png"
        fig.savefig(p, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(str(p))

    # 7. Tabla reachability (GO vs AC conteos)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("off")
    lines = ["Fracciones alcanzables (reach_status=reached), conteo sobre 140 corridas×9 fracs"]
    for material in ("GO", "AC"):
        sub = [r for r in analysis["fraction_crossings"] if r["material"] == material]
        reached = sum(1 for r in sub if r["reach_status"] == "reached")
        lines.append(f"{material}: {reached}/{len(sub)} celdas fracción×corrida")
    ax.text(0.02, 0.5, "\n".join(lines), va="center", fontsize=10, family="monospace")
    p = output_dir / "reachability_summary.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(str(p))

    return paths
