param(
    [Parameter(Mandatory=$true)][string]$LibRawRoot,
    [Parameter(Mandatory=$true)][string]$Compiler
)
$ErrorActionPreference = 'Stop'
$LibRawRoot = (Resolve-Path -LiteralPath $LibRawRoot).Path.Replace('\','/')
New-Item -ItemType Directory -Force build | Out-Null
$source = Get-Content -Raw -LiteralPath "$LibRawRoot/src/decoders/dng.cpp"
$anchor = "    save = ftell(ifp);"
if (($source.Split(@($anchor), [StringSplitOptions]::None).Length - 1) -ne 1) {
    throw 'Unexpected decoder source: patch anchor must occur once'
}
$source = $source.Replace('#include "../../internal/dcraw_defs.h"',
    "#include `"$LibRawRoot/internal/dcraw_defs.h`"`nextern bool ttc_probe_tile_needed(unsigned, unsigned, unsigned, unsigned);")
$source = $source.Replace($anchor, @'
    save = ftell(ifp);
    // Experimental hook: skip an entire independently compressed tile.
    if (tile_length < INT_MAX &&
        !ttc_probe_tile_needed(tcol, trow, tile_width, tile_length))
    {
      fseek(ifp, save + 4, SEEK_SET);
      if ((tcol += tile_width) >= raw_width)
        trow += tile_length + (tcol = 0);
      continue;
    }
'@)
Set-Content -LiteralPath build/selective-dng.cpp -Value $source -Encoding ascii
& $Compiler -O2 -Wall -Wextra -fno-strict-aliasing "-I$LibRawRoot" -c build/selective-dng.cpp -o build/selective-dng.o
if ($LASTEXITCODE) { throw 'Decoder compilation failed' }
& $Compiler -std=c++11 -O2 -Wall -Wextra -fno-strict-aliasing "-I$LibRawRoot" tests/selective_dng_probe.cpp build/selective-dng.o "$LibRawRoot/lib/libraw.a" -lws2_32 -o build/selective-dng-probe.exe
if ($LASTEXITCODE) { throw 'Probe linking failed' }
