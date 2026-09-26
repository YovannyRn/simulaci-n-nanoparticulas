"""Parámetros PSO y Langmuir confirmados (referencia externa; no calibra el motor)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from go_mb.models import pso_qt, pso_time_for_fraction

MaterialRef = Literal["GO", "AC"]

FINAL_TEMPORAL_CLASSIFICATION = (
    "temporal_calibration_go_ac_with_bibliographic_sticking_reference"
)
PADS_055_CLASSIFICATION = (
    "p_ads_055_bibliographic_reference_sensitivity_not_physical_validation"
)

PSO_FORMULA = "qt(t) = (k2 * qe^2 * t) / (1 + k2 * qe * t)"
PSO_INVERSE = "t(f) = f / (k2 * qe * (1 - f))  for 0 < f < 1"

EXPERIMENTAL_CONDITIONS = {
    "temperature_c": 25.0,
    "ph": 6.0,
    "m_mb_mg": 4.0,
    "m_adsorbent_mg": 10.0,
    "volume_ml": 40.0,
    "c0_mg_l": 100.0,
    "c0_note": "100 mg/L confirmado por Wiam; 100 mg/g fue error de escritura.",
}


@dataclass(frozen=True)
class LangmuirReference:
    qmax_mg_g: float
    kl_l_mg: float
    qe_mg_g: float
    ce_mg_l: float


@dataclass(frozen=True)
class PsoReference:
    qe_pso_mg_g: float
    k2_g_mg_min: float

    def qt(self, t_min: float) -> float:
        return pso_qt(self.k2_g_mg_min, self.qe_pso_mg_g, t_min)

    def t_for_fraction(self, fraction: float) -> float | None:
        return pso_time_for_fraction(self.k2_g_mg_min, self.qe_pso_mg_g, fraction)


GO_LANGMUIR = LangmuirReference(
    qmax_mg_g=764.7,
    kl_l_mg=0.206,
    qe_mg_g=380.7,
    ce_mg_l=4.81,
)
AC_LANGMUIR = LangmuirReference(
    qmax_mg_g=412.2,
    kl_l_mg=0.088,
    qe_mg_g=290.9,
    ce_mg_l=27.3,
)

GO_PSO = PsoReference(qe_pso_mg_g=384.6, k2_g_mg_min=0.0002)
AC_PSO = PsoReference(qe_pso_mg_g=100.4, k2_g_mg_min=0.00910)

# Compat temporal_calibration (GO)
PSO_QE_MG_G = GO_PSO.qe_pso_mg_g
PSO_K2_G_MG_MIN = GO_PSO.k2_g_mg_min

BIBLIOGRAPHIC_STICKING_S_STAR = {
    "symbol": "S*",
    "value": 0.55,
    "classification": (
        "bibliographic_sticking_probability_reference_for_a_related_AC_MB_experimental_system"
    ),
    "citation": (
        "Sha'Ato, R. (2021). Isotherms, Kinetics and Thermodynamics of Methylene Blue "
        "Adsorption on Active Carbon from Polyfurfuryl Alcohol. "
        "Nigerian Journal of Chemical Research, 25(1)."
    ),
    "not_equal_to_p_ads": True,
    "not_automatic_substitution_for_p_ads": True,
    "not_universal_physical_probability": True,
    "context_notes": [
        "Procede de un sistema experimental concreto (AC–MB en ese estudio).",
        "No necesariamente corresponde al mismo AC de este proyecto.",
        "No es equivalente a la regla computacional P_ads del modelo.",
        "Uso: referencia contextual y sensibilidad P_ads=0.55 únicamente.",
    ],
}


def pso_for_material(material: MaterialRef) -> PsoReference:
    if material == "GO":
        return GO_PSO
    return AC_PSO


def langmuir_for_material(material: MaterialRef) -> LangmuirReference:
    if material == "GO":
        return GO_LANGMUIR
    return AC_LANGMUIR


def pso_fraction_table(material: MaterialRef, fractions: list[float]) -> list[dict[str, Any]]:
    pso = pso_for_material(material)
    rows: list[dict[str, Any]] = []
    for f in fractions:
        t_pso = pso.t_for_fraction(f)
        rows.append(
            {
                "material": material,
                "fraction_of_pso_qe": f,
                "q_target_mg_g": f * pso.qe_pso_mg_g,
                "t_pso_min": t_pso,
                "qe_pso_mg_g": pso.qe_pso_mg_g,
                "k2_g_mg_min": pso.k2_g_mg_min,
            }
        )
    return rows


def pso_curve_samples(
    material: MaterialRef,
    *,
    t_max_min: float = 120.0,
    n_points: int = 241,
) -> list[dict[str, Any]]:
    pso = pso_for_material(material)
    rows: list[dict[str, Any]] = []
    for i in range(n_points):
        t = t_max_min * i / max(n_points - 1, 1)
        rows.append(
            {
                "material": material,
                "t_min": t,
                "qt_mg_g": pso.qt(t),
                "qe_pso_mg_g": pso.qe_pso_mg_g,
                "k2_g_mg_min": pso.k2_g_mg_min,
            }
        )
    return rows
