#!/bin/bash
# Doble clic en Finder: abre la misma GUI que Iniciar_Simulacion.vbs en Windows.
# Entrada: PYTHONPATH=src  y  .venv/bin/python -m go_mb

set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source "$ROOT/scripts/macos_launch_helpers.sh"

VENV_PY="$(macos_venv_python "$ROOT")"

if ! macos_venv_python_ok "$VENV_PY"; then
  macos_fail "Simulación MB" "Aún no está preparado el entorno de la simulación.

Haga doble clic en Instalar_y_abrir.command (solo la primera vez).
Después use Iniciar_Simulacion.command cada día.

Detalle: docs/GUI_WIAM.md"
fi

macos_launch_gui "$ROOT"
