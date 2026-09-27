"""Media, desviación, coeficiente de variación e intervalo de la media.

Resume un conjunto de semillas. No es un error de laboratorio ni una
regla de adsorción. La desviación usa el convenio habitual de dividir
entre n−1 cuando hay más de un valor.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

# t crítico bilateral 95 %. Método estadístico; el PDF no da el valor.
_T95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    9: 2.262, 19: 2.093, 29: 2.045, 39: 2.023, 59: 2.000,
    119: 1.980,
}


def t_crit_95(n: int) -> float:
    if n < 2:
        raise ValueError("N debe ser ≥ 2 para IC")
    df = n - 1
    if df in _T95:
        return _T95[df]
    # Interpolación simple entre nodos conocidos.
    keys = sorted(_T95)
    if df < keys[0]:
        return _T95[keys[0]]
    if df > keys[-1]:
        return 1.96
    for a, b in zip(keys, keys[1:]):
        if a <= df <= b:
            w = (df - a) / (b - a)
            return _T95[a] * (1 - w) + _T95[b] * w
    return 1.96


def mean_std(values: list[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        raise ValueError("lista vacía")
    mean = float(arr.mean())
    std = float(arr.std(ddof=1)) if arr.size > 1 else 0.0
    return mean, std


def confidence_interval_95(values: list[float]) -> dict[str, float]:
    n = len(values)
    mean, std = mean_std(values)
    t = t_crit_95(n)
    half = t * std / math.sqrt(n)
    return {
        "n": float(n),
        "mean": mean,
        "std": std,
        "t_crit": t,
        "ci_low": mean - half,
        "ci_high": mean + half,
    }


_SUMMARY_KEYS = [
    "n_adsorbed",
    "n_free",
    "percent_adsorbed",
    "m_adsorbed_mg",
    "m_free_mg",
    "c_pdf_mg_l",
    "c_remaining_mg_l",
    "qfinal_mg_g",
    "percent_qmax",
    "n_contacts",
    "mean_speed_q_per_step",
]


def summarize_campaign(runs: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(runs)
    stats: dict[str, Any] = {
        "n_rep": n,
        "n_rep_status": "PENDIENTE (PDF: FAQ 40 vs estadísticos 30)",
        "seeds": [run["run"]["seed"] for run in runs],
        "variables": {},
    }
    for key in _SUMMARY_KEYS:
        vals = [float(run["summary"][key]) for run in runs]
        mean, std = mean_std(vals)
        entry: dict[str, Any] = {"mean": mean, "std": std, "values": vals}
        if n >= 2:
            entry["ci95"] = confidence_interval_95(vals)
        stats["variables"][key] = entry
    return stats
