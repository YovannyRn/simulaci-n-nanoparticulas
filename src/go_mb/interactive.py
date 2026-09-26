"""Visualización interactiva 2D sobre el motor headless.

La capa de vista no altera reglas científicas: solo llama a ``advance_step``.
Matplotlib se importa de forma perezosa al abrir la ventana.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np

from go_mb.config import MaterialKind, RunSettings, SimulationConfig, ac_config
from go_mb.engine import advance_step
from go_mb.metrics import snapshot
from go_mb.state import SimulationState, initialize_state

MaterialChoice = Literal["GO", "AC"]


def config_for_material(material: MaterialChoice) -> SimulationConfig:
    if material == "AC":
        return ac_config()
    return SimulationConfig()


@dataclass
class InteractiveSession:
    """Estado de una sesión visual; métricas provienen del motor."""

    config: SimulationConfig
    settings: RunSettings
    state: SimulationState
    rng: np.random.Generator
    series: list[dict[str, float | int]] = field(default_factory=list)
    paused: bool = False
    finished: bool = False

    @property
    def material_label(self) -> str:
        return self.config.adsorbent_symbol

    def reset(self) -> None:
        self.state, self.rng = initialize_state(self.config, self.settings)
        self.series = []
        self.paused = False
        self.finished = False
        self.series.append(snapshot(self.state, None))

    def step_once(self) -> bool:
        """Avanza un paso. Retorna False si ya se alcanzó n_steps."""
        if self.finished:
            return False
        if self.state.step >= self.settings.n_steps:
            self.finished = True
            return False
        prev_qt = float(self.series[-1]["qt_mg_g"]) if self.series else None
        snap, _ = advance_step(self.state, self.rng, self.settings, prev_qt)
        self.series.append(snap)
        if self.state.step >= self.settings.n_steps:
            self.finished = True
        return True

    def run_to_completion_headless(self) -> dict[str, Any]:
        """Ejecuta todos los pasos restantes sin UI (para tests y paridad)."""
        while self.step_once():
            pass
        return self.metrics_dict()

    def metrics_dict(self) -> dict[str, Any]:
        last = self.series[-1] if self.series else {}
        return {
            "step": int(last.get("step", 0)),
            "n_adsorbed": int(last.get("n_adsorbed", 0)),
            "n_free": int(last.get("n_free", self.config.n_mb)),
            "percent_adsorbed": float(last.get("percent_adsorbed", 0.0)),
            "qt_mg_g": float(last.get("qt_mg_g", 0.0)),
            "n_contacts": int(last.get("n_contacts", 0)),
            "m_adsorbed_mg": float(last.get("m_adsorbed_mg", 0.0)),
            "material": self.config.material.value,
            "seed": self.settings.seed,
            "sigma_px": self.settings.sigma_px,
            "n_steps_target": self.settings.n_steps,
        }


def create_session(
    material: MaterialChoice,
    seed: int,
    sigma_px: float,
    n_steps: int,
    p_ads: float | None = None,
) -> InteractiveSession:
    cfg = config_for_material(material)
    settings = RunSettings(seed=seed, sigma_px=sigma_px, n_steps=n_steps, p_ads=p_ads)
    state, rng = initialize_state(cfg, settings)
    session = InteractiveSession(config=cfg, settings=settings, state=state, rng=rng)
    session.series.append(snapshot(state, None))
    return session


def launch_interactive_viewer(
    material: MaterialChoice = "GO",
    seed: int = 1,
    sigma_px: float = 1.5,
    n_steps: int = 400,
    p_ads: float | None = None,
    interval_ms: int = 30,
) -> None:
    """Abre ventana Matplotlib con animación, pausa y reinicio."""
    try:
        import tkinter  # noqa: F401 — requerido para backend TkAgg en Windows
    except ImportError as exc:
        raise SystemExit(
            "No se puede abrir la ventana: este intérprete no incluye tkinter.\n"
            "El Python embebido en .tools/python312 suele no traerlo.\n\n"
            "Solución recomendada:\n"
            "  1) Instala Python 3.12 (64-bit) desde https://www.python.org/downloads/\n"
            "     (marca «Add python.exe to PATH» en el instalador).\n"
            "  2) En la raíz del repo: python -m venv .venv\n"
            "  3) .\\.venv\\Scripts\\Activate.ps1\n"
            "  4) pip install -r requirements.txt\n"
            "  5) $env:PYTHONPATH = \"src\"\n"
            "  6) python -m go_mb.cli view --material AC --seed 1 --sigma 1.5 --steps 400\n\n"
            "Comprueba el entorno con: .\\scripts\\check_view_env.ps1"
        ) from exc
    import matplotlib

    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from matplotlib.widgets import Button

    session = create_session(material, seed, sigma_px, n_steps, p_ads)
    domain = float(session.config.domain_px)
    mb_s = session.config.mb_size_px
    go_s = session.config.go_size_px
    ads_label = session.material_label

    fig = plt.figure(figsize=(10, 6))
    fig.canvas.manager.set_window_title(f"Simulación 2D {material}–MB (vista, no es el experimento)")
    ax_field = fig.add_axes([0.05, 0.18, 0.55, 0.75])
    ax_metrics = fig.add_axes([0.65, 0.35, 0.32, 0.55])
    ax_series = fig.add_axes([0.65, 0.18, 0.32, 0.14])

    ax_field.set_xlim(0, domain)
    ax_field.set_ylim(0, domain)
    ax_field.set_aspect("equal")
    ax_field.set_title(f"{material}–MB | σ={sigma_px} | seed={seed} | P={n_steps}")

    ads_scatter = ax_field.scatter([], [], s=go_s ** 2, c="black", marker="s", label=ads_label)
    mb_free_scatter = ax_field.scatter([], [], s=mb_s ** 2, c="tab:blue", marker="s", label="MB libre")
    mb_ads_scatter = ax_field.scatter([], [], s=mb_s ** 2, c="tab:red", marker="s", label="MB adsorbido")
    ax_field.legend(loc="upper right", fontsize=8)

    metrics_text = ax_metrics.text(
        0.0,
        1.0,
        "",
        transform=ax_metrics.transAxes,
        va="top",
        fontsize=9,
        family="monospace",
    )
    ax_metrics.axis("off")
    (line_pct,) = ax_series.plot([], [], color="tab:blue")
    ax_series.set_xlabel("paso")
    ax_series.set_ylabel("% ads")
    ax_series.set_title("Evolución (motor)")

    ax_pause = fig.add_axes([0.15, 0.04, 0.12, 0.06])
    ax_reset = fig.add_axes([0.30, 0.04, 0.12, 0.06])
    btn_pause = Button(ax_pause, "Pausa")
    btn_reset = Button(ax_reset, "Reiniciar")

    def toggle_pause(_event) -> None:
        session.paused = not session.paused
        btn_pause.label.set_text("Reanudar" if session.paused else "Pausa")

    def do_reset(_event) -> None:
        session.reset()
        btn_pause.label.set_text("Pausa")

    btn_pause.on_clicked(toggle_pause)
    btn_reset.on_clicked(do_reset)

    def refresh_artists() -> None:
        st = session.state
        free = st.mb_free
        mb = st.mb_xy
        go = st.go_xy
        if np.any(free):
            mb_free_scatter.set_offsets(mb[free])
        else:
            mb_free_scatter.set_offsets(np.empty((0, 2)))
        if np.any(~free):
            mb_ads_scatter.set_offsets(mb[~free])
        else:
            mb_ads_scatter.set_offsets(np.empty((0, 2)))
        ads_scatter.set_offsets(go)
        m = session.metrics_dict()
        fixed_note = " (fijo)" if session.config.material == MaterialKind.AC else " (móvil)"
        metrics_text.set_text(
            f"material: {material}{fixed_note}\n"
            f"paso: {m['step']} / {m['n_steps_target']}\n"
            f"Nads: {m['n_adsorbed']} / {session.config.n_mb}\n"
            f"libres: {m['n_free']}\n"
            f"% ads: {m['percent_adsorbed']:.1f}\n"
            f"qt: {m['qt_mg_g']:.2f} mg/g\n"
            f"contactos: {m['n_contacts']}\n"
            f"m_ads: {m['m_adsorbed_mg']:.3f} mg\n"
            f"seed={seed} σ={sigma_px}\n"
            f"(métricas del motor)"
        )
        steps = [row["step"] for row in session.series]
        pcts = [row["percent_adsorbed"] for row in session.series]
        line_pct.set_data(steps, pcts)
        ax_series.relim()
        ax_series.autoscale_view()

    def on_frame(_i: int) -> None:
        if not session.paused and not session.finished:
            session.step_once()
        refresh_artists()

    refresh_artists()
    _anim = FuncAnimation(fig, on_frame, interval=interval_ms, cache_frame_data=False)
    fig._sim_anim = _anim  # noqa: SLF001 — evitar GC del anim
    plt.show()
