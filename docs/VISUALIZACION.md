# Visualización interactiva 2D

La vista es una **capa sobre el motor**; las métricas salen de `advance_step`, igual que en modo headless.

## Requisito importante (Windows)

Hace falta un Python **completo** con **tkinter** (incluido en el instalador oficial de [python.org](https://www.python.org/downloads/)).

El Python embebido `.tools/python312` sirve para **pytest**, pero **no** suele incluir tkinter → la ventana no abrirá.

## Paso a paso (primera vez)

1. **Instalar Python 3.12 (64-bit)** desde https://www.python.org/downloads/windows/
   - Marca **“Add python.exe to PATH”**.
   - Instalación estándar (incluye Tcl/Tk → tkinter).

2. **Abrir PowerShell** y ir al repo:
   ```powershell
   cd C:\Users\Yovanny\simulaci-n-nanoparticulas
   ```

3. **Crear entorno virtual** (recomendado):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   Si PowerShell bloquea scripts: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

4. **Instalar dependencias**:
   ```powershell
   pip install -r requirements.txt
   ```

5. **Comprobar entorno**:
   ```powershell
   .\scripts\check_view_env.ps1
   ```
   Debe terminar en `[OK] Entorno listo para visualizar.`

6. **Lanzar la simulación con ventana**:
   ```powershell
   $env:PYTHONPATH = "src"
   python -m go_mb.cli view --material AC --seed 1 --sigma 1.5 --steps 400
   ```
   Para GO móvil: `--material GO`

   Atajo:
   ```powershell
   .\scripts\launch_view.ps1 -Material AC -Seed 1 -Sigma 1.5 -Steps 400
   ```

## Uso de la ventana

- **Pausa / Reanudar**: detiene o continúa la animación (el motor avanza un paso por frame).
- **Reiniciar**: misma seed, σ y pasos; estado inicial nuevo.
- Panel de texto: paso, Nads, %, qt, contactos, m_ads, seed, σ.

Los pasos **no** son minutos.

## Sin ventana (gráficos estáticos)

Con cualquier Python que tenga matplotlib (incluso embebido):

```powershell
$env:PYTHONPATH = "src"
.\.tools\python312\python.exe -m go_mb.cli plot --input data/results/ac/ac_seed_1.json --out figures/ac
```

## Tests del motor (sin GUI)

```powershell
$env:PYTHONPATH = "src"
.\.tools\python312\python.exe -m pytest -q
```
