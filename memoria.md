# Memoria del proyecto (contexto acumulado)

Documento **vivo** para recapitular decisiones, datos, hallazgos y pendientes del simulador GO–MB 2D.  
No sustituye `docs/especificacion.md` ni `docs/PENDIENTES.md`; los complementa con el hilo de trabajo y resultados.

**Última actualización:** 2026-09-26 (Campaña final 40+40 GO vs AC)

---

## Cómo usar este archivo

- Añadir entradas en **Cronología** cuando haya sesiones relevantes (auditorías, campañas, informes).
- Mantener **Estado actual** al día (tests, rama, datos en disco).
- No fijar aquí parámetros científicos definitivos salvo que el equipo los declare explícitamente en otro doc.

---

## Proyecto en una frase

Simulación computacional 2D de adsorción de metileno azul (MB) sobre óxido de grafeno (GO): movimiento browniano → contacto geométrico → adsorción por objetos discretos. Langmuir/PSO son **referencia**, no objetivo de ajuste.

---

## Referencias contractuales

| Recurso | Ruta |
|--------|------|
| Especificación | `docs/especificacion.md` |
| Parámetros pendientes | `docs/PENDIENTES.md` |
| Motor | `src/go_mb/` |
| Sensibilidad (CLI) | `python -m go_mb.cli sensitivity {sigma\|steps\|grid\|plot}` |
| Tests | `tests/` — ver última ejecución pytest (incl. `geometry_wiam`, `homogeneous_temporal`) |
| Comparación GO vs AC (asimétrica previa) | `python -m go_mb.cli compare` → `data/comparison/go_vs_ac/` |
| **Homogeneización temporal (referencia actual)** | `python -m go_mb.cli homogeneous` → `data/sensitivity/homogeneous_temporal_wiam_geometry/` |
| Homogeneización legacy (histórico) | `homogeneous --geometry-era legacy_geometry` → `homogeneous_temporal/` |
| Calibración temporal (exploratoria) | `python -m go_mb.cli temporal-calibration` → `data/analysis/temporal_calibration/` |
| Análisis protocolo final (P=2000) | `python -m go_mb.cli final-protocol` → `data/analysis/final_protocol/` |
| **Sensibilidad P_ads (computacional)** | `python -m go_mb p-ads-sensitivity` → `data/sensitivity/p_ads_sensitivity/` |
| **Referencia temporal + S* + P_ads=0.55** | `python -m go_mb final-temporal-reference` → `data/analysis/final_temporal_reference/` |
| **Campaña final (autorizada)** | `python -m go_mb final-campaign` → `data/final_campaign/` |

**Rama / PR (contexto sesión):** `cursor/go-mb-simulation-5bed`, PR #1 (actualizado en trabajo previo).

---

## Decisiones ya implementadas (no renegociar sin acuerdo)

- Recinto 442×442 px; 200 MB (**1×1** Wiam), 100 adsorbentes: GO **7×7**, AC **2×2**; radios contacto inscritos 0,5 / 3,5 / 1,0 px.
- Histórico: campaña `homogeneous_temporal/` = MB 5×5, adsorbente 7×7 (GO y AC).
- Contacto: distancia ≤ r_MB + r_A (círculos inscritos).
- **P_ads físico:** PENDIENTE. **Provisional:** adsorción determinista si hay capacidad ≥ 0,02 mg (equiv. P_ads=1); opcional `--p-ads` Bernoulli.
- **σ y P:** obligatorios por CLI; valores en demos (p. ej. σ=1.5, P=400) son **ejecución**, no literatura.
- **No** calibrar motor a qe = 380,7 mg/g.
- Conservación de masa comprobada en corridas de sensibilidad (`mass_conservation_ok: true`).

---

## Parámetros aún PENDIENTES (no fijados en memoria)

- P_ads (físico/bibliográfico)
- D/σ y P como magnitudes/valores de campaña definitiva
- k2 unificado (PSO referencia usa ejemplo 0,0002)
- Nrep (30 vs 40) y diseño estadístico formal
- α (min/paso)
- CA (sistema no ejecutado)
- Elección explícita de σ y P para campaña — **no automática**

---

## Inventario de datos de sensibilidad

| Carpeta | Contenido |
|---------|-----------|
| `data/sensitivity/sigma/` | σ ∈ {0.5, 1, 1.5, 2}, P=400, seed=1 |
| `data/sensitivity/steps/` | P ∈ {50, 100, 200, 400, 600}, σ=1.5, seed=1 |
| `data/sensitivity/grid/` | malla 3×3 σ×P, seed=1 |
| `data/sensitivity/seeds/` | σ∈{1,1.5} × P∈{200,400} × seeds 1–5 (20 corridas) |
| `data/sensitivity/stabilization_exploratory/` | **Exploratorio GO (no campaña definitiva):** σ∈{1,1.5}, P∈{200…2000}, seeds 1–5 (70 corridas) |
| `data/sensitivity/ac/sigma/` | AC: σ∈{0.5,1,1.5,2}, P=400, seed=1 |
| `data/sensitivity/ac/steps_sigma_1_0/` | AC: σ=1.0, P∈{200…2000}, seed=1 |
| `data/sensitivity/ac/steps_sigma_1_5/` | AC: σ=1.5, P∈{200…2000}, seed=1 |
| `data/sensitivity/ac/grid/` | AC: σ∈{1,1.5}×P completo, seed=1 (heatmap) |
| `data/sensitivity/ac/seeds/` | AC: σ∈{1,1.5}×P∈{200,400}×seeds 1–5 |

Clasificación: `computational_sensitivity_not_experimental_validation`. Etapa: **Caracterización AC + visualización inicial** (no validación científica).

| `data/comparison/go_vs_ac/` | **Fase 4:** JSON/CSV/figuras comparativas descriptivas (4 configs σ×P, seeds 1–5; horizontes GO/AC no simétricos) |
| `data/sensitivity/homogeneous_temporal/` | **Etapa homogénea:** σ∈{1.0,1.5} × P∈{200…2000} × seeds 1–5 × GO+AC (**140 corridas**); provenance `homogeneous_temporal_characterization_not_experimental_validation` |

**Wiam (documentado en provenance, motor sin cambiar en esta campaña):** GO visual 7×7 px, AC ~2×2, MB 1×1; escala ~77,4 µm/px; dosis GO 0,25 g/L comunicada; **Co motor** 100 mg/L (4 mg / 0,04 L); unidad «100 mg/g» pendiente confirmar.

---

## Fase 3 — Cierre (caracterización computacional)

- GO: sensibilidad σ, steps, grid, seeds, estabilización exploratoria (70 corridas).
- AC: sensibilidad análoga en `data/sensitivity/ac/`; AC **fijo**, GO **móvil**.
- Visualización interactiva (`view`, `docs/VISUALIZACION.md`); motor headless intacto.
- **No** campaña 30/40; **no** P_ads/α/k2/Nrep definitivos; pasos ≠ minutos.

### Caracterización AC (seeds 1–5, resumen)

| σ | P | Nads μ | spread | qt μ |
|---|---|--------|--------|------|
| 1.0 | 200 | 58.4 | 18 | 116.8 |
| 1.0 | 400 | 79.8 | 19 | 159.6 |
| 1.5 | 200 | 84.2 | 12 | 168.4 |
| 1.5 | 400 | 109.2 | 20 | 218.4 |

Variabilidad AC: spread 12–20 Nads en estas configs; conservación de masa OK en estudios.

## Fase 4 — Inicio (comparación descriptiva GO vs AC)

Herramienta: `src/go_mb/compare.py` + `compare_viz.py` (solo lee JSON existentes).

Entradas por defecto:
- GO seeds: `data/sensitivity/seeds/study_sigma_steps_grid.json`
- AC seeds: `data/sensitivity/ac/seeds/study_ac_seeds.json`
- Evolución steps seed 1: GO σ=1.5 `data/sensitivity/steps/…`; GO σ=1.0 `data/sensitivity/stabilization_exploratory/…`; AC `data/sensitivity/ac/steps_sigma_*`.

**Diferencias descriptivas (Δ = media GO − media AC), mismas σ,P, 5 seeds:**

| σ | P | ΔNads | Δ% | Δqt | Δcontactos |
|---|---|-------|-----|-----|------------|
| 1.0 | 200 | +24.8 | +12.4 pp | +49.6 mg/g | +17.6 |
| 1.0 | 400 | +35.2 | +17.6 pp | +70.4 mg/g | −18.2 |
| 1.5 | 200 | +31.4 | +15.7 pp | +62.8 mg/g | −59.0 |
| 1.5 | 400 | +40.2 | +20.1 pp | +80.4 mg/g | −248.4 |

Lectura: en estas condiciones el conteo **Nads/qt** medio es mayor en GO; **contactos** no siguen la misma dirección (contacto ≠ adsorción). No se interpreta ranking de materiales.

**Decisiones pendientes:** elección humana σ/P por material; campaña Nrep; P_ads físico; no usar Langmuir como criterio.

## Homogeneización temporal GO–AC (2026-09-24)

**Motivo:** la comparación Fase 4 mezclaba horizontes distintos entre estudios GO y AC; esta etapa usa **la misma malla** para ambos materiales.

**Diseño:** σ∈{1.0, 1.5}, P∈{200, 400, 600, 800, 1000, 1500, 2000}, seeds 1–5 → 70 GO + 70 AC = **140 corridas**.

**Código:** `src/go_mb/homogeneous_temporal.py`, `homogeneous_viz.py`, CLI `homogeneous`, tests `tests/test_homogeneous_temporal.py`.

**Salidas principales:**
- Por corrida: `data/sensitivity/homogeneous_temporal/{go,ac}/` — `*_sens_grid_sigma_*_steps_*_seed_*.json` + `.csv` (serie temporal + outcomes).
- Agregados por material: `{go,ac}/study_homogeneous_temporal_*.json`, `aggregated_stats.json`.
- Comparación cruzada: `comparison/homogeneous_temporal_go_vs_ac.json`, `.csv`, figuras en `comparison/figures/` (Nads, %, qt, contactos vs P, mean±std, por σ).

**Medias cruzadas (Δ = GO − AC), alineadas con CSV homogéneo — caracterización, no ranking:**

| σ | P | ΔNads | Δ% (pp) | Δqt | Δcontactos |
|---|---|-------|---------|-----|------------|
| 1.0 | 2000 | +43.6 | +21.8 | +87.2 | −1712 |
| 1.5 | 2000 | +36.4 | +18.2 | +72.8 | −2353 |

Tendencia con P: Nads/%/qt crecen en ambos materiales; Δ en Nads/%/qt se mantiene positivo en todas las celdas de la malla; contactos medios **AC > GO** desde P≥400 en la mayoría de filas (desacople contacto–adsorción persiste). Conservación de masa OK en todas las celdas agregadas.

**No hecho en esta etapa:** campaña 30/40; elección automática σ/P; cambio de geometría Wiam (AC 2×2); alterar Co por 0,25 g/L GO.

## Alineación geométrica Wiam (2026-09-24)

Motor actual: MB 1×1 (r=0,5), GO 7×7 (r=3,5), AC 2×2 (r=1,0). Sin cambio en adsorción, masas, σ, P, Langmuir/PSO.

Piloto: `data/sensitivity/geometry_update_pilot/` — σ=1.0, P=200, seeds 1–3 (GO+AC). Comparación vs `homogeneous_temporal/` (geometría anterior). Clasificación: `geometry_alignment_pilot_not_experimental_validation`.

CLI: `python -m go_mb.cli geometry-pilot`

## Calibración temporal exploratoria (2026-09-24)

Herramienta: `src/go_mb/temporal_calibration.py` (+ viz). Lee JSON/CSV de `homogeneous_temporal_wiam_geometry/` **sin re-simular**.

Referencia PSO GO: qe=384,6 mg/g, k2=0,0002 g/(mg·min). Fracciones 10–90 % de qe_PSO; `n_sim` = primer paso con qt≥objetivo; α=t_PSO/n_sim (**exploratorio**, no definitivo). AC: fracciones sim descriptivas; **sin** t_PSO/α (PSO GO no aplicable).

Clasificación: `temporal_calibration_exploratory_not_experimental_validation`.

## Análisis protocolo final P=2000 (2026-09-24)

Herramienta: `final_protocol_analysis.py` + CLI `final-protocol`. Lee campaña Wiam + calibración temporal; **no re-simula**.

Salida: `data/analysis/final_protocol/` — agregados P=2000, comparación σ, fracciones, α GO, `candidate_final_protocol`, propuesta campaña (no ejecutada).

Clasificación: `final_protocol_analysis_descriptive_not_experimental_validation`.

---

## Hallazgos descriptivos (resultados existentes + informe A–G)

### Efecto de σ (P=400, seed=1)

Nads / % / qt crecen con σ. Contactos **no monótonos**: pico en σ=1.5 (385) y caída en σ=2.0 (259) con más adsorción final.

| σ | Nads | % | qt | Contactos |
|---|------|---|-----|-----------|
| 0.5 | 60 | 30.0 | 120 | 116 |
| 1.0 | 109 | 54.5 | 218 | 174 |
| 1.5 | 146 | 73.0 | 292 | 385 |
| 2.0 | 167 | 83.5 | 334 | 259 |

### Efecto de P (σ=1.5, seed=1)

Monótono en Nads, %, qt y contactos hasta P=600; desaceleración 400→600 vs 200→400, sin meseta clara.

### Variabilidad entre seeds (σ∈{1,1.5}, P∈{200,400})

Spread Nads ~20–27 (~10–13.5 % sobre 200 MB). σ=1.0 P=400: contactos muy dispersos (122–304) con Nads más estable.

### Estudio extendido de estabilización (medias, 5 seeds)

Incrementos medios ΔNads entre bandas de P consecutivas:

| Transición | ΔNads σ=1.0 | ΔNads σ=1.5 |
|------------|-------------|-------------|
| 200→400 | +31.8 | +33.8 |
| 400→600 | +17.6 | +15.4 |
| 600→800 | +11.6 | +8.0 |
| 800→1000 | +10.2 | +6.4 |
| 1000→1500 | +15.2 | +7.4 |
| 1500→2000 | +6.8 | +4.8 |

En P=2000: media Nads 176.4 (σ=1.0, 88.2 %) y 191.4 (σ=1.5, 95.7 %). Spread Nads σ=1.5 cae a 7 en 2000 pasos.

**Estabilización (solo descriptiva):** desaceleración fuerte hacia P≥1000–1500, sobre todo σ=1.5; **no** meseta estricta en [200, 2000]. Contactos siguen creciendo con P mientras Nads se ralentiza.

### Conservación de masa

100 % en todas las filas revisadas de sensibilidad y estudio extendido.

### Anomalías / notas (no bugs de motor detectados)

1. Contactos vs σ no monótonos (σ=1.5 vs 2.0).
2. Desacople contactos–Nads a P largos.
3. qt≈380 mg/g en algunas corridas (p. ej. seed 5, σ=1.5, P=1500): **coincidencia numérica**, no objetivo Langmuir.
4. Techo ~200 objetos MB → “saturación mecánica” hasta ~97 % adsorbidos, distinto de qe bibliográfico.

### Figuras (estudio extendido)

- `data/sensitivity/stabilization_exploratory/figures/stabilization_percent_adsorbed_vs_steps.png`
- `data/sensitivity/stabilization_exploratory/figures/stabilization_qfinal_mg_g_vs_steps.png`
- `data/sensitivity/stabilization_exploratory/figures/stabilization_n_contacts_vs_steps.png`

---

## Tooling / entorno (Windows)

- Python embebido: `.tools/python312/python.exe`
- Pytest con `pythonpath=src` en `pyproject.toml` → **50 passed**
- CLI: `-m go_mb.cli` puede fallar sin `PYTHONPATH=src` o `sys.path.insert(0,'src')`

```powershell
cd c:\Users\Yovanny\simulaci-n-nanoparticulas
$env:PYTHONPATH = "src"
.\.tools\python312\python.exe -m pytest -q
```

---

## Qué falta antes de una campaña definitiva

1. Decisión humana explícita de σ y P (zona de desaceleración interpretable, sin optimizar a qe).
2. Confirmación con ≥5 seeds en 1–2 candidatos (σ, P), no malla completa.
3. Criterio documentado de horizonte (meseta descriptiva vs % MB libre vs P fijo).
4. ~~Barrido P_ads~~ **Hecho (2026-09-25):** campaña 80 corridas en `p_ads_sensitivity/` — **no** elige P_ads definitivo; ver clasificación `p_ads_sensitivity_computational_not_physical_validation`.
5. Nrep (30/40) e IC **después** de fijar σ, P y protocolo de semilla.

---

## Cronología

### 2026-09-21 — Auditoría, sensibilidad e informe descriptivo

- Suite de ingeniería: **50 tests passed**.
- Análisis de `data/sensitivity/{sigma,steps,grid,seeds}`.
- Estudio exploratorio `stabilization_exploratory` (70 corridas; no campaña definitiva).
- Informe entregado en chat: apartados A–G (existentes, seeds, extendido, estabilización, anomalías, pendientes, información faltante).
- **No** se modificó motor ni reglas de adsorción; **no** se fijaron P_ads, k2, Nrep, α, σ ni P definitivos.

### 2026-09-21 — Creación de `memoria.md`

- Documento creado a petición del usuario para recapitulación y contexto acumulado.

### 2026-09-24 — Fase 4: comparación descriptiva GO vs AC

- Módulo `compare` + CLI `compare`; salida `data/comparison/go_vs_ac/`.
- 66 tests passed. Sin re-simulación. Clasificación: `computational_descriptive_comparison_not_experimental_validation`.

### 2026-09-22 — Caracterización AC + visualización inicial

- Sensibilidad AC en `data/sensitivity/ac/` (σ, steps, grid, seeds); script `scripts/run_ac_sensitivity_batch.py`.
- CLI: `ac sensitivity {sigma|steps|grid|plot}`, `view --material GO|AC`.
- Motor: `advance_step()` compartido con `interactive.py` (Matplotlib TkAgg, pausa/reinicio).
- AC σ=1.5 P=2000 seed 1: 155/200 MB, qt=310 mg/g (vs qe_L≈291 referencia, sin ajuste).
- **No** conclusión GO vs AC; **no** campaña 30/40.

### 2026-09-22 — Configuración AC–MB (Simulación 2)

- `ac_config()`, `MaterialKind.AC`, adsorbente **fijo** (`adsorbent_movable=False`).
- CLI: `ac run --seed --sigma --steps --out data/results/ac`.
- Langmuir AC calculado (qe≈290.9 mg/g, Ce≈27.26 mg/L); **no** fuerza simulación.
- Corrida exploratoria: seed 1, σ=1.5, P=400 → 96/200 MB, qt=192 mg/g vs qe_L≈291 mg/g.
- Inconsistencia PDF: Co 100 mg/L (4 mg/40 mL) vs posible 0.25 g/L en PDF — **confirmar con Wiam**.

### 2026-09-21 — Fase de selección humana (σ, P)

- Informe A–F: 6 configuraciones candidatas descriptivas (σ=1.0/1.5 × P=400–1500); **no** ganador automático.
- Revisión humana sugerida: **σ=1.5, P=1000** y **σ=1.5, P=800** (reproducibilidad + desaceleración); alternativa más conservadora **σ=1.0, P=800**.
- **σ=1.0, P=1000→1500:** ΔNads medio sube (15.2) vs tramo anterior — desaceleración no monótona.
- **σ=1.5, P=1500+:** riesgo de criterio 4 (pocos MB libres); P=2000 ~97 % adsorbido.
- Campaña 30/40 **no** ejecutada.

---

### 2026-09-26 — Campaña final GO vs AC (40+40)

- **80 simulaciones:** σ=1.5, P=2000, P_ads=1.0, seeds 1–40 por material, geometría Wiam.
- Provenance: `final_campaign_wiam_geometry_sigma1.5_P2000_Pads1`.
- Salida: `data/final_campaign/` (13 figuras en `figures/`, README, CSV/JSON).
- GO media Nads≈187.5 (93.7 % MB); AC media Nads≈133.2 (66.6 %). Conservación masa 80/80.
- **126 tests** pytest. Motor sin cambios en adsorción/movimiento/contacto.

#### final_campaign_figures

| Archivo | Descripción |
|---------|-------------|
| `01_nads_by_seed_go_vs_ac.png` | Nads final por seed |
| `02_qt_by_seed_go_vs_ac.png` | qt (mg/g) por seed |
| `03_percent_adsorbed_by_seed.png` | % adsorbido por seed |
| `04_nads_distribution.png` | Distribución Nads |
| `05_qt_distribution.png` | Distribución qt |
| `06_contacts_by_seed.png` | Contactos por seed |
| `07_contact_to_adsorption_efficiency.png` | Eficiencia contacto→adsorción |
| `08_qt_evolution_go_vs_steps.png` | Evolución qt GO (eje: steps) |
| `09_qt_evolution_ac_vs_steps.png` | Evolución qt AC (eje: steps) |
| `10_qt_vs_langmuir_go.png` | qt vs qe Langmuir GO (referencia) |
| `11_qt_vs_langmuir_ac.png` | qt vs qe Langmuir AC (referencia) |
| `12_pso_reference_go_minutes.png` | PSO GO (eje: minutos, referencia) |
| `13_pso_reference_ac_minutes.png` | PSO AC (eje: minutos, referencia) |

### 2026-09-26 — Referencia temporal GO/AC, S*, P_ads=0.55

- Análisis sin re-ejecutar 140 sims Wiam; PSO AC (qe=100.4, k2=0.00910) separado de GO.
- Salida: `data/analysis/final_temporal_reference/` (10 figuras, protocolo preparado **no ejecutado** 40+40).
- 20 corridas nuevas P_ads=0.55; comparación con histórico 0.5/0.75/1.0.
- S*=0.55 documentado como sticking bibliográfico; no sustituye P_ads.
- **121 tests** pytest.

### 2026-09-25 — Auditoría sensibilidad computacional P_ads

- Campaña **80 corridas** (GO+AC, σ∈{1.0,1.5}, P=2000, seeds 1–5, P_ads∈{0.25,0.5,0.75,1.0}), geometría Wiam.
- Salida: `data/sensitivity/p_ads_sensitivity/` (`study_p_ads_sensitivity.json`, `aggregated_stats.csv`, `per_run_records.csv`, `figures/`).
- Contadores nuevos en motor: `n_adsorption_events` (sin cambiar firma de `apply_adsorption`).
- **111 tests** pytest. Clasificación: `p_ads_sensitivity_computational_not_physical_validation`.
- Hallazgo descriptivo: Nads y qt suben con P_ads; eficiencia ads/contacto ~ escala con P_ads en media, pero **contactos también varían** entre niveles de P_ads (acoplamiento vía RNG/trayectoria), no solo conversión post-contacto.

---

## Espacio para próximas entradas

<!-- Plantilla:

### YYYY-MM-DD — Título breve

- Qué se hizo
- Qué se decidió (si aplica)
- Datos nuevos (rutas)
- Riesgos / bloqueos

-->
