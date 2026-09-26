"""Parámetros del experimento GO–MB con procedencia explícita.

Ningún valor PENDIENTE se presenta como dato de literatura.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class OriginStatus(str, Enum):
    DOCUMENTADO = "DOCUMENTADO"
    CALCULADO = "CALCULADO"
    DECISION_COMPUTACIONAL = "DECISIÓN COMPUTACIONAL"
    HIPOTESIS = "HIPÓTESIS"
    PENDIENTE = "PENDIENTE"


class MaterialKind(str, Enum):
    """Material adsorbente del recinto (Simulación 1 GO, Simulación 2 AC)."""

    GO = "GO"
    AC = "AC"


# Geometría visual confirmada por Wiam (2026-09); círculo inscrito r = lado/2.
WIAM_MB_SIDE_PX = 1
WIAM_GO_SIDE_PX = 7
WIAM_AC_SIDE_PX = 2
WIAM_PX_SIDE_UM = 77.4
WIAM_PX_AREA_UM2 = 5990.76
GEOMETRY_LEGACY_NOTE = (
    "Campañas en data/sensitivity/homogeneous_temporal/ usaron MB 5×5 y adsorbente "
    "7×7 para GO y AC (geometría anterior)."
)

HOMOGENEOUS_LEGACY_DIR = "data/sensitivity/homogeneous_temporal"
HOMOGENEOUS_WIAM_DIR = "data/sensitivity/homogeneous_temporal_wiam_geometry"


def geometry_snapshot(config: SimulationConfig) -> dict[str, Any]:
    """Metadatos geométricos de una corrida (motor actual)."""
    return {
        "geometry_era": "wiam_geometry",
        "mb_side_px": config.mb_size_px,
        "adsorbent_side_px": config.go_size_px,
        "adsorbent_symbol": config.adsorbent_symbol,
        "r_mb_px": config.r_mb_px,
        "r_adsorbent_px": config.r_go_px,
        "contact_threshold_px": config.r_mb_px + config.r_go_px,
        "adsorbent_movable": config.adsorbent_movable,
    }


@dataclass(frozen=True)
class Parameter:
    name: str
    symbol: str
    value: Any
    unit: str
    origin: str
    calculation: str
    status: OriginStatus
    function: str = ""


@dataclass(frozen=True)
class SimulationConfig:
    """Parámetros de dominio GO–MB o AC–MB (misma geometría de recinto y MB).

    Internamente las partículas adsorbentes usan los campos ``n_go`` / ``go_*``
    por compatibilidad con el motor; con ``material=AC`` representan unidades AC.
    """

    material: MaterialKind = MaterialKind.GO
    adsorbent_movable: bool = True
    temperature_c: float = 25.0
    ph: float = 6.0
    volume_l: float = 0.04
    m_go_g: float = 0.01
    m_mb_mg: float = 4.0
    qmax_mg_g: float = 764.7
    kl_l_mg: float = 0.206
    qe_pso_mg_g: float = 384.6
    qe_exp_article2_mg_g: float = 385.76
    k2_example_g_mg_min: float = 0.0002
    k2_table_g_mg_min: float = 0.001
    n_mb: int = 200
    n_go: int = 100
    domain_px: int = 442
    vessel_side_cm: float = 3.42
    px_side_um: float = WIAM_PX_SIDE_UM
    mb_size_px: int = WIAM_MB_SIDE_PX
    go_size_px: int = WIAM_GO_SIDE_PX
    go_lateral_um: float = 1.5
    # Referencia documentada AC (Wiam); no fuerza el motor.
    wiam_ce_mg_l: float | None = None
    wiam_qe_mg_g: float | None = None
    wiam_total_capacity_mg: float | None = None
    wiam_eq_adsorption_mg: float | None = None

    @property
    def adsorbent_symbol(self) -> str:
        return "GO" if self.material == MaterialKind.GO else "AC"

    @property
    def m_adsorbent_g(self) -> float:
        return self.m_go_g

    @property
    def n_adsorbent(self) -> int:
        return self.n_go

    @property
    def c_go_mg_l(self) -> float:
        return (self.m_go_g * 1000.0) / self.volume_l

    @property
    def c0_mg_l(self) -> float:
        return self.m_mb_mg / self.volume_l

    @property
    def peso_mb_mg(self) -> float:
        return self.m_mb_mg / self.n_mb

    @property
    def peso_go_mg(self) -> float:
        return (self.m_go_g * 1000.0) / self.n_go

    @property
    def cap_go_mg(self) -> float:
        return self.qmax_mg_g * (self.peso_go_mg / 1000.0)

    @property
    def n_pixels(self) -> int:
        return self.domain_px * self.domain_px

    @property
    def pixel_area_um2(self) -> float:
        return self.px_side_um ** 2

    @property
    def vessel_area_cm2(self) -> float:
        return self.vessel_side_cm ** 2

    @property
    def mb_area_px2(self) -> int:
        return self.n_mb * self.mb_size_px * self.mb_size_px

    @property
    def go_area_px2(self) -> int:
        return self.n_go * self.go_size_px * self.go_size_px

    @property
    def r_mb_px(self) -> float:
        """Círculo inscrito. DECISIÓN COMPUTACIONAL / PENDIENTE de confirmación."""
        return self.mb_size_px / 2.0

    @property
    def r_go_px(self) -> float:
        """Círculo inscrito. DECISIÓN COMPUTACIONAL / PENDIENTE de confirmación."""
        return self.go_size_px / 2.0

    def parameter_table(self) -> list[Parameter]:
        ads_name = "GO" if self.material == MaterialKind.GO else "AC"
        ads_mass_label = f"Masa {ads_name}"
        rows: list[Parameter] = [
            Parameter(
                "Material",
                "material",
                self.material.value,
                "—",
                "configuración",
                "GO vs AC",
                OriginStatus.DECISION_COMPUTACIONAL,
            ),
            Parameter(
                "Adsorbente móvil",
                "adsorbent_movable",
                self.adsorbent_movable,
                "—",
                "configuración",
                "False en AC (Wiam)",
                OriginStatus.DECISION_COMPUTACIONAL,
            ),
            Parameter("Temperatura", "T", self.temperature_c, "°C", "[1]", "—", OriginStatus.DOCUMENTADO),
            Parameter("pH", "pH", self.ph, "—", "[1]", "—", OriginStatus.DOCUMENTADO),
            Parameter("Volumen", "V", self.volume_l, "L", "[1]", "40 mL", OriginStatus.DOCUMENTADO),
            Parameter(
                ads_mass_label,
                "m",
                self.m_go_g,
                "g",
                "[1]" if self.material == MaterialKind.GO else "Wiam",
                "10 mg",
                OriginStatus.DOCUMENTADO,
            ),
            Parameter("Masa MB inicial", "Mo", self.m_mb_mg, "mg", "[1]", "—", OriginStatus.DOCUMENTADO),
            Parameter(
                f"Concentración {ads_name}",
                f"C_{ads_name}",
                self.c_go_mg_l,
                "mg/L",
                "derivado",
                "10/0.04",
                OriginStatus.CALCULADO,
            ),
            Parameter(
                "Concentración inicial MB",
                "Co",
                self.c0_mg_l,
                "mg/L",
                "derivado / Wiam" if self.material == MaterialKind.AC else "derivado / [1]",
                "4 mg / 0.04 L = 100 mg/L",
                OriginStatus.CALCULADO,
            ),
            Parameter("qmax", "qmax", self.qmax_mg_g, "mg/g", "[1]", "—", OriginStatus.DOCUMENTADO),
            Parameter("KL", "KL", self.kl_l_mg, "L/mg", "[1]", "—", OriginStatus.DOCUMENTADO),
            Parameter("qe PSO [2]", "qe_PSO", self.qe_pso_mg_g, "mg/g", "[2]", "—", OriginStatus.DOCUMENTADO),
            Parameter("k2 ejemplo", "k2_ejemplo", self.k2_example_g_mg_min, "g/(mg·min)", "[2] ejemplo 10 min", "cierra 1.672 mg", OriginStatus.DOCUMENTADO),
            Parameter("k2 tabla transcrita", "k2_tabla", self.k2_table_g_mg_min, "g/(mg·min)", "[2] tabla", "no unificado", OriginStatus.PENDIENTE),
            Parameter("N MB", "N_MB", self.n_mb, "objetos", "modelo", "—", OriginStatus.DECISION_COMPUTACIONAL),
            Parameter(f"N {ads_name}", f"N_{ads_name}", self.n_go, "objetos", "modelo", "100", OriginStatus.DECISION_COMPUTACIONAL),
            Parameter("Masa por MB", "peso_MB", self.peso_mb_mg, "mg", "derivado", "4/200", OriginStatus.CALCULADO),
            Parameter(
                f"Masa por {ads_name}",
                f"peso_{ads_name}",
                self.peso_go_mg,
                "mg",
                "derivado",
                "10/100",
                OriginStatus.CALCULADO,
            ),
            Parameter(
                f"Capacidad por {ads_name}",
                f"cap_{ads_name}",
                self.cap_go_mg,
                "mg MB/unidad",
                "derivado",
                f"{self.qmax_mg_g}×masa_unidad_g",
                OriginStatus.CALCULADO,
            ),
            Parameter("Lado recinto", "L", self.vessel_side_cm, "cm", "modelo 2D de 40 mL", "—", OriginStatus.DOCUMENTADO),
            Parameter("Dominio", "Npx_lado", self.domain_px, "px", "modelo", "442", OriginStatus.DECISION_COMPUTACIONAL),
            Parameter("Píxeles totales", "Npx", self.n_pixels, "px²", "derivado", "442²", OriginStatus.CALCULADO),
            Parameter("Escala lineal", "px", self.px_side_um, "μm/px", "confirmado", "≈3.42 cm/442", OriginStatus.DOCUMENTADO),
            Parameter("Área de píxel", "A_px", self.pixel_area_um2, "μm²", "derivado", "77.4²", OriginStatus.CALCULADO),
            Parameter(
                f"{ads_name} px",
                f"{ads_name}_px",
                self.go_size_px,
                "px",
                "Wiam",
                f"{self.go_size_px}×{self.go_size_px}",
                OriginStatus.DECISION_COMPUTACIONAL,
            ),
            Parameter(
                "MB px",
                "MB_px",
                self.mb_size_px,
                "px",
                "Wiam",
                f"{self.mb_size_px}×{self.mb_size_px}",
                OriginStatus.DECISION_COMPUTACIONAL,
            ),
            Parameter(
                "Área gráfica MB",
                "A_MB",
                self.mb_area_px2,
                "px²",
                "derivado",
                f"{self.n_mb}×{self.mb_size_px}²",
                OriginStatus.CALCULADO,
            ),
            Parameter(
                f"Área gráfica {ads_name}",
                f"A_{ads_name}",
                self.go_area_px2,
                "px²",
                "derivado",
                f"{self.n_go}×{self.go_size_px}²",
                OriginStatus.CALCULADO,
            ),
            Parameter(
                "Radio MB inscrito",
                "rMB",
                self.r_mb_px,
                "px",
                "círculo inscrito",
                f"{self.mb_size_px}×{self.mb_size_px} px → {self.r_mb_px}",
                OriginStatus.DECISION_COMPUTACIONAL,
            ),
            Parameter(
                f"Radio {ads_name} inscrito",
                "rA",
                self.r_go_px,
                "px",
                "círculo inscrito",
                f"{self.go_size_px}/2 → {self.r_go_px}",
                OriginStatus.DECISION_COMPUTACIONAL,
            ),
            Parameter("D / σ browniano", "D", None, "px/paso", "sin valor en el PDF", "inyectar --sigma", OriginStatus.PENDIENTE),
            Parameter("Pasos", "P", None, "pasos", "sin valor en el PDF", "inyectar --steps", OriginStatus.PENDIENTE),
            Parameter("P_ads", "P_ads", None, "—", "no hay literatura", "ver docs/PENDIENTES.md", OriginStatus.PENDIENTE),
            Parameter("Nrep", "Nrep", None, "corridas", "PDF 30 vs 40", "inyectar --n-rep", OriginStatus.PENDIENTE),
        ]
        if self.material == MaterialKind.AC:
            rows.append(
                Parameter(
                    "Nota Co PDF",
                    "Co_PDF_check",
                    "100 mg/L",
                    "mg/L",
                    "balance masa",
                    "4 mg / 40 mL = 100 mg/L (confirmado Wiam). "
                    "100 mg/g fue error de escritura.",
                    OriginStatus.HIPOTESIS,
                )
            )
        if self.material == MaterialKind.AC and self.wiam_qe_mg_g is not None:
            rows.extend(
                [
                    Parameter(
                        "Ce referencia Wiam",
                        "Ce_Wiam",
                        self.wiam_ce_mg_l,
                        "mg/L",
                        "Wiam (documentado)",
                        "≈27.26",
                        OriginStatus.DOCUMENTADO,
                    ),
                    Parameter(
                        "qe referencia Wiam",
                        "qe_Wiam",
                        self.wiam_qe_mg_g,
                        "mg/g",
                        "Wiam (documentado)",
                        "≈290.9",
                        OriginStatus.DOCUMENTADO,
                    ),
                    Parameter(
                        "Capacidad total máx. Wiam",
                        "qmax_total_Wiam",
                        self.wiam_total_capacity_mg,
                        "mg",
                        "Wiam",
                        "4.122",
                        OriginStatus.DOCUMENTADO,
                    ),
                    Parameter(
                        "Adsorción equilibrio ref. Wiam",
                        "m_eq_Wiam",
                        self.wiam_eq_adsorption_mg,
                        "mg",
                        "Wiam",
                        "≈2.909",
                        OriginStatus.DOCUMENTADO,
                    ),
                ]
            )
        return rows

    def to_metadata(self) -> dict[str, Any]:
        table = [
            {
                "name": p.name,
                "symbol": p.symbol,
                "value": p.value,
                "unit": p.unit,
                "origin": p.origin,
                "calculation": p.calculation,
                "status": p.status.value,
            }
            for p in self.parameter_table()
        ]
        data = asdict(self)
        data["material"] = self.material.value
        data["adsorbent_symbol"] = self.adsorbent_symbol
        data["derived"] = {
            "c_go_mg_l": self.c_go_mg_l,
            "c0_mg_l": self.c0_mg_l,
            "peso_mb_mg": self.peso_mb_mg,
            "peso_go_mg": self.peso_go_mg,
            "cap_go_mg": self.cap_go_mg,
            "n_pixels": self.n_pixels,
            "pixel_area_um2": self.pixel_area_um2,
            "vessel_area_cm2": self.vessel_area_cm2,
            "mb_area_px2": self.mb_area_px2,
            "go_area_px2": self.go_area_px2,
            "r_mb_px": self.r_mb_px,
            "r_go_px": self.r_go_px,
        }
        data["parameter_table"] = table
        return data


@dataclass(frozen=True)
class RunSettings:
    """Ajustes de una ejecución. sigma, steps, n_rep y p_ads NO son literatura."""

    seed: int
    sigma_px: float
    n_steps: int
    p_ads: float | None = None
    record_every: int = 1
    avoid_overlap: bool = True
    max_place_attempts: int = 20000

    def metadata(self) -> dict[str, Any]:
        if self.p_ads is None or self.p_ads == 1.0:
            rule = "provisional_P_ads_eq_1_after_contact_and_capacity"
            p_ads_effective = 1.0
        else:
            rule = f"bernoulli_p_ads={self.p_ads}_after_capacity_check"
            p_ads_effective = self.p_ads
        return {
            "seed": self.seed,
            "run_classification": "computational_execution",
            "not_experimental_validation": True,
            "sigma_px": self.sigma_px,
            "sigma_status": OriginStatus.PENDIENTE.value,
            "sigma_role": "injected_execution_parameter",
            "n_steps": self.n_steps,
            "n_steps_status": OriginStatus.PENDIENTE.value,
            "n_steps_role": "injected_execution_parameter",
            "p_ads": self.p_ads,
            "p_ads_effective": p_ads_effective,
            "p_ads_status": OriginStatus.PENDIENTE.value,
            "p_ads_implementation_status": "DECISIÓN COMPUTACIONAL PROVISIONAL",
            "adsorption_rule": rule,
            "adsorption_rule_note": (
                "P_ads de literatura sigue PENDIENTE. p_ads=None (defecto) equivale "
                "a P_ads=1 tras contacto geométrico y capacidad restante ≥ peso_MB. "
                "Eso NO es un dato físico ni bibliográfico y no se calibra a qe."
            ),
            "radii_rule": "inscribed_circle_half_side",
            "radii_status": OriginStatus.DECISION_COMPUTACIONAL.value,
            "bounce_rule": "axis_reflection_then_clamp",
            "bounce_status": OriginStatus.DECISION_COMPUTACIONAL.value,
            "step_order": "move_then_contact_then_adsorb",
            "overlap_avoidance": self.avoid_overlap,
            "placement_status": OriginStatus.DECISION_COMPUTACIONAL.value,
            "result_classification": (
                "computational_execution_not_experimental_validation"
            ),
        }


def default_config() -> SimulationConfig:
    return SimulationConfig()


def ac_config() -> SimulationConfig:
    """Configuración AC–MB según datos Wiam (Simulación 2)."""
    return SimulationConfig(
        material=MaterialKind.AC,
        adsorbent_movable=False,
        m_go_g=0.01,
        m_mb_mg=4.0,
        qmax_mg_g=412.2,
        kl_l_mg=0.088,
        n_mb=200,
        n_go=100,
        domain_px=442,
        mb_size_px=WIAM_MB_SIDE_PX,
        go_size_px=WIAM_AC_SIDE_PX,
        qe_pso_mg_g=100.4,
        k2_example_g_mg_min=0.00910,
        wiam_ce_mg_l=27.3,
        wiam_qe_mg_g=290.9,
        wiam_total_capacity_mg=4.122,
        wiam_eq_adsorption_mg=2.909,
    )
