<#
.SYNOPSIS
Build TTC for Windows using pinned, local dependencies.
.DESCRIPTION
Bootstraps w64devkit 2.10.0, LibRaw 0.21.2 and libdeflate 1.25 under
the ignored build directory. Verifies SHA256 archives before extraction.
Builds static build/ttc-simple.exe and build/TTC.exe and collects build/licenses notices.
Requires Windows PowerShell 5.1+ and Windows tar.exe. Downloads require HTTPS.
Dependencies are compiled with two jobs; image processing stays sequential.
.PARAMETER NoDownload
Fail if a required archive is missing instead of accessing the network.
.PARAMETER OpenMP
Build a separate OpenMP-enabled LibRaw. Experimental; the default is sequential.
.EXAMPLE
.\build-windows.ps1 -NoDownload
.EXAMPLE
Get-Help .\build-windows.ps1 -Detailed
#>
[CmdletBinding()]
param([switch]$NoDownload, [switch]$OpenMP)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$buildRoot = Join-Path $PSScriptRoot 'build'
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null

function Get-VerifiedArchive {
    param([string]$Name, [string]$Url, [string]$Sha256)
    $archive = Join-Path $buildRoot $Name
    if (!(Test-Path -LiteralPath $archive)) {
        if ($NoDownload) { throw "Missing archive: $archive (-NoDownload specified)." }
        $partial = "$archive.part"
        Write-Host "Downloading $Url"
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $partial
        if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash -ne $Sha256) {
            throw "SHA256 mismatch: $partial. Archive was not extracted."
        }
        Move-Item -LiteralPath $partial -Destination $archive
    }
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $Sha256) {
        throw "SHA256 mismatch: $archive. Archive was not extracted."
    }
    return $archive
}

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE." }
}

$toolchainArchive = Get-VerifiedArchive 'w64devkit.7z.exe' `
    'https://github.com/skeeto/w64devkit/releases/download/v2.10.0/w64devkit-x64-2.10.0.7z.exe' `
    '18D0A4C71A166F8401AB6305781BEC5882B40B5E06BA9807C61CB5F3B3C6325E'
$compilerRoot = Join-Path $buildRoot 'w64devkit'
$compilerBin = Join-Path $compilerRoot 'bin'
$gcc = Join-Path $compilerBin 'gcc.exe'
if (!(Test-Path -LiteralPath $gcc)) {
    $process = Start-Process -FilePath $toolchainArchive `
        -ArgumentList @('-y', ('-o"{0}"' -f $buildRoot)) `
        -WindowStyle Hidden -PassThru -Wait
    if ($process.ExitCode -ne 0) { throw "w64devkit extraction failed: $($process.ExitCode)" }
}
if (!(Test-Path -LiteralPath $gcc) -or
    (Get-Content -LiteralPath (Join-Path $compilerRoot 'VERSION.txt') -Raw).Trim() -ne '2.10.0') {
    throw 'Expected w64devkit 2.10.0 in build/w64devkit.'
}

$rawArchive = Get-VerifiedArchive 'LibRaw-0.21.2.tar.gz' `
    'https://www.libraw.org/data/LibRaw-0.21.2.tar.gz' `
    'FE7288013206854BAF6E4417D0FB63BA4ED7227BF36FFF021992671C2DD34B03'
$deflateArchive = Get-VerifiedArchive 'libdeflate.zip' `
    'https://github.com/ebiggers/libdeflate/archive/refs/tags/v1.25.zip' `
    '5CE391D1D09FF2F6B21AF492FA72BD693E416A4A682EC48C04F91E5C0E16F383'
$mode = if ($OpenMP) { 'openmp' } else { 'sequential' }
# Separate source/object trees prevent incompatible object reuse between modes.
$rawContainer = Join-Path $buildRoot "dependencies/libraw-$mode"
$rawRoot = Join-Path $rawContainer 'LibRaw-0.21.2'
$tar = Join-Path $env:SystemRoot 'System32/tar.exe'
if (!(Test-Path -LiteralPath (Join-Path $rawRoot 'Makefile.mingw'))) {
    New-Item -ItemType Directory -Force -Path $rawContainer | Out-Null
    Invoke-Checked $tar @('-xzf', $rawArchive, '-C', $rawContainer)
}
function Enable-SelectiveDngTiles {
    param([string]$LibRawRoot)
    $path = Join-Path $LibRawRoot 'src/decoders/dng.cpp'
    $source = Get-Content -LiteralPath $path -Raw
    if ($source -notmatch 'ttc_selective_dng_tile_needed') {
        $source = $source -replace '#include "../../internal/dcraw_defs.h"',
            "#include `"../../internal/dcraw_defs.h`"`r`n`r`nextern `"C`" int ttc_selective_dng_tile_needed(unsigned x, unsigned y, unsigned w, unsigned h);"
        $needle = @'
    if (tile_length < INT_MAX)
      fseek(ifp, get4(), SEEK_SET);
    if (!ljpeg_start(&jh, 0))
      break;
'@
        $replacement = @'
    if (tile_length < INT_MAX)
      fseek(ifp, get4(), SEEK_SET);
    if (tile_length < INT_MAX && !ttc_selective_dng_tile_needed(tcol, trow, tile_width, tile_length))
    {
      fseek(ifp, save + 4, SEEK_SET);
      if ((tcol += tile_width) >= raw_width)
        trow += tile_length + (tcol = 0);
      continue;
    }
    if (!ljpeg_start(&jh, 0))
      break;
'@
        if (-not $source.Contains($needle)) {
            throw "LibRaw dng.cpp did not match selective tile patch context."
        }
        $source = $source.Replace($needle, $replacement)
        Set-Content -LiteralPath $path -Value $source -Encoding UTF8
    }
}
Enable-SelectiveDngTiles $rawRoot
$deflateContainer = Join-Path $buildRoot 'dependencies'
$deflateRoot = Join-Path $deflateContainer 'libdeflate-1.25'
if (!(Test-Path -LiteralPath (Join-Path $deflateRoot 'CMakeLists.txt'))) {
    Expand-Archive -LiteralPath $deflateArchive -DestinationPath $deflateContainer -Force
}
$deflateBuild = Join-Path $buildRoot 'libdeflate-static'
$savedPath = $env:PATH
try {
    $env:PATH = "$compilerBin;$savedPath"
    $rawFlags = '-O3 -I. -w'
    $linkFlags = @()
    if ($OpenMP) {
        $rawFlags += ' -fopenmp -DLIBRAW_FORCE_OPENMP'
        $linkFlags += '-fopenmp'
    }
    Invoke-Checked (Join-Path $compilerBin 'make.exe') @(
        '-C', $rawRoot, '-f', 'Makefile.mingw', '-j2', 'library', "CFLAGS=$rawFlags")
    Invoke-Checked (Join-Path $compilerBin 'cmake.exe') @(
        '-S', $deflateRoot, '-B', $deflateBuild, '-G', 'Ninja',
        "-DCMAKE_C_COMPILER=$gcc", '-DCMAKE_BUILD_TYPE=Release',
        '-DLIBDEFLATE_BUILD_STATIC_LIB=ON', '-DLIBDEFLATE_BUILD_SHARED_LIB=OFF',
        '-DLIBDEFLATE_BUILD_GZIP=OFF', '-DLIBDEFLATE_BUILD_TESTS=OFF')
    Invoke-Checked (Join-Path $compilerBin 'cmake.exe') @(
        '--build', $deflateBuild, '--parallel', '2')
    $rawLibrary = Join-Path $rawRoot 'lib/libraw.a'
    $deflateLibrary = Join-Path $deflateBuild 'libdeflate.a'
    foreach ($library in @($rawLibrary, $deflateLibrary)) {
        if (!(Test-Path -LiteralPath $library)) { throw "Missing static library: $library" }
    }
    $executable = Join-Path $buildRoot 'ttc-simple.exe'
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'vlad_detector.h')) {
        $linkFlags += '-DTTC_VLAD_DETECTOR'
    }
    $arguments = @('-std=c99', '-O2', '-fno-strict-aliasing', '-static',
        '-DTTC_LIBDEFLATE', "-I$rawRoot", "-I$deflateRoot",
        (Join-Path $PSScriptRoot 'ttc-simple.c'), '-o', $executable,
        $rawLibrary, $deflateLibrary, '-lstdc++', '-lws2_32') + $linkFlags
    Invoke-Checked $gcc $arguments
    Invoke-Checked $gcc @('-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-static',
        '-municode', '-mwindows', '-s', (Join-Path $PSScriptRoot 'local/ttc_launcher.c'),
        '-o', (Join-Path $buildRoot 'TTC.exe'))

    $licenses = Join-Path $buildRoot 'licenses'
    New-Item -ItemType Directory -Force -Path $licenses | Out-Null
    foreach ($name in @('COPYRIGHT', 'LICENSE.LGPL', 'LICENSE.CDDL')) {
        Copy-Item -LiteralPath (Join-Path $rawRoot $name) `
            -Destination (Join-Path $licenses "LibRaw-$name")
    }
    Copy-Item -LiteralPath (Join-Path $deflateRoot 'COPYING') `
        -Destination (Join-Path $licenses 'libdeflate-COPYING')
    Copy-Item -LiteralPath (Join-Path $compilerRoot 'COPYING.MinGW-w64-runtime.txt') `
        -Destination $licenses
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'LICENSE') `
        -Destination (Join-Path $licenses 'TTC-LICENSE')
    # stb's license notices are embedded in the vendored headers.
    foreach ($header in @('stb_image.h', 'stb_image_write.h')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $header) -Destination $licenses
    }
    @"
Build dependencies: w64devkit 2.10.0; LibRaw 0.21.2 ($mode); libdeflate 1.25.
Unmodified LibRaw source: https://www.libraw.org/data/LibRaw-0.21.2.tar.gz
LibRaw offers CDDL 1.0 or LGPL 2.1; included license texts describe the terms.
GCC runtime: https://www.gnu.org/licenses/gcc-exception-3.1.en.html
Ship this notices directory with the executable and retain applicable source availability.
"@ | Set-Content -LiteralPath (Join-Path $licenses 'DEPENDENCIES.txt') -Encoding UTF8
    Invoke-Checked $executable @('--help')
    Write-Host "Built $executable (LibRaw $mode) and build/TTC.exe. Distribution notices: $licenses"
} finally {
    $env:PATH = $savedPath
}
