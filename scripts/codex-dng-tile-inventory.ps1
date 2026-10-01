# Read-only, fixture-specific classic little-endian TIFF inventory.
# Not a general DNG validator or production parser.
param([Parameter(Mandatory=$true)][string]$InputDng)
$ErrorActionPreference = 'Stop'
$stream = [IO.File]::OpenRead((Resolve-Path -LiteralPath $InputDng).Path)
$reader = [IO.BinaryReader]::new($stream)
try {
    if ($reader.ReadUInt16() -ne 0x4949 -or $reader.ReadUInt16() -ne 42) {
        throw 'Only classic little-endian TIFF is supported'
    }
    $queue = [Collections.Generic.Queue[uint32]]::new()
    $queue.Enqueue($reader.ReadUInt32())
    $seen = [Collections.Generic.HashSet[uint32]]::new()
    $wanted = @(256,257,258,259,262,274,277,284,322,323,324,325,330,50719,50720,50829)
    while ($queue.Count) {
        $ifd = $queue.Dequeue()
        if (!$seen.Add($ifd)) { continue }
        $stream.Position = $ifd
        $count = $reader.ReadUInt16()
        $tags = @{}
        for ($i=0; $i -lt $count; $i++) {
            $stream.Position = [long]$ifd + 2 + 12*$i
            $tag=[int]$reader.ReadUInt16(); $type=$reader.ReadUInt16()
            $n=$reader.ReadUInt32(); $value=$reader.ReadUInt32()
            if ($tag -notin $wanted -or $type -notin @(3,4)) { continue }
            $size=4; if ($type -eq 3) { $size=2 }
            $location=[long]$ifd+2+12*$i+8
            if ([long]$n*$size -gt 4) { $location=$value }
            if ($n -gt 1000000 -or $location+[long]$n*$size -gt $stream.Length) { throw 'Invalid tag bounds' }
            $stream.Position=$location
            $values = [Collections.Generic.List[uint32]]::new()
            for ($j=0; $j -lt $n; $j++) {
                if ($type -eq 3) { $values.Add($reader.ReadUInt16()) }
                else { $values.Add($reader.ReadUInt32()) }
            }
            $tags[$tag]=$values.ToArray()
        }
        $stream.Position=[long]$ifd+2+12*$count
        $next=$reader.ReadUInt32(); if ($next) { $queue.Enqueue($next) }
        if ($tags.ContainsKey(330)) { foreach ($child in $tags[330]) { $queue.Enqueue($child) } }
        if (!$tags.ContainsKey(324)) { continue }
        foreach ($tag in $wanted | Where-Object { $_ -ne 324 -and $_ -ne 325 -and $tags.ContainsKey($_) }) {
            Write-Output "IFD=$ifd tag=$tag values=$($tags[$tag] -join ',')"
        }
        if ($tags[256][0] -ne 19200 -or $tags[257][0] -ne 12752 -or
            $tags[322][0] -ne 160 -or $tags[323][0] -ne 144 -or $tags[259][0] -ne 7) {
            throw 'Unsupported fixture tile profile'
        }
        $boxes=@(@(9260,4840,650,650),@(2040,1740,880,880),@(16380,1930,880,880),@(1690,9890,880,880),@(16180,10300,880,880))
        $selected=0; [long]$allBytes=0; [long]$selectedBytes=0
        $offsets=$tags[324]; $lengths=$tags[325]
        if ($offsets.Count -ne 10680 -or $lengths.Count -ne $offsets.Count) { throw 'Unexpected tile count' }
        for ($i=0; $i -lt $offsets.Count; $i++) {
            if ([long]$offsets[$i]+$lengths[$i] -gt $stream.Length) { throw 'Tile exceeds file' }
            $x=($i % 120)*160; $y=[math]::Floor($i/120)*144
            $needed=$false
            foreach ($box in $boxes) {
                $w=$box[2]+130; $h=$box[3]+130
                $rx=19136-($box[0]-65)-$w; $ry=12752-($box[1]-65)-$h
                if ($x -lt $rx+$w -and $x+160 -gt $rx -and $y -lt $ry+$h -and $y+144 -gt $ry) { $needed=$true }
            }
            $allBytes+=$lengths[$i]
            if ($needed) { $selected++; $selectedBytes+=$lengths[$i] }
        }
        Write-Output "tiles=$($offsets.Count) selected=$selected compressed_tile_bytes=$allBytes selected_compressed_bytes=$selectedBytes"
        # Inspect one tile's JPEG frame/scan markers; other tiles are exercised by LibRaw.
        $stream.Position=$offsets[0]
        if ($reader.ReadByte() -ne 255 -or $reader.ReadByte() -ne 216) { throw 'Missing JPEG SOI' }
        while ($true) {
            if ($reader.ReadByte() -ne 255) { throw 'Unexpected JPEG marker' }
            $marker=$reader.ReadByte()
            $length=256*$reader.ReadByte()+$reader.ReadByte()
            $payload=$reader.ReadBytes($length-2)
            if ($marker -eq 195) {
                Write-Output "first_tile_SOF3 bits=$($payload[0]) width=$(256*$payload[3]+$payload[4]) height=$(256*$payload[1]+$payload[2]) components=$($payload[5])"
            }
            if ($marker -eq 218) {
                Write-Output "first_tile_SOS predictor=$($payload[1+2*$payload[0]]) point_transform=$($payload[3+2*$payload[0]] -band 15)"
                break
            }
        }
    }
} finally { $reader.Dispose(); $stream.Dispose() }
