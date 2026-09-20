# Simulación 2D de adsorción de azul de metileno en óxido de grafeno

Experimento **computacional** (no molecular). Cadena **movimiento → contacto → adsorción**. Langmuir y PSO son referencias macroscópicas: **no fuerzan** el resultado.

Contrato: [`docs/especificacion.md`](docs/especificacion.md). Huecos y decisiones ya programadas: [`docs/PENDIENTES.md`](docs/PENDIENTES.md).

Una corrida del motor **no** es validación experimental.

## Requisitos

```bash
python3 -m pip install -r requirements.txt
```

## Motor (sin interfaz)

`--sigma` (D) y `--steps` (P) son **PENDIENTE** en el documento: hay que inyectarlos. Los números de los ejemplos siguientes son **parámetros de ejecución/prueba**, no D ni P científicos de [1]/[2].

Corrida reproducible (demostración computacional):

```bash
PYTHONPATH=src python3 -m go_mb.cli run --seed 1 --sigma 1.5 --steps 400 --out data/results
```

Con esa semilla y esos parámetros de prueba el motor llegó a **146/200** MB adsorbidos. Ese recuento es una **demostración computacional**, no una validación experimental ni un objetivo a clavar.

`--p-ads` por defecto es `None`: **DECISIÓN COMPUTACIONAL PROVISIONAL** equivalente a P_ads=1 tras contacto geométrico y capacidad restante ≥ 0,02 mg. No es un valor de literatura.

Campaña (Nrep también PENDIENTE: el PDF dice 30 y 40; hay que inyectarlo; no lances campañas estadísticas hasta cerrar esta auditoría):

```bash
PYTHONPATH=src python3 -m go_mb.cli campaign --n-rep 3 --base-seed 1000 --sigma 1.5 --steps 400 --out data/results
```

Graficar un resultado ya guardado (Matplotlib no forma parte del motor):

```bash
PYTHONPATH=src python3 -m go_mb.cli plot --input data/results/go_seed_1.json --out figures
```

## Tests

```bash
PYTHONPATH=src python3 -m pytest
```

## Qué no hace este código

- No inventa `P_ads` de literatura. El defecto es una decisión provisional (P_ads=1 tras contacto y capacidad).
- No detiene la corrida en qe = 380,7 mg/g.
- No asigna probabilidad de colisión.
- No convierte `sigma=1.5` ni `steps=400` en valores científicos definitivos.
- No ejecuta el sistema CA: el PDF no lo parametriza.
- Un paso **no** es un minuto.
- Un recuento como 146/200 **no** valida el experimento de laboratorio.
