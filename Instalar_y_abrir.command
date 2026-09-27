#!/bin/bash
# Primera vez en macOS: doble clic → crea .venv, instala dependencias si hace falta y abre la GUI.
# Ejecuciones posteriores: use Iniciar_Simulacion.command (este archivo también puede repetirse con seguridad).

set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source "$ROOT/scripts/macos_launch_helpers.sh"

echo "=========================================="
echo "  Simulación MB — instalación (macOS)"
echo "=========================================="
echo "Carpeta del proyecto: $ROOT"
echo ""

PY312=""
if PY312="$(macos_resolve_python312)"; then
  echo "[OK] Python 3.12 encontrado."
else
  macos_fail "Simulación MB" "$(macos_python312_missing_message)"
fi

VENV_PY="$(macos_venv_python "$ROOT")"

if macos_venv_python_ok "$VENV_PY"; then
  echo "[OK] El entorno .venv ya existe."
else
  if [[ -d "$ROOT/.venv" ]]; then
    macos_fail "Simulación MB" "Hay una carpeta .venv pero no es válida o no usa Python 3.12.

Elimine la carpeta .venv de este proyecto (arrástrela a la Papelera) y vuelva a hacer doble clic en Instalar_y_abrir.command."
  fi
  echo "Creando .venv (solo la primera vez; puede tardar un minuto)..."
  if ! "$PY312" -m venv "$ROOT/.venv"; then
    macos_fail "Simulación MB" "No se pudo crear .venv.

Compruebe que Python 3.12 está bien instalado y vuelva a intentarlo."
  fi
  echo "[OK] Entorno .venv creado."
fi

if macos_deps_ready "$VENV_PY"; then
  echo "[OK] Las dependencias ya están instaladas (no se reinstalan)."
else
  echo "Instalando dependencias desde requirements.txt (solo la primera vez)..."
  if ! "$VENV_PY" -m pip install -r "$ROOT/requirements.txt"; then
    macos_fail "Simulación MB" "No se pudieron instalar las dependencias.

Compruebe su conexión a internet y vuelva a hacer doble clic en Instalar_y_abrir.command."
  fi
  if ! macos_deps_ready "$VENV_PY"; then
    macos_fail "Simulación MB" "Tras instalar, faltan paquetes necesarios.

Vuelva a hacer doble clic en Instalar_y_abrir.command. Si el problema continúa, consulte docs/GUI_WIAM.md."
  fi
  echo "[OK] Dependencias instaladas."
fi

macos_chmod_launchers "$ROOT"
echo "[OK] Permisos del lanzador preparados."
echo ""
echo "Abriendo la ventana de la simulación..."
echo "(Puede dejar esta ventana de Terminal abierta mientras usa el programa.)"
echo ""

macos_launch_gui "$ROOT"
