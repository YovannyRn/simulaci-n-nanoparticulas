# Reconstruye Simulacion_GO_AC.exe (solo desarrollo). Wiam no debe ejecutar este script.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Creando .venv con el Python del sistema..."
    py -3.12 -m venv (Join-Path $Root ".venv")
    if (-not (Test-Path $py)) {
        throw "No se pudo crear .venv. Instale Python 3.12."
    }
}

& $py -m pip install --upgrade pip
& $py -m pip install -r (Join-Path $Root "requirements.txt") pyinstaller

& $py -m PyInstaller --noconfirm --clean (Join-Path $Root "packaging\Simulacion_GO_AC.spec")

$exe = Join-Path $Root "dist\Simulacion_GO_AC.exe"
if (-not (Test-Path $exe)) {
    throw "No se genero $exe"
}
$mb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
Write-Host ""
Write-Host "Ejecutable: $exe"
Write-Host "Tamano: $mb MB"
Write-Host "Copie ese archivo al ordenador de Wiam. No hace falta Python."
