# Funciones compartidas para Iniciar_Simulacion.command e Instalar_y_abrir.command (macOS).
# No modifica el motor científico; solo prepara .venv y lanza: PYTHONPATH=src python -m go_mb

macos_show_dialog() {
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
}

macos_pause_before_close() {
  if [[ -t 0 ]]; then
    read -r -p "Pulse Enter para cerrar..." _
  fi
}

macos_fail() {
  local title="$1"
  local body="$2"
  macos_show_dialog "$title" "$body"
  macos_pause_before_close
  exit 1
}

# Devuelve la ruta de un intérprete Python 3.12 (stdout) o código distinto de 0 si no hay ninguno.
macos_resolve_python312() {
  local candidates=(
    python3.12
    /usr/local/bin/python3.12
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
    /opt/homebrew/bin/python3.12
  )
  local c
  for c in "${candidates[@]}"; do
    if command -v "$c" >/dev/null 2>&1; then
      if "$c" -c 'import sys; exit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null; then
        command -v "$c"
        return 0
      fi
    fi
  done
  if command -v python3 >/dev/null 2>&1; then
    if python3 -c 'import sys; exit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null; then
      command -v python3
      return 0
    fi
  fi
  return 1
}

macos_python312_missing_message() {
  cat <<'EOF'
No se encontró Python 3.12 en este Mac.

1. Abra en el navegador: https://www.python.org/downloads/
2. Descargue e instale Python 3.12 para macOS (instalador oficial).
3. Vuelva a hacer doble clic en Instalar_y_abrir.command.

No hace falta usar la Terminal para instalar Python.
EOF
}

macos_venv_python() {
  local root="$1"
  echo "$root/.venv/bin/python"
}

macos_venv_python_ok() {
  local venv_py="$1"
  [[ -x "$venv_py" ]] && "$venv_py" -c 'import sys; exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null
}

macos_deps_ready() {
  local venv_py="$1"
  "$venv_py" -c 'import numpy, matplotlib' 2>/dev/null
}

macos_chmod_launchers() {
  local root="$1"
  chmod +x "$root/Iniciar_Simulacion.command" "$root/Instalar_y_abrir.command" 2>/dev/null || true
}

macos_launch_gui() {
  local root="$1"
  local venv_py
  venv_py="$(macos_venv_python "$root")"
  export PYTHONPATH="$root/src"
  exec "$venv_py" -m go_mb
}
