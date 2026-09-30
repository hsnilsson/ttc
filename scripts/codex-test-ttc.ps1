Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

function Get-Python {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            & $py.Source -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return @($py.Source, '-3')
            }
        } catch {
        }
    }

    $codexPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $codexPython) {
        return $codexPython
    }

    throw 'Python 3.10+ was not found. Install Python or run this from a Codex desktop environment with bundled Python.'
}

if (-not (Test-Path -LiteralPath '.\build\ttc-simple.exe')) {
    Write-Host 'build\ttc-simple.exe is missing; building first.'
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\scripts\codex-build-ttc.ps1'
    if ($LASTEXITCODE -ne 0) {
        throw "Build action failed with exit code $LASTEXITCODE."
    }
    if (-not (Test-Path -LiteralPath '.\build\ttc-simple.exe')) {
        throw 'Build action did not produce build\ttc-simple.exe.'
    }
}

$python = Get-Python
Write-Host 'Running Python service checks...'
if ($python -is [array]) {
    & $python[0] $python[1] -B tests\local_checks.py
} else {
    & $python -B tests\local_checks.py
}

Write-Host 'Running viewer tests...'
node --test web\tests\viewer.test.cjs
if ($LASTEXITCODE -ne 0) {
    throw "Node viewer tests failed with exit code $LASTEXITCODE."
}
node --check web\viewer.js
if ($LASTEXITCODE -ne 0) {
    throw "Node syntax check failed with exit code $LASTEXITCODE."
}

Write-Host 'Checking whitespace in tracked diffs...'
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check failed with exit code $LASTEXITCODE."
}

Write-Host 'TTC checks passed.'
