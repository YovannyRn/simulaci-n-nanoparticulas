# Guía para Wiam — simulación con ventana

## Cómo ejecutar (ordenador de Wiam, sin instalar Python)

1. Copie el archivo `Simulacion_GO_AC.exe` al ordenador.
2. Haga **doble clic** en `Simulacion_GO_AC.exe`.
3. Espere unos segundos. Aparece la ventana de configuración (sin ventana negra de comandos).

No hace falta instalar Python, NumPy ni Matplotlib, ni crear un entorno, ni escribir comandos.

El archivo se genera en este proyecto con `scripts\build_windows.ps1` y queda en `dist\Simulacion_GO_AC.exe`. Esa carpeta no se guarda en Git.

## Qué puede modificar

- Material: GO o AC
- σ (magnitud del movimiento, px/paso)
- Número de **pasos** (no son minutos)
- Semilla (seed)
- Intervalo de animación (milisegundos)
- P_ads, solo en **Opciones avanzadas**

**Configuración recomendada** (botón en la pantalla) restaura:

- GO, σ = 1.5, 2000 pasos, semilla 1, intervalo 35 ms, P_ads = 1.0

## Qué no debe modificar

Masas, volumen, concentración, número de partículas, tamaños, qmax, KL y las reglas del modelo aparecen en un recuadro de solo lectura. No se pueden editar.

## Importante

- Los pasos de la simulación **no son minutos**.
- P_ads = 1.0 es una **decisión computacional** del modelo, no un valor experimental universal.

## Inicio en el ordenador de desarrollo (alternativa)

1. **Primera vez solamente:** instalar Python 3.12 desde [python.org](https://www.python.org/downloads/) (marcar *Add to PATH*).
2. En la carpeta del proyecto, abrir PowerShell y ejecutar:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   .\scripts\check_view_env.ps1
   ```
3. **Cada vez que quiera ver la simulación:** hacer **doble clic** en  
   **`Iniciar_Simulacion.vbs`**  
   (en la carpeta principal del proyecto).  
   Se abre solo la ventana de configuración, **sin consola negra**.  
   `Iniciar_Simulacion.bat` hace lo mismo (llama a ese archivo).

Aparecerá una pantalla para elegir **GO** o **AC**, pasos, semilla, etc.  
**Configuración recomendada** restaura GO, σ=1.5, 2000 pasos, semilla 1 y P_ads=1.  
Pulse **Iniciar simulación**.  
Al cerrar la ventana de la animación puede configurar otra corrida sin cerrar el programa.

## Qué puede cambiar

- Material (GO o AC)
- σ (sigma)
- Número de **pasos** (no son minutos)
- Semilla (seed)
- Velocidad de animación (milisegundos entre fotogramas)

En **Opciones avanzadas** puede cambiar P_ads; es una regla del programa, no una medida de laboratorio.

## Qué no se puede cambiar desde la pantalla

Masas, volumen, C₀, número de partículas, tamaños, Langmuir, PSO, etc. Se muestran solo para información.

## Atajos alternativos

```powershell
cd C:\Users\Yovanny\simulaci-n-nanoparticulas
$env:PYTHONPATH = "src"
python -m go_mb
```

o `python -m go_mb present`

## Ventana de simulación

- **Pausa / Reanudar**
- **Reiniciar** (misma configuración, nueva trayectoria)

Los resultados numéricos son los mismos que en el modo científico sin ventana.
