# Parámetros PENDIENTE

El motor **no inventa** estos valores como si procedieran de literatura. Cuando un ensayo necesita un número para ejecutarse, se inyecta por CLI o test y se persiste con estado `PENDIENTE` o `DECISIÓN COMPUTACIONAL`.

| Símbolo | Qué falta | Cómo lo trata el código |
|---|---|---|
| `P_ads` | No hay probabilidad de adsorción por choque en literatura. **Sigue PENDIENTE** como dato físico/bibliográfico. | **DECISIÓN COMPUTACIONAL PROVISIONAL** (no literatura): tras contacto geométrico, si `cap_restante ≥ peso_MB` (0,02 mg) se adsorbe el objeto entero. Equivale a **P_ads = 1**. No se calibra a qe = 380,7 mg/g. Se puede inyectar `--p-ads` en (0,1) (Bernoulli etiquetado) o 0. `None` y `1.0` no extraen RNG extra. **Auditoría 2026-09-25:** barrido {0.25,0.5,0.75,1.0} × σ × seeds en `data/sensitivity/p_ads_sensitivity/` — clasificación `p_ads_sensitivity_computational_not_physical_validation`; **no** elige P_ads definitivo. |
| `D` / `σ` | Escala browniana sin valor | Obligatorio inyectar `--sigma` (px/paso). Es **parámetro de ejecución**, no valor científico definitivo. `1.5` en demos/tests es prueba, no D de [1]/[2]. |
| `P` | Número de pasos sin valor | Obligatorio inyectar `--steps`. Es **parámetro de ejecución**, no horizonte físico. `400` en demos/tests es prueba, no P del PDF. |
| `k2` | 0,0002 (ejemplo) vs 0,001 (tabla) | Se guardan ambos. La curva PSO de referencia usa el valor del ejemplo (0,0002) porque es el único que cierra el cálculo a 10 min = 1,672 mg. |
| `Nrep` | 30 vs 40 | **Campaña final ejecutada:** 40 seeds GO + 40 seeds AC en `data/final_campaign/` (σ=1.5, P=2000, P_ads=1). Para otros diseños, inyectar `--n-rep`. |
| `rMB`, `rA` | Círculos inscritos Wiam | MB 1×1 → r=0,5 px; GO 7×7 → r=3,5 px; AC 2×2 → r=1,0 px. Campañas previas (p. ej. `homogeneous_temporal/`) usaron MB 5×5 y adsorbente 7×7. |
| CA | Sin qmax, KL, N, tamaño | Sistema CA no se ejecuta. |
| `α` | min/paso | **Exploratorio** — recalibrado GO **y** AC con PSO confirmado (qe/k2 por material) en `data/analysis/final_temporal_reference/` (`temporal_calibration_go_ac_with_bibliographic_sticking_reference`). **No** convertir steps↔minutos; **no** α definitivo. |
| `S*` (AC) | 0,55 (Sha'Ato 2021) | **Referencia bibliográfica contextual** para un sistema AC–MB relacionado; **≠ P_ads**. Sensibilidad computacional `P_ads=0.55` en la misma carpeta (`p_ads_055_bibliographic_reference_sensitivity_not_physical_validation`). |

**Demostración computacional (no validación experimental):** una corrida con `--seed 1 --sigma 1.5 --steps 400` produjó **146/200** MB adsorbidos. Ese recuento etiqueta una ejecución del motor; no valida el experimento de Ortiz ni fija qe.

**Etapa de sensibilidad:** usar `python -m go_mb.cli sensitivity {sigma|steps|grid}` para barridos de σ y/o pasos. Los resultados se clasifican como `computational_sensitivity_not_experimental_validation`. No sustituye la elección futura de D/σ ni P.

Otras hipótesis operativas (no son literatura):

- Rebote: reflexión del solapamiento en cada eje y recorte al recinto.
- Orden de paso: mover MB libres y GO → detectar todos los contactos → adsorber.
- Un MB que toca varios GO se adsorben al GO **más cercano** con capacidad (empate: índice menor).
- Capacidad fraccionaria: no se adsorben 0,01647 mg sueltos; solo objetos enteros de 0,02 mg.
- GO saturado sigue moviéndose.
- Colocación inicial aleatoria sin solape de cuadrados (rechazo).
- `qt = m_adsorbed / m_GO` (mg/g).
- Se registran **las dos** concentraciones: `C_pdf = m_adsorbed / V` (fórmula del PDF) y `C_remaining = m_free / V` (concentración restante).
- Porcentajes 10…100 % se calculan respecto a `qe_L` y también respecto a `qfinal` de la corrida.
- Velocidad simulada: `Δqt / Δpaso` y `qfinal / n_steps`.
