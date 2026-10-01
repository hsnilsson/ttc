# Selective lossless DNG tile unpacking

Research on 2026-10-01, TTC base `cf417f4`, Windows, existing w64devkit GCC
16.2.0, sequential LibRaw 0.21.2, `-O2`. Production behavior is unchanged.
The standalone probe links an experimental decoder object before the existing
static LibRaw archive. It modifies no dependency source, library, or input file.

## Result

**Feasible for the two tested full-color pixel-shift DNGs.** A minimal skip hook
in `lossless_dng_load_raw()` decoded only the tiles intersecting five padded ROI
windows. The unpacked samples and rendered RGB8 windows matched a full unpack
and full-frame render exactly. All five windows include 65 pixels of context
on each side: 32 reference context + 32 maximum search + 1 smoothing pixel.

For each fixture, 18,755,200 16-bit channel values (including the zero fourth
channel) and 14,066,400 RGB8 bytes are compared. Zero differences were observed.
This covers the complete padded windows, not just a hash or the ROI cores.
Identical RGB inputs preserve the existing deterministic metrics and tracking
calculations when global coordinates/bounds/sample placement are retained.
The probe does **not** execute an end-to-end analysis CSV, PNG, or stack tracking
comparison. It does not establish correctness for arbitrary DNGs.

| Input / run | Full unpack | Selective unpack | Full open + unpack + RGB render | Selective open + unpack + five RGB renders |
| --- | ---: | ---: | ---: | ---: |
| 3982 initial | 11.155 s | 0.292 s | 13.993 s | 0.362 s |
| 3982 repeat | 10.948 s | 0.302 s | 13.550 s | 0.371 s |
| 3982 final source | 11.072 s | 0.299 s | 13.592 s | 0.366 s |
| 4350 | 10.995 s | 0.296 s | 13.829 s | 0.367 s |

These are exploratory sequential runs, warm filesystem cache, on this machine,
without cache flushing or isolation from other workloads. They exclude process
startup, close/free time, comparison loops, metric computation, tracking, report
encoding, overview and detection/export work. The control uses the same decoder
object with the hook accepting all tiles; the original tile decoding body is
unchanged. A fresh selective-only process took 0.381 s on 3982. It performs no
equivalence comparison (`compared=0`); comparison mode is the correctness check.

The observed unpack reduction is about **36-38x**, and decode/render reduction
about **37-39x**. The equal-cost tile-count ceiling is 10680/274 = **38.98x**
for unpack alone. It is an estimate, not a hard bound: tile costs differ.
Compressed-payload ratio suggests about 40x less JPEG data. Existing full-unpack
cropbox loading takes roughly 11-13 seconds, so selective unpack addresses its
dominant remaining stage. Whole-application improvement will be lower whenever
tracking, encoding, reference overview, detection, or full export dominate.

## Actual TIFF/JPEG metadata and coordinates

Read-only inventory (`scripts/codex-dng-tile-inventory.ps1`) found the same RAW
IFD at offset 164914 in both fixtures. Classic little-endian TIFF, not BigTIFF:

| Tag | Meaning | Observed value |
| --- | --- | --- |
| 256 / 257 | Stored dimensions | 19200 x 12752 |
| 258 | BitsPerSample | 16,16,16 |
| 259 | Compression | 7 (JPEG); first tile is SOF3 lossless Huffman JPEG |
| 262 | PhotometricInterpretation | 34892 (LinearRaw) |
| 277 / 284 | Samples / planar configuration | 3 / 1 (chunky/interleaved) |
| 322 / 323 | Tile size | 160 x 144 |
| 324 / 325 | Tile offsets / byte counts | 10680 entries each |
| 50829 | ActiveArea (top,left,bottom,right) | 0,0,12752,19136 |

There are 120 columns and 89 rows; the last row is partial (80 active stored
rows). Tiles are row-major. LibRaw reports flip 3 (180 degrees), zero margins,
active/output size 19136 x 12752, filters=0, colors=3, and `color4_image` storage.
The inventory's RAW IFD does not contain an Orientation tag; use LibRaw's resolved
orientation, not an assumption that orientation must appear in that IFD.
The first tile's SOF3 is 16-bit, 160 x 144, three components; SOS predictor is 1
and point transform is 0. Only the first header was independently inspected;
LibRaw exercises the actual JPEG decoders for all selected/control tiles.

| Input | All compressed RAW tile bytes | Selected compressed tile bytes | Tiles |
| --- | ---: | ---: | ---: |
| `_DSC3982-_DSC3997.dng` | 639106093 | 15921846 (2.491%) | 274 / 10680 |
| `_DSC4350-_DSC4365.dng` | 610305119 | 15225193 (2.495%) | 274 / 10680 |

For an oriented half-open rectangle `(x,y,w,h)`, inverse flip 3 in the **active**
image: `(19136-x-w, 12752-y-h, w,h)`. Then add `left_margin,top_margin` to reach
stored coordinates. Use strict half-open intersection against stored tile
rectangles and take the union, decoding an overlapping tile only once. Apply
padding/clipping in original global oriented coordinates before mapping. Do not
use 19200 in the flip formula and do not silently apply DNG DefaultCrop instead
of TTC/LibRaw's active-image policy. The probe intentionally rejects other active
sizes, orientation, filters, colors and decoder identities; inventory also
rejects other tile geometry/compression and checks offset/length bounds.

For future flip 0 use the identity; flips containing axis transpose must swap
width/height and map rectangle endpoints as well as the origin. Implement and
test all eight LibRaw flip bit combinations before generalizing. DNG opcodes,
rotated sensors, scaling/default crop and alternate RAW IFD/frame selection can
require additional transforms; keep a full-decoder fallback.

## Why skipping works and why naive parallelization does not

Inspected the existing LibRaw sources under
`build/dependencies/libraw-sequential/LibRaw-0.21.2` in the primary checkout:

- `src/metadata/tiff.cpp` handles TileWidth/Length, offsets/counts, ActiveArea,
  SubIFDs and chooses the RAW IFD. For this classic TIFF path, `data_offset`
  addresses a four-byte tile-offset table, not the first tile's pixel bytes.
- `src/decoders/dng.cpp:lossless_dng_load_raw` saves the table cursor, reads one
  offset, seeks to that tile, calls `ljpeg_start`, decodes rows, returns to
  `save+4`, advances tile coordinates and frees JPEG state. `adobe_copy_pixel`
  preserves LibRaw's per-sample curve mapping and right/bottom bounds handling.
- `src/decoders/decoders_dcraw.cpp:ljpeg_start/ljpeg_row_unrolled` constructs fresh
  JPEG/Huffman/row state for each stream and initializes predictors and the
  bitreader at row zero. JPEG predictors depend on earlier samples **inside
  the same tile**. Decode whole selected tiles; skipping arbitrary scanline
  prefixes or subrectangles is not equivalent.
- `src/decoders/unpack.cpp` allocates this full-color Adobe-copy buffer with
  `calloc`, keeps original decoder identity/flags, and attaches `color4_image`.
  `crop_masked_pixels()` is only called for `raw_image`, not these full-color
  buffers. Black normalization and metadata snapshots remain unchanged.
- `src/preprocessing/raw2image.cpp:raw2image_ex` restores RAW metadata and copies
  cropbox pixels using the raw pitch and margins. Each selected padded window
  is initialized even though skipped tiles remain zero.
- `src/postprocessing/dcraw_process.cpp` and
  `src/postprocessing/postprocessing_utils_dcrdefs.cpp:scale_colors` explain the
  rendering dependencies. TTC disables auto brightness/maximum adjustment,
  uses valid metadata camera WB, and these fixtures require no demosaicing.

The hook skips before `ljpeg_start`, advances the table cursor by four bytes,
advances coordinates exactly like the original path, and continues. Thus it
avoids seeks/reads/JPEG decompression for skipped tiles but still visits all
10680 offset entries. Decoder identity stays `lossless_dng_load_raw()` so
LibRaw's decoder flags and allocation decisions stay intact.

The current input cursor, `getbits/gethuff` TLS state, `zero_after_ff`, error and
cancellation handling, `shot_select`, curve, and output pointers are shared
within a LibRaw instance. Adding OpenMP to this loop is unsafe even though
JPEG streams are independent. A parallel implementation needs independent,
bounded per-tile input/bitstream/predictor/error contexts and immutable shared
calibration data. Start with serial selective decoding: it already removes
nearly all unnecessary work. The probe hook uses process globals and is
explicitly single-threaded; production must use per-instance state.

## Correctness and integration limits

1. **Full-color profile only initially.** CFA demosaic neighborhoods and phase,
   X-Trans alignment, algorithm tile boundaries, zero repair, denoising, median
   filters, chromatic correction, highlight recovery and opcodes can depend on
   pixels beyond the measurement/tracking windows. A guessed halo is insufficient
   proof. Reject unsupported profiles/settings and fall back to full unpack.
2. **Global calibration.** The tested files have black=0, maximum=14848, valid
   camera multipliers, fixed brightness and no maximum adjustment. Missing WB
   can trigger content-derived auto WB even when `use_auto_wb=0`. Other formats
   may calculate black from masked pixels or normalize floating RAW globally.
   Either preserve necessary global samples/statistics or reject the profile.
3. **Sparse buffer semantics.** Unselected pixels are zero here because of
   `calloc`; they are not valid decoded pixels. Never export a full frame, run
   full-frame processing, or create an overview from that buffer. Retain a
   coverage contract and enforce that every processing window is covered.
4. **Memory.** This experiment retains the full approximately 1.95 GB virtual
   RAW allocation (19200 x (12752+8) x 8 bytes). Skipping should reduce touched
   pages, but working set/RSS was not measured. Compact tile storage and a new
   raw2image adapter are separate work; changing public image dimensions to
   deceive unpacking would break offsets, stride, calibration and orientation.
5. **File variants and errors.** Compression=7 alone does not prove the supported
   SOF3 layout. Validate IFD, sample packing, JPEG component/geometry/precision,
   table count/type/bounds and actual decoder choice. Strips, single tiles,
   SOF1, lossy JPEG, floating/deflate, VC5, BigTIFF and other backend engines need
   separate paths. A full-sized strip may offer no useful selectivity. Selected
   tile errors must fail explicitly. Skipping tiles also skips detection of
   corrupt JPEG payloads outside the requested regions; do not claim whole-file
   integrity validation. Prefer bounded tile streams using TileByteCounts.
6. **Maintenance/licensing.** Use an opt-in pinned LibRaw patch/extension with
   per-instance rectangle selection, explicit decoder support gates and full
   fallback. The build script generates modified upstream source in ignored
   `build/`, retains its license header, and leaves installed dependencies intact.
   Any distribution of a patched library must follow its chosen LGPL/CDDL terms.

## Concrete implementation plan

1. Add per-LibRaw-instance stored-coordinate selection windows/coverage, consumed
   only by the validated tiled SOF3 full-color decoder; include metadata and
   backend eligibility checks. Preserve the existing tile decode body, stream
   resets, curve, flags, progress/cancel, exception cleanup and metadata restore.
2. Convert TTC's oriented ROIs to unioned padded stored rectangles; unpack once,
   process each cropbox, retain origins/full dimensions. Adapt ROI tracking to
   original global sample grid and bounds. Keep camera WB/gamma/color settings
   exactly as current `load_image`. Version the render/cache policy.
3. Keep the reference frame's overview as a full decode initially, or reuse a
   verified full-frame preview with explicit dimensions/orientation and visual
   policy. The local detection preview and optional aligned export still need
   their existing complete-frame workflow. Subsequent ROI-only frames can use
   the selective path. For a 16-frame stack with one full reference and fifteen
   0.37 s selective loads, modeled load/render time is approximately 19.5 s
   instead of 224 s (about 11.5x); this is not a measured application benchmark.
4. Validate full samples, every exported crop byte, all CSV metrics and all
   tracking statuses/shifts across the actual stack. Include overlapping and
   boundary windows, nonzero margins, orientation variants, alternate exposure
   and WB, errors/cancellation and unsupported-format fallback. Test Windows and
   Linux. Use isolated decoder backend selection so RawSpeed/DNG SDK cannot
   silently bypass the selection contract.
5. Benchmark cold/warm cache and full end-to-end wall time/working set before
   deciding whether to implement compact sparse buffers or per-tile concurrency.

## Reproduce

From the task checkout in PowerShell (dependencies can be elsewhere/read-only):

```powershell
$raw = 'D:/camera scanning/vlads/ttc/build/dependencies/libraw-sequential/LibRaw-0.21.2'
$compiler = 'D:/camera scanning/vlads/ttc/build/w64devkit/bin/g++.exe'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/codex-selective-dng-probe.ps1 -LibRawRoot $raw -Compiler $compiler
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/codex-dng-tile-inventory.ps1 -InputDng 'D:/camera scanning/vlads4/_DSC3982-_DSC3997.dng'
build/selective-dng-probe.exe 'D:/camera scanning/vlads4/_DSC3982-_DSC3997.dng'
build/selective-dng-probe.exe 'D:/camera scanning/vlads4/_DSC4350-_DSC4365.dng'
build/selective-dng-probe.exe 'D:/camera scanning/vlads4/_DSC3982-_DSC3997.dng' --selective-only
```

Both fixture comparisons passed, including a repeat on 3982; independent TIFF
inventory passed on both. Build uses `-Wall -Wextra`; the only decoder compilation
warning is upstream MSVC `#pragma comment` ignored by GCC. Probe source has no
warnings. Missing argument/file error checks return 1. `git diff --check` passed.
No production files were edited, so the production suite was not rerun. No Linux,
new camera/compression profile, malformed tile/cancel matrix, peak-memory,
cold-cache, or end-to-end stack checks are claimed. Generated sources/objects,
executables and raw logs stay in ignored `build/`.
