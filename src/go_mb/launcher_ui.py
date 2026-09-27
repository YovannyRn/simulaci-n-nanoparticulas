"""Pantalla de configuración para Wiam (Tkinter). Invoca el mismo motor que el CLI."""

from __future__ import annotations

from typing import Any

from go_mb.interactive import launch_interactive_viewer
from go_mb.launcher_validation import (
    P_ADS_WARNING,
    SIGMA_HELP,
    SIGMA_LABEL,
    parse_execution_fields,
    read_only_info_text,
)
from go_mb.presentation import PresentationDefaults, default_presentation


def show_config_dialog(
    defaults: PresentationDefaults | None = None,
) -> dict[str, Any] | None:
    """Modal hasta Iniciar (dict de parámetros) o Salir (None)."""
    import tkinter as tk
    from tkinter import messagebox, ttk

    d = defaults or default_presentation()
    result: dict[str, Any] | None = None

    root = tk.Tk()
    root.title("Simulación MB — GO / AC")
    root.resizable(False, False)

    frm = ttk.Frame(root, padding=12)
    frm.grid(row=0, column=0, sticky="nsew")

    material_var = tk.StringVar(value=d.material)
    sigma_var = tk.StringVar(value=str(d.sigma_px))
    steps_var = tk.StringVar(value=str(d.n_steps))
    seed_var = tk.StringVar(value=str(d.seed))
    interval_var = tk.StringVar(value=str(d.interval_ms))
    p_ads_var = tk.StringVar(value=str(d.p_ads))
    advanced_var = tk.BooleanVar(value=d.show_advanced_p_ads)

    ttk.Label(frm, text="Configuración de simulación", font=("Segoe UI", 11, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
    )

    ttk.Label(frm, text="Material:").grid(row=1, column=0, sticky="w")
    mat_frm = ttk.Frame(frm)
    mat_frm.grid(row=1, column=1, sticky="w")
    ttk.Radiobutton(mat_frm, text="GO (móvil)", variable=material_var, value="GO").pack(side=tk.LEFT)
    ttk.Radiobutton(mat_frm, text="AC (fijo)", variable=material_var, value="AC").pack(
        side=tk.LEFT, padx=8
    )

    def add_row(row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w", pady=2)
        ttk.Entry(frm, textvariable=var, width=14).grid(row=row, column=1, sticky="w", pady=2)

    add_row(2, SIGMA_LABEL + ":", sigma_var)
    ttk.Label(frm, text=SIGMA_HELP, wraplength=420, foreground="#444444").grid(
        row=3, column=0, columnspan=2, sticky="w", pady=(0, 4)
    )
    add_row(4, "Pasos (steps):", steps_var)
    add_row(5, "Semilla (seed):", seed_var)
    add_row(6, "Intervalo animación (ms):", interval_var)

    info = tk.Text(frm, height=10, width=52, wrap=tk.WORD, font=("Consolas", 9))
    info.grid(row=7, column=0, columnspan=2, pady=(10, 4), sticky="ew")
    info.configure(state=tk.DISABLED, background="#f5f5f5")

    def refresh_info(*_args: object) -> None:
        mat = material_var.get()
        info.configure(state=tk.NORMAL)
        info.delete("1.0", tk.END)
        info.insert("1.0", read_only_info_text(mat))  # type: ignore[arg-type]
        info.configure(state=tk.DISABLED)

    material_var.trace_add("write", refresh_info)
    refresh_info()

    adv_chk = ttk.Checkbutton(
        frm,
        text="Opciones avanzadas (P_ads)",
        variable=advanced_var,
    )
    adv_chk.grid(row=8, column=0, columnspan=2, sticky="w", pady=(6, 0))

    p_ads_entry = ttk.Entry(frm, textvariable=p_ads_var, width=14, state=tk.DISABLED)
    p_ads_entry.grid(row=9, column=1, sticky="w")
    ttk.Label(frm, text="P_ads (0–1):").grid(row=9, column=0, sticky="w")
    warn_lbl = ttk.Label(frm, text=P_ADS_WARNING, wraplength=420, foreground="#884400")
    warn_lbl.grid(row=10, column=0, columnspan=2, sticky="w", pady=(2, 6))
    warn_lbl.grid_remove()

    def toggle_advanced(*_args: object) -> None:
        if advanced_var.get():
            p_ads_entry.configure(state=tk.NORMAL)
            warn_lbl.grid()
        else:
            p_ads_entry.configure(state=tk.DISABLED)
            p_ads_var.set(str(d.p_ads))
            warn_lbl.grid_remove()

    advanced_var.trace_add("write", toggle_advanced)
    toggle_advanced()

    btn_frm = ttk.Frame(frm)
    btn_frm.grid(row=11, column=0, columnspan=2, pady=(8, 0))

    def apply_recommended() -> None:
        rec = default_presentation()
        material_var.set(rec.material)
        sigma_var.set(str(rec.sigma_px))
        steps_var.set(str(rec.n_steps))
        seed_var.set(str(rec.seed))
        interval_var.set(str(rec.interval_ms))
        p_ads_var.set(str(rec.p_ads))
        advanced_var.set(False)

    def on_start() -> None:
        nonlocal result
        p_text = p_ads_var.get() if advanced_var.get() else str(d.p_ads)
        parsed, err = parse_execution_fields(
            sigma_text=sigma_var.get(),
            steps_text=steps_var.get(),
            seed_text=seed_var.get(),
            interval_text=interval_var.get(),
            p_ads_text=p_text,
        )
        if err or parsed is None:
            messagebox.showerror("Entrada no válida", err or "Revise los campos.")
            return
        material = material_var.get()
        if material not in ("GO", "AC"):
            messagebox.showerror("Material", "Seleccione GO o AC.")
            return
        result = {
            "material": material,
            "seed": int(parsed["seed"]),
            "sigma_px": float(parsed["sigma_px"]),
            "n_steps": int(parsed["n_steps"]),
            "p_ads": float(parsed["p_ads"]) if advanced_var.get() else None,
            "interval_ms": int(parsed["interval_ms"]),
        }
        root.quit()
        root.destroy()

    def on_quit() -> None:
        root.quit()
        root.destroy()

    ttk.Button(btn_frm, text="Configuración recomendada", command=apply_recommended).pack(
        side=tk.LEFT, padx=4
    )
    ttk.Button(btn_frm, text="Iniciar simulación", command=on_start).pack(side=tk.LEFT, padx=4)
    ttk.Button(btn_frm, text="Salir", command=on_quit).pack(side=tk.LEFT, padx=4)

    root.protocol("WM_DELETE_WINDOW", on_quit)
    root.mainloop()
    return result


def run_presentation_app() -> None:
    """Bucle: configuración → ventana de simulación → configuración."""
    while True:
        params = show_config_dialog()
        if params is None:
            break
        launch_interactive_viewer(
            material=params["material"],
            seed=params["seed"],
            sigma_px=params["sigma_px"],
            n_steps=params["n_steps"],
            p_ads=params["p_ads"],
            interval_ms=params["interval_ms"],
        )
