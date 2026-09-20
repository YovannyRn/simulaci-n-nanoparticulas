# Parámetros PENDIENTE

El motor **no inventa** estos valores como si procedieran de literatura. Cuando un ensayo necesita un número para ejecutarse, se inyecta por CLI o test y se persiste con estado `PENDIENTE` o `DECISIÓN COMPUTACIONAL`.

| Símbolo | Qué falta | Cómo lo trata el código |
|---|---|---|
| `P_ads` | No hay probabilidad de adsorción por choque en literatura | Regla operativa por defecto: adsorber un objeto MB entero **solo si** queda capacidad ≥ 0,02 mg. No se calibra a qe = 380,7 mg/g. Se puede inyectar `p_ads` explícito para experimentos, siempre etiquetado. |
| `D` / `σ` | Escala browniana sin valor | Obligatorio inyectar `--sigma` (px/paso). |
| `P` | Número de pasos sin valor | Obligatorio inyectar `--steps`. |
| `k2` | 0,0002 (ejemplo) vs 0,001 (tabla) | Se guardan ambos. La curva PSO de referencia usa el valor del ejemplo (0,0002) porque es el único que cierra el cálculo a 10 min = 1,672 mg. |
| `Nrep` | 30 vs 40 | Obligatorio inyectar `--n-rep`. |
| `rMB`, `rA` | Círculos sobre cuadrados 5×5 y 7×7 | Decisión computacional documentada: círculo **inscrito**, r = lado/2 (2,5 y 3,5 px). |
| CA | Sin qmax, KL, N, tamaño | Sistema CA no se ejecuta. |
| `α` | min/paso | Solo se estima a posteriori `t_PSO / n_sim` si hay datos. No se usa en el motor. |

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
