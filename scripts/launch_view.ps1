# Lanza la visualización 2D (GO o AC).
param(
    [ValidateSet("GO", "AC")]
    [string]$Material = "AC",
    [int]$Seed = 1,
    [double]$Sigma = 1.5,
    [int]$Steps = 400,
    [int]$IntervalMs = 30
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$env:PYTHONPATH = "src"

if ($env:VIRTUAL_ENV) {
    $py = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
} else {
    $py = (Get-Command python -ErrorAction Stop).Source
}

Write-Host "Python: $py"
Write-Host "Material=$Material seed=$Seed sigma=$Sigma steps=$Steps"
& $py -m go_mb.cli view --material $Material --seed $Seed --sigma $Sigma --steps $Steps --interval-ms $IntervalMs
