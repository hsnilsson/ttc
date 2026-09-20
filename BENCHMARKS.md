# Full-resolution performance report

Measured 2026-09-21 on Windows, AMD Ryzen 9 3950X (16 cores/32 logical processors), 31.91 GiB usable RAM,
w64devkit 2.10.0 / GCC 16.2.0, `-O2`, sequential LibRaw 0.21.2, libdeflate 1.25.
Inputs under `D:\camera scanning\vlads4` were read-only. No preview decoding,
downsampling, altered crop coordinates, or lossy encoding was used.

## Correct baseline

The original native loader at `66803a8` copied 16-bit raw bytes into an RGB8
buffer without color rendering. Its timing would not be a valid comparison.
This is not a comparison with the Python release. The baseline is corrected decoder commit `0990441`, with the original compositor,
stb PNG compressor, and full RGB copy. Both benchmark builds linked the same
pre-existing `C:\libraw\lib\libraw.a` to isolate application/encoder changes.
The reproducible build also builds LibRaw from pinned upstream source.

Rendering: full size, daylight WB, sRGB primaries, LibRaw default gamma/demosaic,
metadata orientation, brightness 1, no auto WB/brightness, and no content-based
maximum adjustment. The RGB8 policy is explicit, not a linear RAW export.

## Repeated measurements

Input `_DSC3982-_DSC3997.dng` (647,089,698 bytes), rendered **19,136 × 12,752**;
composite **12,752 × 12,752**. Six alternating baseline/optimized runs, three per
configuration, with other TTC image tasks and dependency compilation stopped.
Warm filesystem cache; no cache flushing. Same source file and output volume.

| Run | Version | Load (s) | Composite + PNG (s) | Phase sum (s) | Peak working set (MiB) |
|---|---|---:|---:|---:|---:|
| 1 | Correct baseline | 14.303 | 17.891 | 32.194 | 5133.64 |
| 1 | Optimized | 13.581 | 9.088 | 22.669 | 4435.55 |
| 2 | Correct baseline | 13.767 | 18.237 | 32.004 | 5131.84 |
| 2 | Optimized | 13.802 | 9.129 | 22.932 | 4433.73 |
| 3 | Correct baseline | 14.343 | 18.008 | 32.351 | 5131.86 |
| 3 | Optimized | 13.335 | 8.842 | 22.178 | 4433.71 |

Median phase sum: **32.194 → 22.669 seconds**, **29.6% less time / 1.42× throughput**.
Median composite phase: **18.008 → 9.088 seconds**, **49.5% less time**.
Median peak working set: **5131.86 → 4433.73 MiB**, **698 MiB / 13.6% lower**.
Output size: **174,170,946 → 110,435,180 bytes**, **36.6% smaller**.

Every run matched full-image FNV-1a-64 hashes:

- Source RGB: `5c983bb16ed77774`.
- Decoded composite RGB: `88382fffe249be15`.

The harness hashes every RGB byte, with dimensions checked, outside timed
sections. These are regression checks, not cryptographic identity proofs.
The reported sum excludes process startup, verification hashing, and rereading
PNG output; it includes source read/decode and composite allocation/copy/encode/write.
Peak working set is captured before PNG verification. See
[tests/README.md](tests/README.md) for executable commands and harness details.

## Changes and decisions

- Use LibRaw's independently owned RGB bitmap directly and release it through
  `free_image`; eliminate a redundant 732 MB full-image allocation/copy.
  `Image` has a trailing `allocation` owner pointer. Consumers must use
  `free_image`, not `free(image->data)`. Zero-initialize caller-created Images.
- Copy complete crop rows instead of per-pixel three-byte copies, retaining the
  original layout including black padding.
- Use optional libdeflate at level 6 through stb's supported zlib callback.
  Default build enables it. Adaptive PNG filtering is unchanged. The stb-only
  fallback remains available for manual builds without `TTC_LIBDEFLATE`.
- A fixed Sub PNG filter was also tried: 6.0 s versus 9.1 s adaptive with
  libdeflate, but increased output from 110 MB to 119 MB on this fixture. Retained
  adaptive filtering for the default; this was exploratory, not the repeated result.
- Keep file processing sequential. The old parallel commit `2d480f9` submitted
  up to CPU-count-minus-one images without per-file memory budgeting, could skip
  high-memory inputs, and changed demosaic quality/orientation. The revert
  `10cafaf` records no reason, so these are risks, not a proven explanation.

## Build and limitations

`build-windows.ps1` pins compiler and dependency archives by SHA256, builds all
libraries locally, and statically links `build/ttc-simple.exe`. It supports offline
archive reuse (`-NoDownload`) and keeps system/coordinator installations untouched.
Dependency notices are collected under `build/licenses`.

The optional `-OpenMP` build is experimental and is separate from the measured
sequential decoder configuration. LibRaw on MinGW needs both `-fopenmp` and
`LIBRAW_FORCE_OPENMP`; merely passing `-fopenmp` does not enable its loops.
Image-level concurrent decodes remain disabled.

Results are from this machine and these fixtures, not a full 16-file throughput
claim. Several GB of memory remain necessary. Other camera models, compressed
DNG variants, and Linux were not comprehensively tested. LibRaw active dimensions
are preserved; applying the DNG DefaultCrop rectangle is a separate policy.

Questions for tomorrow: whether a separate camera-WB viewing mode is wanted,
and whether quantitative analysis needs linear/16-bit samples instead of the
existing RGB8 interface. Conservative choice tonight: fixed documented rendering
and no silent quality reduction.

## Final build and reference checks

- Clean `powershell.exe -NoProfile -ExecutionPolicy Bypass -File build-windows.ps1 -NoDownload`
  passed from checksum-verified archives, compiling fresh sequential LibRaw and
  libdeflate source trees. Final executable: `build/ttc-simple.exe` (2,129,426 bytes).
- PE import inspection: only `KERNEL32.dll`, `msvcrt.dll`, `WS2_32.dll`.
- Final-source synthetic RGB PNG and malformed-DNG tests passed.
- Full 244 MP loader output matched the independent LibRaw PPM file writer,
  dimensions `19136x12752` and hash `5c983bb16ed77774`, using the freshly built
  library. This checks extraction and orientation, not LibRaw color science
  against a different RAW engine.
- Coordinate/padding tests passed with both stb fallback and libdeflate encoding.
- Final executable processed the repository's `flow.jpg` (1121x747) through the
  directory CLI and created its composite successfully.
- `git diff --check` passed. No Linux run is claimed.

Second fixture `_DSC4350-_DSC4365.dng` (617,917,166 bytes) was checked with
**both executables linked to the clean, newly built dependency libraries**:

| Version | Load (s) | Composite + PNG (s) | Phase sum (s) | Peak (MiB) |
|---|---:|---:|---:|---:|
| Correct baseline | 15.378 | 18.649 | 34.027 | 5133.65 |
| Optimized | 13.872 | 9.023 | 22.895 | 4435.59 |

One pair only, a confirmation rather than a repeated estimate: 32.7% less phase
time. Both rendered 19136x12752 and produced 12752x12752 composites. Full source
hash `08b3bd2c7f34587d` and decoded composite hash `cbb0b9e80ce98280` matched.
The optimized executable and source/API ownership changes passed these checks.
The optional OpenMP archive was compiled and its parallel-loop symbols verified,
but no OpenMP image timings or correctness claim is made; default stays sequential.
