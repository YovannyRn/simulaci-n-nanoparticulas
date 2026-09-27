"""Comprueba que los lanzadores macOS existen y tienen sintaxis bash válida."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_macos_launch_files_exist() -> None:
    assert (ROOT / "Instalar_y_abrir.command").is_file()
    assert (ROOT / "Iniciar_Simulacion.command").is_file()
    assert (ROOT / "scripts" / "macos_launch_helpers.sh").is_file()


def _bash_for_syntax_check() -> str | None:
    candidates: list[str] = []
    found = shutil.which("bash")
    if found:
        candidates.append(found)
    for extra in (
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ):
        if Path(extra).is_file():
            candidates.append(extra)
    for bash in candidates:
        probe = subprocess.run(
            [bash, "-c", "exit 0"],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode == 0 and "WSL" not in (probe.stderr or ""):
            return bash
    return None


def test_macos_launch_scripts_bash_syntax() -> None:
    bash = _bash_for_syntax_check()
    if bash is None:
        return
    for rel in (
        "Instalar_y_abrir.command",
        "Iniciar_Simulacion.command",
        "scripts/macos_launch_helpers.sh",
    ):
        path = ROOT / rel
        proc = subprocess.run(
            [bash, "-n", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr


def test_macos_installer_is_idempotent_by_design() -> None:
    installer = (ROOT / "Instalar_y_abrir.command").read_text(encoding="utf-8")
    helpers = (ROOT / "scripts" / "macos_launch_helpers.sh").read_text(encoding="utf-8")
    assert "macos_deps_ready" in installer
    assert "ya están instaladas" in installer
    assert "ya existe" in installer
    assert "-m go_mb" in helpers
    assert 'PYTHONPATH="$root/src"' in helpers or "PYTHONPATH=\"$root/src\"" in helpers
