"""Figuras campaña final GO vs AC."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from go_mb.pso_reference import AC_LANGMUIR, AC_PSO, GO_LANGMUIR, GO_PSO


def _save(fig, path: Path, description: str, catalog: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    catalog.append({"filename": path.name, "description": description, "path": str(path)})


def plot_final_campaign(
    records: list[dict[str, Any]],
    run_paths: list[tuple[str, Path]],
    output_dir: Path,
) -> list[dict[str, str]]:
    catalog: list[dict[str, str]] = []
    go = sorted([r for r in records if r["material"] == "GO"], key=lambda x: x["seed"])
    ac = sorted([r for r in records if r["material"] == "AC"], key=lambda x: x["seed"])
    seeds = [r["seed"] for r in go]

    # 1 Nads por seed
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(seeds, [r["n_adsorbed"] for r in go], "o-", label="GO", color="tab:blue")
    ax.plot(seeds, [r["n_adsorbed"] for r in ac], "s-", label="AC", color="tab:orange")
    ax.set_xlabel("seed")
    ax.set_ylabel("Nads final")
    ax.set_title("Nads por seed — GO vs AC")
    ax.legend()
    _save(fig, output_dir / "01_nads_by_seed_go_vs_ac.png", "Nads final por seed (GO y AC).", catalog)

    # 2 qt por seed
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(seeds, [r["qfinal_mg_g"] for r in go], "o-", label="GO")
    ax.plot(seeds, [r["qfinal_mg_g"] for r in ac], "s-", label="AC")
    ax.set_xlabel("seed")
    ax.set_ylabel("qt (mg/g)")
    ax.set_title("qt final por seed")
    ax.legend()
    _save(fig, output_dir / "02_qt_by_seed_go_vs_ac.png", "qt final (mg/g) por seed.", catalog)

    # 3 % adsorbido
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(seeds, [r["percent_adsorbed"] for r in go], "o-", label="GO")
    ax.plot(seeds, [r["percent_adsorbed"] for r in ac], "s-", label="AC")
    ax.set_xlabel("seed")
    ax.set_ylabel("% MB adsorbido")
    ax.set_title("Porcentaje adsorbido por seed")
    ax.legend()
    _save(fig, output_dir / "03_percent_adsorbed_by_seed.png", "% adsorbido por seed.", catalog)

    # 4-5 distribuciones
    for metric, ylab, fname, desc in (
        ("n_adsorbed", "Nads", "04_nads_distribution.png", "Histograma Nads GO vs AC."),
        ("qfinal_mg_g", "qt (mg/g)", "05_qt_distribution.png", "Histograma qt GO vs AC."),
    ):
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist([r[metric] for r in go], bins=12, alpha=0.6, label="GO", color="tab:blue")
        ax.hist([r[metric] for r in ac], bins=12, alpha=0.6, label="AC", color="tab:orange")
        ax.set_xlabel(ylab)
        ax.set_ylabel("frecuencia")
        ax.legend()
        _save(fig, output_dir / fname, desc, catalog)

    # 6 contactos
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(seeds, [r["n_contacts"] for r in go], "o-", label="GO")
    ax.plot(seeds, [r["n_contacts"] for r in ac], "s-", label="AC")
    ax.set_xlabel("seed")
    ax.set_ylabel("contactos")
    ax.set_title("Contactos acumulados por seed")
    ax.legend()
    _save(fig, output_dir / "06_contacts_by_seed.png", "Contactos por seed.", catalog)

    # 7 eficiencia
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(
        seeds,
        [r["contact_to_adsorption_efficiency"] or 0 for r in go],
        "o-",
        label="GO",
    )
    ax.plot(
        seeds,
        [r["contact_to_adsorption_efficiency"] or 0 for r in ac],
        "s-",
        label="AC",
    )
    ax.set_xlabel("seed")
    ax.set_ylabel("adsorciones / contactos")
    ax.set_title("Eficiencia contacto→adsorción")
    ax.legend()
    _save(fig, output_dir / "07_contact_to_adsorption_efficiency.png", "Eficiencia por seed.", catalog)

    # 8-9 evolución qt vs steps
    from go_mb.final_campaign import load_campaign_series

    series_by_mat = load_campaign_series(run_paths)
    for material, fname, num in (("GO", "08_qt_evolution_go_vs_steps.png", "08"), ("AC", "09_qt_evolution_ac_vs_steps.png", "09")):
        fig, ax = plt.subplots(figsize=(8, 4))
        for seed, series in series_by_mat[material]:
            steps = [int(r["step"]) for r in series]
            qt = [float(r["qt_mg_g"]) for r in series]
            ax.plot(steps, qt, alpha=0.25, lw=0.6, color="tab:blue" if material == "GO" else "tab:orange")
        ax.set_xlabel("steps (simulación)")
        ax.set_ylabel("qt (mg/g)")
        ax.set_title(f"{material} — evolución qt vs steps (40 seeds)")
        _save(
            fig,
            output_dir / fname,
            f"Evolución qt vs steps — {material}; eje temporal en pasos, no minutos.",
            catalog,
        )

    # 10-11 Langmuir referencia
    for material, recs, qe, fname in (
        ("GO", go, GO_LANGMUIR.qe_mg_g, "10_qt_vs_langmuir_go.png"),
        ("AC", ac, AC_LANGMUIR.qe_mg_g, "11_qt_vs_langmuir_ac.png"),
    ):
        fig, ax = plt.subplots(figsize=(7, 4))
        qts = [r["qfinal_mg_g"] for r in recs]
        ax.scatter(range(len(qts)), sorted(qts), alpha=0.7)
        ax.axhline(qe, color="red", ls="--", label=f"qe Langmuir ref. = {qe} mg/g")
        ax.set_xlabel("índice ordenado (seed)")
        ax.set_ylabel("qt final (mg/g)")
        ax.set_title(f"{material} — qt vs referencia Langmuir (no objetivo)")
        ax.legend()
        _save(fig, output_dir / fname, f"qt simulado vs qe Langmuir {material}.", catalog)

    # 12-13 PSO referencia (minutos)
    for pso, mat, fname in (
        (GO_PSO, "GO", "12_pso_reference_go_minutes.png"),
        (AC_PSO, "AC", "13_pso_reference_ac_minutes.png"),
    ):
        t_vals = np.linspace(0, 120, 241)
        qt_vals = [pso.qt(float(t)) for t in t_vals]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(t_vals, qt_vals, color="tab:purple")
        ax.set_xlabel("t (min) — referencia PSO")
        ax.set_ylabel("qt (mg/g)")
        ax.set_title(f"Referencia PSO {mat} (no convierte steps a minutos)")
        _save(fig, output_dir / fname, f"Curva PSO {mat} en minutos (referencia externa).", catalog)

    return catalog
