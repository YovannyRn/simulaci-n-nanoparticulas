"""Sin argumentos: interfaz de presentación. Con argumentos: CLI headless."""

from __future__ import annotations

import sys


def _run_presentation() -> int:
    try:
        from go_mb.launcher_ui import run_presentation_app

        run_presentation_app()
        return 0
    except ImportError as exc:
        print(
            "No se pudo abrir la interfaz (falta tkinter o dependencias).\n"
            "Instale Python desde python.org, cree .venv e instale requirements.txt.\n"
            "Ejecute: .\\scripts\\check_view_env.ps1\n",
            file=sys.stderr,
        )
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        raise SystemExit(_run_presentation())
    from go_mb.cli import main

    raise SystemExit(main())
