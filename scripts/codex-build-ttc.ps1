Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

Write-Host 'Building TTC native executable...'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\build-windows.ps1'
if ($LASTEXITCODE -ne 0) {
    throw "build-windows.ps1 failed with exit code $LASTEXITCODE."
}

if (-not (Test-Path -LiteralPath '.\build\ttc-simple.exe')) {
    throw 'Build completed without producing build\ttc-simple.exe.'
}

Write-Host 'Built build\ttc-simple.exe.'
