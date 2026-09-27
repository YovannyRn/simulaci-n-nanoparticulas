#!/bin/bash
# Doble clic en Finder: abre la misma GUI que Iniciar_Simulacion.vbs en Windows.
# Entrada: PYTHONPATH=src  y  .venv/bin/python -m go_mb

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

VENV_PY="$ROOT/.venv/bin/python"

show_message() {
  local title="$1"
  local body="$2"
  if command -v osascript >/dev/null 2>&1; then
    osascript - "$title" "$body" <<'APPLESCRIPT' >/dev/null 2>&1 || true
on run argv
  set dlgTitle to item 1 of argv
  set dlgBody to item 2 of argv
  display dialog dlgBody with title dlgTitle buttons {"OK"} default button "OK" with icon caution
end run
APPLESCRIPT
  fi
  echo "$body" >&2
  if [[ -t 0 ]]; then
    read -r -p "Pulse Enter para cerrar..." _
  fi
}

if [[ ! -x "$VENV_PY" ]]; then
  show_message "Simulación MB" "No se encontró el entorno .venv.

Una sola vez, en esta carpeta (Terminal):
  python3.12 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

Después vuelva a hacer doble clic en Iniciar_Simulacion.command.
Detalle: docs/GUI_WIAM.md"
  exit 1
fi

if ! "$VENV_PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
  ver="$("$VENV_PY" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo desconocida)"
  show_message "Simulación MB" "El Python de .venv debe ser 3.12 o superior (ahora: ${ver}).

Recree el entorno con Python 3.12:
  rm -rf .venv
  python3.12 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

Detalle: docs/GUI_WIAM.md"
  exit 1
fi

export PYTHONPATH="$ROOT/src"
exec "$VENV_PY" -m go_mb
