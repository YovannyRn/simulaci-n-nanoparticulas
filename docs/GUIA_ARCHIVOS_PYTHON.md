# Guía de archivos Python

Esta guía resume la responsabilidad general de cada archivo Python del repositorio. La documentación describe el comportamiento implementado; no convierte los parámetros provisionales del modelo en datos experimentales ni bibliográficos.

## Aplicación y empaquetado

- `packaging/present_entry.py`: prepara el punto de entrada para presentar o ejecutar la aplicación.
- `src/go_mb/__init__.py`: define los elementos que se exponen al importar el paquete.
- `src/go_mb/__main__.py`: permite ejecutar el paquete como módulo.
- `src/go_mb/cli.py`: procesa los comandos para ejecutar simulaciones y consultar resultados.
- `src/go_mb/cli_sensitivity.py`: ofrece los comandos de análisis de sensibilidad.
- `src/go_mb/launcher_ui.py`: construye la interfaz para iniciar y configurar ejecuciones.
- `src/go_mb/launcher_validation.py`: valida los valores y opciones de lanzamiento.
- `src/go_mb/interactive.py`: coordina la experiencia interactiva de configuración o exploración.
- `src/go_mb/presentation.py`: agrupa utilidades relacionadas con la presentación.

## Núcleo de la simulación

- `src/go_mb/config.py`: define materiales, geometría, parámetros, procedencia y ajustes de ejecución.
- `src/go_mb/state.py`: representa el estado dinámico, coloca partículas y comprueba los límites del recinto.
- `src/go_mb/motion.py`: aplica desplazamientos brownianos simplificados y rebotes en las paredes.
- `src/go_mb/contact.py`: identifica pares de partículas que cumplen la condición geométrica de contacto.
- `src/go_mb/adsorption.py`: aplica la regla de adsorción tras el contacto y comprueba la capacidad restante.
- `src/go_mb/engine.py`: coordina cada paso y la corrida completa: movimiento, contacto, adsorción y métricas.
- `src/go_mb/metrics.py`: registra y resume masa adsorbida, concentración, qt, contactos y evolución.
- `src/go_mb/models.py`: calcula referencias teóricas de Langmuir y pseudo-segundo orden; no decide la adsorción.
- `src/go_mb/pso_reference.py`: calcula referencias basadas en pseudo-segundo orden.
- `src/go_mb/io.py`: persiste y recupera corridas y estudios en JSON/CSV.
- `src/go_mb/viz.py`: genera representaciones gráficas del estado y de los resultados.

## Campañas, análisis y visualización

- `src/go_mb/experiments.py`: prepara configuraciones y utilidades para ejecuciones comparables.
- `src/go_mb/sensitivity.py`: evalúa la sensibilidad a parámetros de simulación.
- `src/go_mb/compare.py`: compara escenarios y resultados.
- `src/go_mb/compare_viz.py`: visualiza las comparaciones.
- `src/go_mb/final_campaign.py`: ejecuta la campaña computacional final.
- `src/go_mb/final_campaign_viz.py`: representa los resultados de esa campaña.
- `src/go_mb/final_protocol_analysis.py`: agrega y analiza los resultados conforme al protocolo final.
- `src/go_mb/final_protocol_viz.py`: crea figuras del análisis del protocolo final.
- `src/go_mb/final_temporal_reference.py`: calcula referencias temporales y compara la evolución con modelos de referencia.
- `src/go_mb/final_temporal_reference_viz.py`: visualiza el análisis temporal de referencia.
- `src/go_mb/geometry_update_pilot.py`: ejecuta pruebas piloto de actualización geométrica.
- `src/go_mb/homogeneous_temporal.py`: ejecuta campañas temporales homogéneas.
- `src/go_mb/homogeneous_viz.py`: visualiza las campañas temporales homogéneas.
- `src/go_mb/p_ads_055.py`: ejecuta el escenario temporal configurado con P_ads = 0,55.
- `src/go_mb/p_ads_sensitivity.py`: estudia el efecto de variar P_ads.
- `src/go_mb/p_ads_sensitivity_viz.py`: visualiza el análisis de sensibilidad de P_ads.
- `src/go_mb/temporal_calibration.py`: analiza la calibración temporal frente a referencias.
- `src/go_mb/temporal_calibration_viz.py`: genera las visualizaciones de calibración temporal.
- `src/go_mb/stats.py`: calcula resúmenes estadísticos.
- `scripts/run_ac_sensitivity_batch.py`: ejecuta un lote de sensibilidad para AC.
- `scripts/build_documentation_pdf.py`: construye un PDF de documentación.
- `scripts/build_guia_explicacion.py`: genera la guía explicativa del modelo.

## Pruebas automatizadas

Los archivos de `tests/` verifican comportamientos del software. No son experimentos de laboratorio ni validación física por sí mismos.

- `tests/test_ac_mb.py`: comprueba el escenario AC–MB.
- `tests/test_ac_sensitivity.py`: comprueba el análisis de sensibilidad de AC.
- `tests/test_adsorption.py`: comprueba las reglas de adsorción.
- `tests/test_compare.py`: comprueba la comparación de resultados.
- `tests/test_config_models.py`: comprueba parámetros y modelos de referencia.
- `tests/test_contact.py`: comprueba la detección geométrica de contactos.
- `tests/test_contract_rules.py`: comprueba reglas y contratos del modelo.
- `tests/test_engine_campaign.py`: comprueba el motor y las campañas.
- `tests/test_final_campaign.py`: comprueba la campaña final.
- `tests/test_final_protocol_analysis.py`: comprueba el análisis del protocolo final.
- `tests/test_final_temporal_reference.py`: comprueba el análisis temporal de referencia.
- `tests/test_geometry_wiam.py`: comprueba la geometría actualizada.
- `tests/test_homogeneous_temporal.py`: comprueba las campañas temporales homogéneas.
- `tests/test_homogeneous_wiam_campaign.py`: comprueba la campaña homogénea con geometría actualizada.
- `tests/test_interactive.py`: comprueba la funcionalidad interactiva.
- `tests/test_launcher_ui.py`: comprueba la interfaz de lanzamiento.
- `tests/test_macos_launch_scripts.py`: comprueba los scripts de inicio para macOS.
- `tests/test_motion.py`: comprueba el movimiento y los rebotes.
- `tests/test_p_ads_sensitivity.py`: comprueba la sensibilidad de P_ads.
- `tests/test_sensitivity.py`: comprueba los análisis de sensibilidad.
- `tests/test_state.py`: comprueba la inicialización y el estado.
- `tests/test_temporal_calibration.py`: comprueba la calibración temporal.

## Criterio de interpretación

Los comentarios explican el código tal como está implementado. Parámetros como `sigma`, el número de pasos y `P_ads` deben interpretarse según su estado de procedencia en la configuración y documentación del proyecto; no deben confundirse automáticamente con valores experimentales validados.
