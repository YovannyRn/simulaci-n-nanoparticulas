"""Validación de entradas de la GUI (sin tkinter; usable en pytest)."""

from __future__ import annotations

from go_mb.interactive import MaterialChoice, config_for_material


P_ADS_WARNING = (
    "Decisión computacional; no representa un valor experimental universal. "
    "El valor 1.0 es el usado en la campaña final."
)

SIGMA_LABEL = "σ (magnitud del movimiento, px/paso)"
SIGMA_HELP = "Parámetro de ejecución de la simulación; no es un valor experimental medido."


def _as_float(raw: str, field: str) -> tuple[float | None, str | None]:
    text = raw.strip().replace(",", ".")
    if not text:
        return None, f"Escriba un número en «{field}»."
    try:
        return float(text), None
    except ValueError:
        return None, f"«{field}» debe ser un número."


def _as_int(raw: str, field: str) -> tuple[int | None, str | None]:
    text = raw.strip()
    if not text:
        return None, f"Escriba un número entero en «{field}»."
    try:
        if any(c in text for c in ".,"):
            return None, f"«{field}» debe ser un número entero."
        return int(text), None
    except ValueError:
        return None, f"«{field}» debe ser un número entero."


def validate_inputs(
    *,
    sigma_px: float,
    n_steps: int,
    seed: int,
    interval_ms: int,
    p_ads: float,
) -> str | None:
    if sigma_px <= 0:
        return "La magnitud del movimiento (σ) debe ser un número mayor que 0."
    if n_steps < 1:
        return "El número de pasos debe ser un entero positivo."
    if n_steps > 50_000:
        return "El número de pasos es demasiado grande (máximo 50000)."
    if seed < 0:
        return "La semilla debe ser un entero igual o mayor que 0."
    if interval_ms <= 0:
        return "El intervalo de animación debe ser un entero positivo (milisegundos)."
    if interval_ms < 5:
        return "El intervalo de animación es demasiado pequeño (mínimo 5 ms)."
    if interval_ms > 2000:
        return "El intervalo de animación es demasiado grande (máximo 2000 ms)."
    if not (0.0 <= p_ads <= 1.0):
        return "P_ads debe estar entre 0 y 1."
    return None


def parse_execution_fields(
    *,
    sigma_text: str,
    steps_text: str,
    seed_text: str,
    interval_text: str,
    p_ads_text: str,
) -> tuple[dict[str, float | int] | None, str | None]:
    """Convierte textos de la GUI. Devuelve (valores, None) o (None, mensaje sencillo)."""
    sigma, err = _as_float(sigma_text, "magnitud del movimiento")
    if err:
        return None, err
    n_steps, err = _as_int(steps_text, "pasos")
    if err:
        return None, err
    seed, err = _as_int(seed_text, "semilla")
    if err:
        return None, err
    interval_ms, err = _as_int(interval_text, "intervalo de animación")
    if err:
        return None, err
    p_ads, err = _as_float(p_ads_text, "P_ads")
    if err:
        return None, err
    assert sigma is not None and n_steps is not None and seed is not None
    assert interval_ms is not None and p_ads is not None
    msg = validate_inputs(
        sigma_px=sigma,
        n_steps=n_steps,
        seed=seed,
        interval_ms=interval_ms,
        p_ads=p_ads,
    )
    if msg:
        return None, msg
    return {
        "sigma_px": sigma,
        "n_steps": n_steps,
        "seed": seed,
        "interval_ms": interval_ms,
        "p_ads": p_ads,
    }, None


def read_only_info_text(material: MaterialChoice) -> str:
    cfg = config_for_material(material)
    mov = "fijo" if material == "AC" else "móvil"
    side = cfg.go_size_px
    return (
        f"Parámetros fijos del modelo (solo lectura)\n"
        f"{'─' * 40}\n"
        f"T = {cfg.temperature_c} °C   pH = {cfg.ph}\n"
        f"MB inicial = {cfg.m_mb_mg} mg   adsorbente = {cfg.m_go_g * 1000:.0f} mg\n"
        f"V = {cfg.volume_l * 1000:.0f} mL   C₀ = {cfg.c0_mg_l:.0f} mg/L\n"
        f"N MB = {cfg.n_mb}   N {material} = {cfg.n_go}\n"
        f"MB {cfg.mb_size_px}×{cfg.mb_size_px} px   "
        f"{material} {side}×{side} px ({mov})\n"
        f"qmax = {cfg.qmax_mg_g} mg/g   KL = {cfg.kl_l_mg} L/mg\n"
        f"Los pasos de simulación NO son minutos."
    )
