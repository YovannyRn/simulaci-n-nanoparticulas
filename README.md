# Simulación 2D de adsorción de azul de metileno en óxido de grafeno

Experimento computacional (no molecular). Cadena **movimiento → contacto → adsorción**. Langmuir y PSO son referencias macroscópicas: **no fuerzan** el resultado.

Contrato: [`docs/especificacion.md`](docs/especificacion.md). Huecos: [`docs/PENDIENTES.md`](docs/PENDIENTES.md).

## Requisitos

```bash
python3 -m pip install -r requirements.txt
```

## Motor (sin interfaz)

`--sigma` (D) y `--steps` (P) son **PENDIENTE** en el documento: hay que inyectarlos. No son propiedades físicas de [1].

```bash
PYTHONPATH=src python3 -m go_mb.cli run --seed 1 --sigma 1.0 --steps 400 --out data/results --plot
```

Campaña (Nrep también PENDIENTE: el PDF dice 30 y 40):

```bash
PYTHONPATH=src python3 -m go_mb.cli campaign --n-rep 3 --base-seed 1000 --sigma 1.0 --steps 200 --out data/results
```

Graficar un resultado ya guardado:

```bash
PYTHONPATH=src python3 -m go_mb.cli plot --input data/results/go_seed_1.json --out figures
```

## Tests

```bash
PYTHONPATH=src python3 -m pytest
```

## Qué no hace este código

- No inventa `P_ads` de literatura (regla por defecto: capacidad másica de objetos enteros).
- No detiene la corrida en qe = 380,7 mg/g.
- No asigna probabilidad de colisión.
- No ejecuta el sistema CA: el PDF no lo parametriza.
- Un paso **no** es un minuto.
