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
    ads_label = cfg.get("adsorbent_symbol") or cfg.get("material", "GO")
    ax.scatter(go[:, 0], go[:, 1], s=go_s ** 2, c="black", marker="s", label=ads_label, zorder=2)
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


def _series_from_study_record(record: dict[str, Any]) -> list[dict[str, float | int]] | None:
    paths = record.get("paths") or {}
    json_path = paths.get("json")
    if not json_path:
        return None
    from go_mb.io import load_run

    loaded = load_run(json_path)
    return loaded.get("series")


def plot_sensitivity_study(study: dict[str, Any], output_dir: str | Path) -> list[str]:
    """Gráficas de sensibilidad. Solo lectura; pasos ≠ minutos; sin objetivo Langmuir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    kind = study["study"]["kind"]
    out_paths: list[str] = []

    if kind == "sigma_sweep":
        out_paths.append(_plot_final_vs_sigma(study, output_dir))
        out_paths.append(_plot_qt_vs_sigma(study, output_dir))
        out_paths.append(_plot_evolution_by_sigma(study, output_dir))
        if study["analysis"].get("seed_variability"):
            out_paths.append(_plot_seed_variability(study, output_dir))
    elif kind == "steps_sweep":
        out_paths.append(_plot_final_vs_steps(study, output_dir))
        out_paths.append(_plot_evolution_by_steps(study, output_dir))
        out_paths.append(_plot_contacts_vs_steps(study, output_dir))
        if study["analysis"].get("seed_variability"):
            out_paths.append(_plot_seed_variability(study, output_dir))
    elif kind == "sigma_steps_grid":
        out_paths.append(_plot_grid_heatmap(study, output_dir, "n_adsorbed"))
        out_paths.append(_plot_grid_heatmap(study, output_dir, "qfinal_mg_g"))
        if study["analysis"].get("seed_variability"):
            out_paths.append(_plot_seed_variability(study, output_dir))
    return [p for p in out_paths if p]


def _plot_qt_vs_sigma(study: dict[str, Any], output_dir: Path) -> str:
    rows = study["analysis"]["rows"]
    sigmas = sorted({r["sigma_px"] for r in rows})
    means = []
    for s in sigmas:
        vals = [r["qfinal_mg_g"] for r in rows if r["sigma_px"] == s]
        means.append(sum(vals) / len(vals))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(sigmas, means, "o-", color="tab:green")
    ax.set_xlabel("σ (px/paso, parámetro de ejecución)")
    ax.set_ylabel("qt final (mg/g)")
    ax.set_title("qt vs σ (referencia Langmuir no es objetivo)")
    path = output_dir / "sensitivity_qt_vs_sigma.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return str(path)


def _plot_seed_variability(study: dict[str, Any], output_dir: Path) -> str:
    sv = study["analysis"]["seed_variability"]
    if not sv:
        return ""
    fig, ax = plt.subplots(figsize=(max(7, len(sv) * 0.8), 4))
    labels = [f"σ={e['sigma_px']:g}\nP={e['n_steps']}" for e in sv]
    spreads = [e["n_adsorbed_spread"] for e in sv]
    means = [
        sum(e["n_adsorbed_values"]) / len(e["n_adsorbed_values"]) for e in sv
    ]
    x = range(len(sv))
    ax.bar(x, means, color="tab:blue", alpha=0.7, label="Nads medio")
    ax.set_xticks(list(x), labels, fontsize=8)
    ax.set_ylabel("Nads")
    ax.set_title("Variabilidad entre seeds (spread anotado)")
    for i, (m, sp) in enumerate(zip(means, spreads)):
        ax.text(i, m, f"±{sp}", ha="center", va="bottom", fontsize=8)
    path = output_dir / "sensitivity_seed_variability.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return str(path)


def _plot_final_vs_sigma(study: dict[str, Any], output_dir: Path) -> str:
    rows = study["analysis"]["rows"]
    sigmas = sorted({r["sigma_px"] for r in rows})
    means = []
    for s in sigmas:
        vals = [r["percent_adsorbed"] for r in rows if r["sigma_px"] == s]
        means.append(sum(vals) / len(vals))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(sigmas, means, "o-", color="tab:blue")
    ax.set_xlabel("σ (px/paso, parámetro de ejecución)")
    ax.set_ylabel("% adsorbido final")
    ax.set_title("Sensibilidad a σ (no validación experimental)")
    path = output_dir / "sensitivity_final_percent_vs_sigma.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return str(path)


def _plot_final_vs_steps(study: dict[str, Any], output_dir: Path) -> str:
    rows = study["analysis"]["rows"]
    steps = sorted({r["n_steps"] for r in rows})
    means = []
    for st in steps:
        vals = [r["percent_adsorbed"] for r in rows if r["n_steps"] == st]
        means.append(sum(vals) / len(vals))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(steps, means, "s-", color="tab:green")
    ax.set_xlabel("pasos (no minutos)")
    ax.set_ylabel("% adsorbido final")
    ax.set_title("Sensibilidad al número de pasos")
    path = output_dir / "sensitivity_final_percent_vs_steps.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return str(path)


def _plot_contacts_vs_steps(study: dict[str, Any], output_dir: Path) -> str:
    rows = study["analysis"]["rows"]
    steps = sorted({r["n_steps"] for r in rows})
    means = []
    for st in steps:
        vals = [r["n_contacts"] for r in rows if r["n_steps"] == st]
        means.append(sum(vals) / len(vals))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(steps, means, "^-", color="tab:orange")
    ax.set_xlabel("pasos")
    ax.set_ylabel("contactos acumulados")
    ax.set_title("Contactos vs pasos (sensibilidad)")
    path = output_dir / "sensitivity_contacts_vs_steps.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return str(path)


def _plot_evolution_by_sigma(study: dict[str, Any], output_dir: Path) -> str:
    fig, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    for rec in study["runs"]:
        series = _series_from_study_record(rec)
        if not series:
            continue
        sigma = rec["execution_parameters"]["sigma_px"]["value"]
        steps = [row["step"] for row in series]
        pct = [row["percent_adsorbed"] for row in series]
        qt = [row["qt_mg_g"] for row in series]
        label = f"σ={sigma:g}"
        axes[0].plot(steps, pct, label=label)
        axes[1].plot(steps, qt, label=label)
    axes[0].set_ylabel("% adsorbido")
    axes[1].set_ylabel("qt (mg/g)")
    axes[1].set_xlabel("paso")
    axes[0].set_title("Evolución temporal por σ")
    axes[0].legend(fontsize=8)
    axes[1].legend(fontsize=8)
    path = output_dir / "sensitivity_evolution_by_sigma.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return str(path)


def _plot_evolution_by_steps(study: dict[str, Any], output_dir: Path) -> str:
    fig, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    for rec in study["runs"]:
        series = _series_from_study_record(rec)
        if not series:
            continue
        n_steps = rec["execution_parameters"]["n_steps"]["value"]
        steps = [row["step"] for row in series]
        pct = [row["percent_adsorbed"] for row in series]
        qt = [row["qt_mg_g"] for row in series]
        label = f"P={n_steps}"
        axes[0].plot(steps, pct, label=label)
        axes[1].plot(steps, qt, label=label)
    axes[0].set_ylabel("% adsorbido")
    axes[1].set_ylabel("qt (mg/g)")
    axes[1].set_xlabel("paso")
    axes[0].set_title("Evolución temporal por número de pasos")
    axes[0].legend(fontsize=8)
    axes[1].legend(fontsize=8)
    path = output_dir / "sensitivity_evolution_by_steps.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return str(path)


def _plot_grid_heatmap(study: dict[str, Any], output_dir: Path, metric: str) -> str:
    rows = study["analysis"]["rows"]
    sigmas = sorted({r["sigma_px"] for r in rows})
    steps_list = sorted({r["n_steps"] for r in rows})
    grid = np.full((len(sigmas), len(steps_list)), np.nan)
    for i, sigma in enumerate(sigmas):
        for j, st in enumerate(steps_list):
            if metric == "n_adsorbed":
                vals = [r["n_adsorbed"] for r in rows if r["sigma_px"] == sigma and r["n_steps"] == st]
            else:
                vals = [r["qfinal_mg_g"] for r in rows if r["sigma_px"] == sigma and r["n_steps"] == st]
            if vals:
                grid[i, j] = sum(vals) / len(vals)
    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(grid, aspect="auto", origin="lower", cmap="viridis")
    ax.set_xticks(range(len(steps_list)), labels=[str(s) for s in steps_list])
    ax.set_yticks(range(len(sigmas)), labels=[f"{s:g}" for s in sigmas])
    ax.set_xlabel("pasos")
    ax.set_ylabel("σ (px/paso)")
    ax.set_title(f"Mapa σ×pasos — {metric} (media sobre seeds si aplica)")
    fig.colorbar(im, ax=ax)
    path = output_dir / f"sensitivity_grid_{metric}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return str(path)
