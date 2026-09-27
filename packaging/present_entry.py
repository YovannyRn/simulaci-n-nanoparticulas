"""Punto de entrada del ejecutable. No contiene lógica científica."""

from __future__ import annotations

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot  # noqa: F401  — PyInstaller debe incluir el backend
import tkinter  # noqa: F401
from matplotlib.backends import backend_tkagg  # noqa: F401

from go_mb.launcher_ui import run_presentation_app


def main() -> None:
    run_presentation_app()


if __name__ == "__main__":
    main()
