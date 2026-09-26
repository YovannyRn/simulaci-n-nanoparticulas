"""Figuras sensibilidad P_ads (separado del motor)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _flat_agg(aggregated: list[dict[str, Any]], material: str, sigma: float) -> list[dict[str, Any]]:
    return sorted(
        [
            a
            for a in aggregated
            if a["material"] == material and abs(a["sigma_px"] - sigma) < 1e-9
        ],
        key=lambda x: x["p_ads"],
    )


def plot_p_ads_sensitivity(
    aggregated: list[dict[str, Any]],
    records: list[dict[str, Any]],
    output_dir: Path,
) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    p_vals = sorted({a["p_ads"] for a in aggregated})

    for material in ("GO", "AC"):
        for sigma in (1.0, 1.5):
            pts = _flat_agg(aggregated, material, sigma)
            if not pts:
                continue
            xs = [p["p_ads"] for p in pts]

            for metric, ylabel, fname in (
                ("n_adsorbed", "Nads final", "nads"),
                ("qfinal_mg_g", "qt (mg/g)", "qt"),
                ("n_contacts", "Contactos (pares)", "contacts"),
                ("contact_to_adsorption_efficiency", "Adsorciones/contactos", "efficiency"),
            ):
                means = [p[metric]["mean"] for p in pts]
                stds = [p[metric]["std"] or 0.0 for p in pts]
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.errorbar(xs, means, yerr=stds, fmt="o-", capsize=3)
                ax.set_xlabel("P_ads (computacional, no físico)")
                ax.set_ylabel(ylabel)
                ax.set_title(f"{material} σ={sigma} — {ylabel} vs P_ads")
                p = output_dir / f"{fname}_vs_pads_{material.lower()}_sigma_{sigma:g}.png"
                fig.savefig(p, dpi=150, bbox_inches="tight")
                plt.close(fig)
                paths.append(str(p))

            # variabilidad seeds (spread Nads)
            fig, ax = plt.subplots(figsize=(7, 4))
            for p in p_vals:
                sub = [
                    r
                    for r in records
                    if r["material"] == material
                    and abs(r["sigma_px"] - sigma) < 1e-9
                    and abs(float(r["p_ads_effective"]) - p) < 1e-9
                ]
                nads = [r["n_adsorbed"] for r in sub]
                ax.scatter([p] * len(nads), nads, alpha=0.7, s=25)
            ax.set_xlabel("P_ads")
            ax.set_ylabel("Nads por seed")
            ax.set_title(f"{material} σ={sigma} — variabilidad entre seeds")
            p = output_dir / f"nads_seed_spread_{material.lower()}_sigma_{sigma:g}.png"
            fig.savefig(p, dpi=150, bbox_inches="tight")
            plt.close(fig)
            paths.append(str(p))

    # GO vs AC overlay Nads mean
    for sigma in (1.0, 1.5):
        fig, ax = plt.subplots(figsize=(7, 4))
        for material, color in (("GO", "tab:blue"), ("AC", "tab:orange")):
            pts = _flat_agg(aggregated, material, sigma)
            ax.plot(
                [p["p_ads"] for p in pts],
                [p["n_adsorbed"]["mean"] for p in pts],
                "o-",
                color=color,
                label=material,
            )
        ax.set_xlabel("P_ads (computacional)")
        ax.set_ylabel("Nads medio (5 seeds)")
        ax.set_title(f"GO vs AC — Nads vs P_ads (σ={sigma})")
        ax.legend()
        p = output_dir / f"go_vs_ac_nads_sigma_{sigma:g}.png"
        fig.savefig(p, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(str(p))

    return paths
