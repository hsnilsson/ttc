Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

New-Item -ItemType Directory -Force -Path 'build' | Out-Null

Write-Host 'TTC local environment is ready.'
Write-Host 'Use the Codex actions: Build TTC, Test TTC, or Run TTC Local.'
