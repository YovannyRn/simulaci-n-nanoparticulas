# Mapa sencillo del repositorio

Sirve para explicar dónde está cada cosa, sin programar.

| Carpeta o archivo | Qué es | Cómo decirlo |
|---|---|---|
| `src/go_mb/` | El programa que calcula la simulación | "Aquí está el motor: movimiento, contacto y adsorción." |
| `tests/` | 135 comprobaciones automáticas del programa | "No son experimentos. Comprueban que el programa no se ha roto." |
| `scripts/` | Herramientas para tareas concretas | "Sirven para construir documentos, abrir la ventana o empaquetar. No son la ciencia." |
| `data/final_campaign/` | Las 80 simulaciones finales y sus gráficos | "De aquí salen las medias de GO y de AC." |
| `data/final_campaign_reported/` | Copia de consulta de esa campaña | "Es el mismo tipo de resultado, guardado para consultarlo." |
| `data/sensitivity/` | Pruebas anteriores: sigma, pasos, geometría, P_ads | "Aquí se exploró antes de fijar el protocolo. No se mezcla con la campaña final." |
| `data/analysis/` | Lecturas posteriores: tiempo de referencia y protocolo | "No son simulaciones nuevas del motor; leen resultados ya guardados." |
| `docs/` | Textos para estudiar y explicar | "La memoria técnica, la guía breve y esta explicación." |
| `packaging/` | Receta para crear el programa de Windows | "Para llevar la ventana a un ordenador sin instalar el entorno de desarrollo." |
| `Iniciar_Simulacion.vbs` y `.bat` | Abren la ventana de configuración | "Doble clic para presentar, sin escribir comandos." |
| `README.md` | Puerta de entrada del proyecto | "Dice qué es el modelo y cómo se lanza una corrida de prueba." |
| `requirements.txt` | Lista de bibliotecas que necesita el programa | "No son resultados." |
| `memoria.md` | Notas de trabajo del proyecto | "No sustituye a la memoria en PDF." |

Dentro de `scripts/`:

- `build_documentation_pdf.py` genera la memoria técnica y la guía breve de estudio.
- `build_guia_explicacion.py` genera esta guía de explicación.
- `build_windows.ps1` construye el ejecutable de Windows. Es una herramienta de desarrollo.
- `launch_view.ps1` abre la visualización.
- `check_view_env.ps1` comprueba si el ordenador puede abrir esa ventana.
- `run_ac_sensitivity_batch.py` sirvió para caracterizaciones del carbón activado. No es la campaña final y no hay que volver a lanzarlo para explicar los resultados.

Dentro de `src/go_mb/`, los archivos que basta saber explicar:

- `engine.py` — el ciclo: mover, tocar, adsorber, anotar.
- `motion.py` — el salto aleatorio y el rebote en el borde.
- `contact.py` — la distancia que cuenta como contacto.
- `adsorption.py` — la regla de quedarse pegado si cabe la masa.
- `config.py` — masas, tamaños, capacidades y condiciones.
- `models.py` — Langmuir y la curva cinética, al margen del motor.
- `metrics.py` — qt y el resto de números de una corrida.
- `stats.py` — medias y dispersión de varias semillas.
- `io.py` — cómo se guardan CSV y JSON.
- `viz.py` e `interactive.py` — los dibujos. No cambian la física.
