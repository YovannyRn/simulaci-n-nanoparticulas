"""Figuras referencia temporal GO/AC y sensibilidad P_ads contextual."""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from go_mb.io import load_run
from go_mb.pso_reference import AC_PSO, GO_PSO
from go_mb.temporal_calibration import discover_run_json_paths


def _p2000_paths(campaign_root: Path, material: str) -> list[Path]:
    sub = "go" if material == "GO" else "ac"
    return sorted(
        p
        for _, p in discover_run_json_paths(campaign_root)
        if p.parent.name == sub and "_steps_2000_" in p.name
    )


def _fraction_vs_steps_figure(
    campaign_root: Path,
    material: str,
    output_dir: Path,
) -> str:
    paths = _p2000_paths(campaign_root, material)
    fig, ax = plt.subplots(figsize=(8, 4))
    qe = GO_PSO.qe_pso_mg_g if material == "GO" else AC_PSO.qe_pso_mg_g
    for jpath in paths[:10]:
        data = load_run(jpath)
        series = data.get("series") or []
        steps = [int(r["step"]) for r in series]
        fracs = [float(r["qt_mg_g"]) / qe for r in series]
        ax.plot(steps, fracs, alpha=0.35, lw=0.8)
    for f in (0.1, 0.5, 0.9):
        ax.axhline(f, color="gray", ls="--", lw=0.6, alpha=0.7)
    ax.set_xlabel("steps (simulación)")
    ax.set_ylabel("qt / qe_PSO")
    ax.set_title(f"{material} — fracción PSO vs steps (P=2000, varias seeds/σ)")
    p = output_dir / f"fraction_vs_steps_{material.lower()}.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(p)


def _alpha_vs_fraction(crossings: list[dict[str, Any]], material: str, output_dir: Path) -> str:
    sub = [r for r in crossings if r["material"] == material and r["reach_status"] == "reached"]
    fig, ax = plt.subplots(figsize=(7, 4))
    for sigma, color in ((1.0, "tab:blue"), (1.5, "tab:orange")):
        by_f: dict[float, list[float]] = {}
        for r in sub:
            if abs(float(r["sigma_px"]) - sigma) > 1e-9:
                continue
            a = r.get("alpha_min_per_step")
            if a is not None:
                by_f.setdefault(float(r["fraction_of_pso_qe"]), []).append(float(a))
        if not by_f:
            continue
        fracs = sorted(by_f)
        means = [statistics.mean(by_f[f]) for f in fracs]
        stds = [
            statistics.stdev(by_f[f]) if len(by_f[f]) > 1 else 0.0 for f in fracs
        ]
        ax.errorbar(
            [f * 100 for f in fracs],
            means,
            yerr=stds,
            fmt="o-",
            capsize=3,
            color=color,
            label=f"σ={sigma}",
        )
    ax.set_xlabel("Fracción qe_PSO (%)")
    ax.set_ylabel("α (min/step, exploratorio)")
    ax.set_title(f"{material} — α vs fracción")
    ax.legend()
    p = output_dir / f"alpha_vs_fraction_{material.lower()}.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(p)


def _alpha_go_vs_ac(crossings: list[dict[str, Any]], output_dir: Path) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    for material, color in (("GO", "tab:blue"), ("AC", "tab:orange")):
        sub = [
            r
            for r in crossings
            if r["material"] == material
            and r["reach_status"] == "reached"
            and abs(float(r["sigma_px"]) - 1.5) < 1e-9
        ]
        by_f: dict[float, list[float]] = {}
        for r in sub:
            a = r.get("alpha_min_per_step")
            if a is not None:
                by_f.setdefault(float(r["fraction_of_pso_qe"]), []).append(float(a))
        fracs = sorted(by_f)
        if not fracs:
            continue
        means = [statistics.mean(by_f[f]) for f in fracs]
        ax.plot([f * 100 for f in fracs], means, "o-", color=color, label=material)
    ax.set_xlabel("Fracción qe_PSO (%)")
    ax.set_ylabel("α medio (min/step, σ=1.5)")
    ax.set_title("Comparación α GO vs AC (descriptivo, no validado)")
    ax.legend()
    p = output_dir / "alpha_go_vs_ac_sigma_1_5.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(p)


def _p_ads_panel(comparison: list[dict[str, Any]], material: str, output_dir: Path) -> str:
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    metrics = (
        ("n_adsorbed", "Nads"),
        ("qfinal_mg_g", "qt (mg/g)"),
        ("n_contacts", "Contactos"),
        ("contact_to_adsorption_efficiency", "Ads/contactos"),
    )
    p_vals = [0.5, 0.55, 0.75, 1.0]
    for ax, (key, ylab) in zip(axes.flat, metrics):
        for sigma, mk in ((1.0, "o"), (1.5, "s")):
            means: list[float] = []
            xs: list[float] = []
            for p in p_vals:
                sub = [
                    r
                    for r in comparison
                    if r["material"] == material
                    and abs(float(r["sigma_px"]) - sigma) < 1e-9
                    and abs(float(r["p_ads_effective"]) - p) < 1e-9
                ]
                if not sub:
                    continue
                vals = [float(r[key]) for r in sub if r.get(key) is not None]
                if vals:
                    xs.append(p)
                    means.append(statistics.mean(vals))
            if xs:
                ax.plot(xs, means, f"{mk}-", label=f"σ={sigma}")
        ax.set_xlabel("P_ads (computacional)")
        ax.set_ylabel(ylab)
    fig.suptitle(f"{material} — P_ads 0.50 / 0.55 / 0.75 / 1.00 (sin ganador)")
    fig.tight_layout()
    p = output_dir / f"p_ads_sensitivity_{material.lower()}_050_055_075_100.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(p)


def _p_ads_overlay(comparison: list[dict[str, Any]], output_dir: Path) -> str:
    fig, ax = plt.subplots(figsize=(8, 4))
    for material, color in (("GO", "tab:blue"), ("AC", "tab:orange")):
        for sigma, ls in ((1.0, "-"), (1.5, "--")):
            xs, ys = [], []
            for p in (0.5, 0.55, 0.75, 1.0):
                sub = [
                    r
                    for r in comparison
                    if r["material"] == material
                    and abs(float(r["sigma_px"]) - sigma) < 1e-9
                    and abs(float(r["p_ads_effective"]) - p) < 1e-9
                ]
                if sub:
                    xs.append(p)
                    ys.append(statistics.mean(float(r["n_adsorbed"]) for r in sub))
            if xs:
                ax.plot(
                    xs,
                    ys,
                    ls,
                    color=color,
                    label=f"{material} σ={sigma}",
                )
    ax.set_xlabel("P_ads")
    ax.set_ylabel("Nads medio")
    ax.set_title("Comparación P_ads (0.50–1.00 incl. 0.55 contextual)")
    ax.legend(fontsize=8)
    p = output_dir / "p_ads_comparison_nads_overlay.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(p)


def plot_final_temporal_reference(
    crossings: list[dict[str, Any]],
    comparison: list[dict[str, Any]],
    campaign_root: Path,
    output_dir: Path,
) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []

    for pso, mat, fname in (
        (GO_PSO, "GO", "pso_go_qt_vs_time_min.png"),
        (AC_PSO, "AC", "pso_ac_qt_vs_time_min.png"),
    ):
        t_vals = [i * 0.5 for i in range(0, 241)]
        qt_vals = [pso.qt(t) for t in t_vals]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(t_vals, qt_vals, color="tab:purple")
        ax.set_xlabel("t (min) — referencia PSO")
        ax.set_ylabel("qt (mg/g)")
        ax.set_title(f"Referencia PSO {mat} (no calibra el motor)")
        p = output_dir / fname
        fig.savefig(p, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(str(p))

    paths.append(_fraction_vs_steps_figure(campaign_root, "GO", output_dir))
    paths.append(_fraction_vs_steps_figure(campaign_root, "AC", output_dir))
    paths.append(_alpha_vs_fraction(crossings, "GO", output_dir))
    paths.append(_alpha_vs_fraction(crossings, "AC", output_dir))
    paths.append(_alpha_go_vs_ac(crossings, output_dir))
    if comparison:
        paths.append(_p_ads_panel(comparison, "GO", output_dir))
        paths.append(_p_ads_panel(comparison, "AC", output_dir))
        paths.append(_p_ads_overlay(comparison, output_dir))

    return paths
