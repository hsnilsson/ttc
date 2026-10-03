# Publish the public guide, explicitly selected screenshots and example demo.
[CmdletBinding()]
param([string]$Destination = 'build/pages')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$output = Join-Path $root $Destination
if (Test-Path -LiteralPath $output) { throw "Use a fresh Pages destination: $output" }
New-Item -ItemType Directory -Path (Join-Path $output 'images') -Force | Out-Null
foreach ($name in @('index.html', 'style.css')) {
    Copy-Item -LiteralPath (Join-Path $root "site/$name") -Destination $output
}
foreach ($name in @('sharpness-map.png', 'vlad-roi-overlay.jpg')) {
    Copy-Item -LiteralPath (Join-Path $root "docs/screenshots/$name") -Destination (Join-Path $output 'images')
}
$demo = Join-Path $output 'demo'
New-Item -ItemType Directory -Path $demo | Out-Null
foreach ($name in @('index.html', 'demo.css', 'demo.js', 'sample.json')) {
    Copy-Item -LiteralPath (Join-Path $root "site/demo/$name") -Destination $demo
}
foreach ($name in @('viewer.js', 'viewer.css', 'report.html')) {
    Copy-Item -LiteralPath (Join-Path $root "web/$name") -Destination $demo
}
Copy-Item -LiteralPath (Join-Path $root 'site/demo/assets') -Destination $demo -Recurse
New-Item -ItemType File -Path (Join-Path $output '.nojekyll') | Out-Null
