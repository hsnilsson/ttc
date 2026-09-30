Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

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

$python = @(Get-Python)
$deps = Join-Path $root 'build\python-deps'
$requirements = Join-Path $root 'local\requirements-vlad.txt'

function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
    $prefix = @()
    if ($python.Length -gt 1) {
        $prefix = $python[1..($python.Length - 1)]
    }
    & $python[0] @prefix @Arguments
}

New-Item -ItemType Directory -Force -Path $deps | Out-Null

$oldErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    Invoke-Python -c "import sys; sys.path.insert(0, r'$deps'); import cv2, numpy as np; raise SystemExit(0 if cv2.__version__ == '4.11.0' and np.__version__ == '2.3.3' else 1)" 2>$null
    $dependencyCheckExitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $oldErrorActionPreference
}
if ($dependencyCheckExitCode -eq 0) {
    Write-Host 'Vlad detector dependencies already available in build\python-deps.'
    exit 0
}

Write-Host 'Installing pinned Vlad detector dependencies into build\python-deps...'
Invoke-Python -m pip install --upgrade --target $deps -r $requirements
if ($LASTEXITCODE -ne 0) {
    throw "pip install failed with exit code $LASTEXITCODE."
}

Invoke-Python -c "import sys; sys.path.insert(0, r'$deps'); import cv2, numpy as np; assert cv2.__version__ == '4.11.0' and np.__version__ == '2.3.3'"
if ($LASTEXITCODE -ne 0) {
    throw 'Installed Vlad detector dependencies could not be imported from build\python-deps.'
}

Write-Host 'Vlad detector dependencies are ready.'
