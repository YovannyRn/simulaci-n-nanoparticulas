# Comprueba si puedes lanzar la visualización interactiva (TkAgg + motor).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Test-PythonView([string]$PythonExe) {
    Write-Host "`n--- Probando: $PythonExe ---"
    if (-not (Test-Path $PythonExe)) {
        Write-Host "  No encontrado."
        return $false
    }
    $code = @"
import sys
sys.path.insert(0, r'$Root\src')
try:
    import tkinter
    print('  tkinter: OK')
except ImportError:
    print('  tkinter: FALTA (necesitas Python completo, no embebido)')
    raise SystemExit(1)
import numpy
import matplotlib
print('  numpy:', numpy.__version__)
print('  matplotlib:', matplotlib.__version__)
from go_mb.interactive import create_session
s = create_session('AC', seed=1, sigma_px=1.0, n_steps=2)
s.run_to_completion_headless()
print('  motor (headless): OK')
print('  LISTO para: python -m go_mb.cli view ...')
"@
    & $PythonExe -c $code
    return ($LASTEXITCODE -eq 0)
}

Write-Host "Raíz del proyecto: $Root"

$ok = $false
if ($env:VIRTUAL_ENV) {
    $venvPy = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    $ok = Test-PythonView $venvPy
}
if (-not $ok) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $ok = Test-PythonView $cmd.Source }
}
if (-not $ok) {
    $embed = Join-Path $Root ".tools\python312\python.exe"
    Write-Host "`nPython embebido (solo tests; normalmente SIN tkinter):"
    Test-PythonView $embed | Out-Null
}

if (-not $ok) {
    Write-Host "`n[ ] Entorno de visualización NO listo. Sigue docs/VISUALIZACION.md o los pasos del README."
    exit 1
}
Write-Host "`n[OK] Entorno listo para visualizar."
exit 0
