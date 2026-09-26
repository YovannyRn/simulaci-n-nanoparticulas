# Campaña final computacional GO vs AC

**Clasificación:** `final_campaign_wiam_geometry_sigma1.5_P2000_Pads1`  
**not_experimental_validation:** true  
**computational_final_campaign:** true

## Protocolo

| Parámetro | Valor |
|-----------|-------|
| Geometría | Wiam (MB 1×1, GO 7×7, AC 2×2) |
| MB / GO / AC | 200 / 100 / 100 unidades |
| σ | 1.5 px/paso |
| Pasos | 2000 |
| P_ads | 1.0 (regla computacional de adsorción; **no** probabilidad experimental de sticking) |
| Seeds GO | 1–40 (40 corridas) |
| Seeds AC | 1–40 (40 corridas) |
| Total | 80 simulaciones |

## Condiciones experimentales (provenance)

- T = 25 °C, pH = 6  
- MB inicial = 4 mg, adsorbente = 10 mg, V = 40 mL  
- **C₀ = 100 mg/L** (confirmado Wiam)

## Langmuir (solo referencia de equilibrio)

- **GO:** qmax=764.7, KL=0.206, qe=380.7 mg/g, Ce=4.81 mg/L  
- **AC:** qmax=412.2, KL=0.088, qe=290.9 mg/g, Ce=27.3 mg/L  

No se fuerza la simulación a alcanzar qe.

## PSO (referencia cinética por material)

- **GO:** qe_PSO=384.6 mg/g, k2=0.0002 g/(mg·min)  
- **AC:** qe_PSO=100.4 mg/g, k2=0.00910 g/(mg·min)  

No usar PSO GO para AC ni viceversa. **Los pasos de simulación no son minutos.**

## S* = 0.55 (contexto bibliográfico)

Referencia de sticking probability en un sistema AC–MB relacionado (Sha'Ato, 2021).  
**No sustituye P_ads=1.0** en esta campaña.

## α (escala temporal)

Exploratorio (`exploratory temporal scale`). No modifica el motor.

## Métricas por corrida

material, seed, σ, steps, P_ads, T, pH, masas, C₀, Nads, % adsorbido, qt, contactos, eventos adsorción, eficiencia contacto→adsorción, conservación de masa, provenance.

## Estadística

Por material: mean, median, std, min, max, CV, percentiles 25/75; IC 95% cuando aplica (`stats.py`).

## Limitaciones

- Modelo 2D discreto; no validación experimental.  
- Comparación GO/AC descriptiva, sin causalidad demostrada.  
- P_ads=1 es decisión computacional provisional, no dato físico.

## final_campaign_figures

- **01_nads_by_seed_go_vs_ac.png** — Nads final por seed (GO y AC).
- **02_qt_by_seed_go_vs_ac.png** — qt final (mg/g) por seed.
- **03_percent_adsorbed_by_seed.png** — % adsorbido por seed.
- **04_nads_distribution.png** — Histograma Nads GO vs AC.
- **05_qt_distribution.png** — Histograma qt GO vs AC.
- **06_contacts_by_seed.png** — Contactos por seed.
- **07_contact_to_adsorption_efficiency.png** — Eficiencia por seed.
- **08_qt_evolution_go_vs_steps.png** — Evolución qt vs steps — GO; eje temporal en pasos, no minutos.
- **09_qt_evolution_ac_vs_steps.png** — Evolución qt vs steps — AC; eje temporal en pasos, no minutos.
- **10_qt_vs_langmuir_go.png** — qt simulado vs qe Langmuir GO.
- **11_qt_vs_langmuir_ac.png** — qt simulado vs qe Langmuir AC.
- **12_pso_reference_go_minutes.png** — Curva PSO GO en minutos (referencia externa).
- **13_pso_reference_ac_minutes.png** — Curva PSO AC en minutos (referencia externa).
