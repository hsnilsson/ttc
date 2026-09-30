Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

function Get-Python {
    $candidates = @()
    $codexPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $codexPython) {
        $candidates += ,@($codexPython)
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $candidates += ,@($python.Source)
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        $candidates += ,@($py.Source, '-3.11')
        $candidates += ,@($py.Source, '-3')
    }

    foreach ($candidate in $candidates) {
        $oldErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $prefix = @()
            if ($candidate.Length -gt 1) {
                $prefix = $candidate[1..($candidate.Length - 1)]
            }
            & $candidate[0] @prefix -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } finally {
            $ErrorActionPreference = $oldErrorActionPreference
        }
    }

    throw 'Python 3.11+ was not found. Install Python or run this from a Codex desktop environment with bundled Python.'
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

Write-Host 'Ensuring Vlad detector dependencies...'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\scripts\codex-ensure-vlad-deps.ps1'
if ($LASTEXITCODE -ne 0) {
    throw "Vlad detector dependency setup failed with exit code $LASTEXITCODE."
}

$python = @(Get-Python)
$pythonPrefix = @()
if ($python.Length -gt 1) {
    $pythonPrefix = $python[1..($python.Length - 1)]
}
Write-Host 'Starting TTC local service. Use the URL printed by the service below.'
Write-Host 'Keep this terminal running while using the browser UI.'

& $python[0] @pythonPrefix local\ttc_local.py serve --engine build\ttc-simple.exe
