# ROI validation record

Tested on Windows with w64devkit GCC, on the native C baseline `66803a8` plus
the ROI feature. Real DNG tests additionally used the corrected decoder from
`0990441` in an isolated generated integration build. The feature and decoder
must both be integrated before using DNG analysis; the old baseline raw-buffer
copying is unsuitable for measurements.

## Synthetic and CLI checks

```text
gcc -O2 -Wall -Wextra -DNO_LIBRAW tests/roi_checks.c -o build/roi-checks.exe
build/roi-checks.exe
git diff --check
```

Passed exposure multiplication invariance, progressive blur on sinusoidal
detail, expected upward noise bias, known integer translation, boundary and
repeated-pattern rejection, flatness, endpoint clipping, ROI bounds, duplicate
names, integer overflow, UTF-8 BOM, invalid radius, dimension mismatch, failed
reference, missing inputs, report column counts, and refusal to overwrite an
existing output directory. Compiler warnings were limited to the existing
`S_ISREG` redefinition in baseline TTC. The ROI code itself produced no warnings.

An independent read-only review checked the formulas, tracking bounds,
configuration validation, CSV layout, and output escaping.

## Real full-resolution pixel-shift stack

Read-only inputs:

```text
D:\camera scanning\vlads4\_DSC3982-_DSC3997.dng
D:\camera scanning\vlads4\_DSC3998-_DSC4013.dng
```

Both decoded to **19136 × 12752**, using LibRaw full-size RGB8, sRGB output,
camera/as-shot white balance (`use_camera_wb=1`, `use_auto_wb=0`),
`no_auto_bright=1`, `adjust_maximum_thr=0`, and `bright=1`. The full-frame overview
and five crop previews were inspected: the image orientation and named center /
corner USAF locations agree with the target. Some ROI boxes deliberately include
adjacent coarse structures; they are reusable scene regions, not isolated or
calibrated USAF elements.

Command, with the isolated combined executable:

```text
build/ttc-integrated.exe --analyze examples/vlads4-19136x12752.roi build/real-stack-final --track 16 "D:\camera scanning\vlads4\_DSC3982-_DSC3997.dng" "D:\camera scanning\vlads4\_DSC3998-_DSC4013.dng"
```

Results for the second image relative to the first:

| ROI | dx, dy (pixels) | NCC | Peak margin | Relative sharpness |
| --- | --- | --- | --- | --- |
| center_usaf | 0, +1 | 0.999766 | 0.047592 | 100.59% |
| top_left_usaf | 0, +1 | 0.999708 | 0.023841 | 98.93% |
| top_right_usaf | 0, +1 | 0.999859 | 0.012729 | 99.92% |
| bottom_left_usaf | 0, +1 | 0.999705 | 0.021686 | 99.89% |
| bottom_right_usaf | 0, +1 | 0.999847 | 0.020742 | 100.72% |

All five matches passed the conservative acceptance thresholds. All ten rows
were measured; no endpoint-clipping warning was triggered. These differences
are a **repeatability observation**, not an aperture ranking: aperture labels
and capture conditions were not independently established. Small differences
can reflect residual subpixel motion, noise, rendering, or target sampling.

The report, CSV, saved coordinates, and PNG previews remain isolated under
`build/real-stack-final/` in the task worktree; image originals were untouched.
They are intentionally excluded from Git. The HTML and CSV were checked
structurally, and PNG previews were viewed directly. Browser rendering of the
local HTML was unavailable because the browser's URL policy blocks local-file
navigation; no bypass was attempted.

See [accuracy limits and definitions](roi-analysis.md) before interpreting
metrics. No calibrated lp/mm, MTF, fringing, automatic target identification,
rotation/scale correction, or claims about the best aperture are made.
