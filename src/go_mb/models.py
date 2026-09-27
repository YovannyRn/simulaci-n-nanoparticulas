"""Referencias de Langmuir y de pseudo-segundo orden. Fuera del contacto.

Estas fórmulas describen un equilibrio (Langmuir) y una curva en minutos
de laboratorio (PSO). El motor no las consulta para decidir si adsorbe,
ni se detiene al llegar a qe. Cada material usa sus propios parámetros.
"""

from __future__ import annotations

import math
from typing import Any

from go_mb.config import MaterialKind, SimulationConfig


def langmuir_qe(qmax: float, kl: float, ce: float) -> float:
    return qmax * kl * ce / (1.0 + kl * ce)


def mass_balance_qe(c0: float, ce: float, volume_l: float, m_g: float) -> float:
    return (c0 - ce) * volume_l / m_g


def langmuir_equilibrium(config: SimulationConfig) -> dict[str, float]:
    """Resuelve Ce y qe combinando Langmuir y balance de masa.

    qe = qmax KL Ce / (1 + KL Ce) = (Co − Ce) V / m
    """
    qmax = config.qmax_mg_g
    kl = config.kl_l_mg
    c0 = config.c0_mg_l
    v = config.volume_l
    m = config.m_go_g
    # a Ce^2 + b Ce + c = 0 con a = KL V, etc.
    # (c0 - Ce) V / m = qmax kl Ce / (1 + kl Ce)
    # (c0 - Ce) (1 + kl Ce) V = m qmax kl Ce
    v_over_m = v / m
    aa = kl * v_over_m
    bb = v_over_m * (1.0 - kl * c0) + qmax * kl
    cc = -c0 * v_over_m
    disc = bb * bb - 4.0 * aa * cc
    if disc < 0:
        raise ValueError("El equilibrio Langmuir no tiene solución real")
    ce = (-bb + math.sqrt(disc)) / (2.0 * aa)
    if ce <= 0:
        ce = (-bb - math.sqrt(disc)) / (2.0 * aa)
    qe = mass_balance_qe(c0, ce, v, m)
    qe_lang = langmuir_qe(qmax, kl, ce)
    return {
        "ce_mg_l": ce,
        "qe_mg_g": qe,
        "qe_langmuir_check_mg_g": qe_lang,
        "m_adsorbed_eq_mg": qe * m,
        "m_free_eq_mg": ce * v,
        "percent_removal": (qe * m / config.m_mb_mg) * 100.0,
        "percent_qmax": (qe / qmax) * 100.0,
    }


def pso_qt(k2: float, qe: float, t_min: float) -> float:
    """qt = k2 qe² t / (1 + k2 qe t)."""
    num = k2 * (qe ** 2) * t_min
    den = 1.0 + k2 * qe * t_min
    return num / den


def pso_time_for_fraction(k2: float, qe: float, fraction: float) -> float | None:
    """t = f / (k2 qe (1 − f)) para 0 < f < 1."""
    if fraction <= 0:
        return 0.0
    if fraction >= 1:
        return None
    beta = k2 * qe
    if beta <= 0:
        return None
    return fraction / (beta * (1.0 - fraction))


def reference_bundle(config: SimulationConfig) -> dict[str, Any]:
    eq = langmuir_equilibrium(config)
    bundle: dict[str, Any] = {
        "langmuir": eq,
        "material": config.material.value,
        "use": (
            "Referencia macroscópica. El motor NO detiene ni sesga la adsorción "
            "para alcanzar qe."
        ),
    }
    if config.material == MaterialKind.AC:
        bundle["wiam_documented"] = {
            "ce_mg_l": config.wiam_ce_mg_l,
            "qe_mg_g": config.wiam_qe_mg_g,
            "total_capacity_mg": config.wiam_total_capacity_mg,
            "equilibrium_adsorption_mg": config.wiam_eq_adsorption_mg,
            "note": (
                "Valores transcritos de Wiam para comparación descriptiva. "
                "No calibran el motor ni fijan el resultado de la simulación."
            ),
        }
        bundle["langmuir_vs_wiam"] = {
            "delta_qe_mg_g": eq["qe_mg_g"] - (config.wiam_qe_mg_g or 0.0),
            "delta_ce_mg_l": eq["ce_mg_l"] - (config.wiam_ce_mg_l or 0.0),
            "delta_m_eq_mg": eq["m_adsorbed_eq_mg"] - (config.wiam_eq_adsorption_mg or 0.0),
        }
        from go_mb.pso_reference import AC_PSO, PSO_FORMULA

        bundle["pso"] = {
            "qe_pso_mg_g": AC_PSO.qe_pso_mg_g,
            "k2_g_mg_min": AC_PSO.k2_g_mg_min,
            "formula_qt": PSO_FORMULA,
            "note": (
                "Referencia cinética PSO AC (Wiam confirmado). "
                "No calibra el motor ni se mezcla con parámetros GO."
            ),
        }
        return bundle

    example_t = 10.0
    qt10 = pso_qt(config.k2_example_g_mg_min, config.qe_pso_mg_g, example_t)
    bundle["pso"] = {
        "qe_pso_mg_g": config.qe_pso_mg_g,
        "qe_exp_article2_mg_g": config.qe_exp_article2_mg_g,
        "k2_example_g_mg_min": config.k2_example_g_mg_min,
        "k2_table_g_mg_min": config.k2_table_g_mg_min,
        "k2_used_for_reference_curve": config.k2_example_g_mg_min,
        "k2_note": (
            "PENDIENTE de unificación: el ejemplo a 10 min cierra con 0.0002; "
            "la tabla transcribe 0.001. La curva de referencia usa 0.0002."
        ),
        "qt_10min_mg_g": qt10,
        "mass_10min_mg": qt10 * config.m_go_g,
        "objects_10min": (qt10 * config.m_go_g) / config.peso_mb_mg,
        "conditions_note": "PSO de [2] es pH 7 y 20 °C; Langmuir de [1] es pH 6 y 25 °C.",
    }
    return bundle
