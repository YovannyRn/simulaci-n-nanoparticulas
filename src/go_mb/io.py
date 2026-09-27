"""Guardado de resultados. No dibuja ni decide la adsorción.

El CSV es la tabla que se puede abrir en una hoja de cálculo.
El JSON guarda la misma corrida con su configuración y su serie,
para poder volver a la procedencia de un número o de un gráfico.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def save_run(result: dict[str, Any], directory: str | Path, stem: str) -> dict[str, str]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{stem}.json"
    csv_path = directory / f"{stem}.csv"
    payload = {k: v for k, v in result.items() if k != "series"}
    payload["series_csv"] = str(csv_path)
    json_path.write_text(json.dumps(payload, indent=2))
    series = result["series"]
    if series:
        with csv_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(series[0].keys()))
            writer.writeheader()
            writer.writerows(series)
    return {"json": str(json_path), "csv": str(csv_path)}


def save_study(study: dict[str, Any], directory: str | Path, stem: str) -> str:
    """Persiste un estudio de sensibilidad (JSON agregado + filas por corrida)."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{stem}.json"
    path.write_text(json.dumps(study, indent=2, default=str))
    return str(path)


def load_study(json_path: str | Path) -> dict[str, Any]:
    return json.loads(Path(json_path).read_text())


def load_run(json_path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(json_path).read_text())
    csv_path = data.get("series_csv")
    series: list[dict[str, float | int]] = []
    if csv_path and Path(csv_path).exists():
        with Path(csv_path).open(newline="") as fh:
            for row in csv.DictReader(fh):
                parsed: dict[str, float | int] = {}
                for k, v in row.items():
                    if k in {"step", "n_adsorbed", "n_free", "n_contacts"}:
                        parsed[k] = int(float(v))
                    else:
                        parsed[k] = float(v)
                series.append(parsed)
    data["series"] = series
    return data
