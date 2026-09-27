# Fuentes usadas en la memoria técnica

El PDF y la guía de estudio se redactaron a partir de estos archivos. No se modificaron resultados ni se lanzó una campaña nueva.

La fuente editable de ambos PDF es `scripts/build_documentation_pdf.py`. Regenerarlos exige la biblioteca `fpdf2` y las fuentes Arial del sistema.

## Parámetros y motor

- `src/go_mb/config.py` — condiciones, geometría, qmax, KL, dominio 442 px, escala 77,4 μm/px, lado 3,42 cm.
- `src/go_mb/pso_reference.py` — Langmuir y PSO de GO y AC, C0 = 100 mg/L, referencia S* = 0,55.
- `src/go_mb/models.py` — ecuaciones de Langmuir, balance de masa y PSO.
- `src/go_mb/motion.py` — incrementos normales y rebote.
- `src/go_mb/contact.py` — umbral d ≤ r_MB + r_adsorbente.
- `src/go_mb/adsorption.py` y `src/go_mb/engine.py` — orden mover → contactar → adsorber.
- `docs/PENDIENTES.md` — parámetros aún no identificados físicamente (sigma, pasos, P_ads, k2 de tabla, α).

## Campaña final

- `data/final_campaign/comparison_go_ac.csv`
- `data/final_campaign/aggregate_results.csv`
- `data/final_campaign/statistics.json`
- `data/final_campaign/provenance.json`
- `data/final_campaign/per_run_records.csv`
- `data/final_campaign/figures/` — figuras 1 a 8 del PDF (curvas PSO, Nads, qt, eficiencia, Langmuir GO, evolución).

## Etapas previas (citadas, no recalculadas)

- `data/sensitivity/homogeneous_temporal/` — geometría anterior.
- `data/sensitivity/` — malla temporal con la geometría anterior y, en una carpeta distinta, la misma malla con la geometría final.
- `data/sensitivity/p_ads_sensitivity/` — barrido P_ads.
- `data/analysis/final_temporal_reference/` — PSO por material, α exploratorio, escenario P_ads = 0,55.
- `data/analysis/final_protocol/` — análisis descriptivo previo a la campaña de 40+40.

## Pruebas

- `tests/` — 135 funciones `test_` en el estado del repositorio al redactar el documento.

## Qué no pudo documentarse con evidencia nueva

- No se repitió la campaña ni se contó de nuevo la suite en esta redacción más allá del inventario de funciones de prueba.
- No se incorporó bibliografía experimental completa más allá de los valores ya transcritos en el código y de la cita de Sha'Ato (2021) guardada en `pso_reference.py`.
- La identificación de sigma con un coeficiente de difusión, y de los pasos con minutos, no está demostrada en el repositorio; el documento la deja como límite.
