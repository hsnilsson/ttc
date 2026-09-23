# Content-based Vlad detection and registration

This documents the older native CLI. The browser service now uses the
[rotation-aware Python/OpenCV detector](vlad-registration.md).

`vlad_detector.h` is a dependency-free native detector for **the Vlad target
variant and approximately frame-filling orientation in the local vlads4 set**.
It recognizes the center and four corner USAF contexts; it is not a generic USAF
element reader, chart calibrator, or MTF measurement. No decoder is changed.

## Integration contract

Include the header after TTC's `Image`, `load_image`, and `free_image` definitions.
The backend owns the main executable dispatcher:

```c
#ifdef TTC_VLAD_DETECTOR
#include "vlad_detector.h"
#endif
/* in main, before normal cropper output: */
if (argc > 1 && !strcmp(argv[1], "--detect-preview"))
    return vlad_detect_cli(argc, argv);
```

```text
ttc-simple --detect-preview PREVIEW.png FULL_WIDTH FULL_HEIGHT
```

Use a decoded, oriented preview, preferably 1600 pixels wide, made by TTC's
existing rendering pipeline. Dimensions describe that same oriented source.
All returned rectangles use zero-based full-resolution source pixels; right and
bottom endpoints are excluded. IDs are `center`, `tl`, `tr`, `bl`, `br`.

JSON contains `status`, `confidence`, `rois`, `candidates`, and `warnings`.
`status=accepted` means all five candidates passed the checks; only then is
`rois` populated. `manual-required` always has an empty `rois` list. `candidates`
provides five diagnostic objects with `x,y,width,height`, NCC `confidence`,
competing-peak `margin`, local `scale`, `angle` (degrees), and per-region `status`.
Never silently apply failed candidates. Offer manual editing and retain the
user's corrected boxes. A valid JSON response exits 0 even when manual selection
is required; invalid command arguments or failed loading exit 1.

The direct C API is `vlad_detect(image, full_width, full_height, &detection)`.
It returns true only for accepted detection. Detect the reference **once**, then
track those regions at full resolution throughout the series. Re-detecting each
capture would introduce preview quantization and varying measurement boxes.

## Content and confidence

The detector reduces the preview to at most 800 pixels wide using area averages.
Five small grayscale context templates include actual bars, labels, and nearby
structure. It searches translations within approximately 12% of image width and
height around approximate expected positions, three initial scales and three
angles, then refines position, scale, and angle using bilinear samples. The
normalized positions guide a search; they never suffice to accept a box.

Zero-mean normalized cross-correlation must exceed 0.78, with a 0.10 separation
from a spatially distinct competing peak. Both best and competing peaks are
refined: coarse competing samples alone can incorrectly accept duplicate
patches. Flat image context, out-of-bounds boxes, search-edge matches, local
scale outside 0.88–1.12, and rotation beyond 4.5 degrees are rejected. Scale and
rotation search support small setup changes, not arbitrary reframing. Boxes
remain axis-aligned; rotation is a template matching parameter, not an image
rotation or perspective correction.

These thresholds are heuristics tested below, **not calibrated probabilities**.
The overall confidence is the minimum of the five nonnegative NCC scores.
Failure on another target design, substantially different framing, inversion,
lighting, blur, occlusion, or changed rendering is expected. A finite negative
test set cannot establish a universal false-positive rate. Inspect all boxes.

## Template provenance

`vlad_templates.h` contains five 32×32 grayscale arrays (5,120 intensity samples,
approximately 17 KB as C text). They are minimal derivatives of the user's local
`_DSC3982-_DSC3997.dng`, using its previously validated 1600×1066 `reference.png`
from the ROI task's `build/real-stack-final/`. The center is calculated from
`examples/vlads4-19136x12752.roi`; context spans 200 preview pixels for center and
210 for corners. Each sample averages a 5×5 neighborhood. No full image, DNG,
embedded metadata, absolute input path, or large source asset is committed.
Original target artwork rights are not changed by this code's MIT license.

The reference preview SHA-256 is
`92A10F9545A60DE1EFB7A4029D4A1A0C0203F357AC668DA0C624B67C31506477`.

Reproduce with `tests/make_vlad_templates.c` against that exact preview. It emits
the header on stdout and requires the documented preview dimensions. The saved
manual coordinates define which known physical features the templates represent;
runtime location still depends on image content.

## Verification (2026-09-21)

Built with cached w64devkit GCC, `-O2 -Wall -Wextra -DNO_LIBRAW`, no added runtime:

```text
gcc -O2 -Wall -Wextra -DNO_LIBRAW tests/vlad_checks.c -o build/vlad-checks.exe
build/vlad-checks.exe
build/vlad-checks.exe PATH_TO_REFERENCE_PREVIEW.png
gcc -O2 -Wall -Wextra -DNO_LIBRAW tests/vlad_detect_cli.c -o build/vlad-detect.exe
gcc -O2 -Wall -Wextra -DNO_LIBRAW tests/roi_alignment_checks.c -o build/roi-alignment-checks.exe
build/roi-alignment-checks.exe
git diff --check
```

The no-argument checks construct a mechanical fixture from the templates. That
is a reproducible code regression test, not independent recognition evidence.
The optional real-preview suite applies controlled transforms to a **single
reference capture**: shift (+47,-25) preview pixels, scale 0.96, rotation +2
degrees, and combined scale 0.97/rotation -1.5/shift (+16,-7). On that reference,
all five locations followed the transforms with center error below 1.2 preview
pixels (about 15 full-resolution pixels). This is localization accuracy under
known synthetic transforms, not measured real-capture registration accuracy.

Negatives reject constant gray, seeded noise, checkerboard, repeated stripes,
missing center context, and two identical center contexts (ambiguous). The
repository's `flow.jpg`, which includes the target at unsupported scale among
other content, is rejected at its correct 1121×747 dimensions. Incorrect source
aspect ratio also returns manual-required. Synthetic negatives are not a broad
photographic classification benchmark.

Two genuine DNGs were decoded sequentially by the backend task using TTC's
existing decoder; the detector reused its previews without extra full decodes:

| Capture | Relationship | Minimum NCC | Result |
| --- | --- | ---: | --- |
| `_DSC3982-_DSC3997.dng` | Template source, freshly decoded | 0.964087 | Five accepted |
| `_DSC4222-_DSC4237.dng` | Independent capture, different aperture sequence | 0.963176 | Five accepted |

Both decoded dimensions are 19136×12752. The independent capture's detected
coordinates move by approximately -3 to -9 pixels horizontally and +9 to +15
vertically. The preview was visually inspected and locations correspond to the
five USAF contexts. No independent full-resolution landmark ground truth was
established, so these movements are **not** claimed as subpixel ground truth.
All originals were read-only. No source files were modified.

## Registration and display

Current product crops use existing conservative integer `roi_track` results and
original decoded pixels. They are integer-aligned, **not subpixel-perfect**.
Residual fractional translation, rotation, and scale differences can remain
visible when flipping crops and can affect sampled detail scores.

`roi_display_alignment.h` is an optional, tested helper, not wired into crop
production in this release. After an accepted integer match it fits a local
two-dimensional quadratic to the 3×3 NCC neighborhood, including the mixed
derivative. It rejects non-concave/ill-conditioned fits, offsets beyond half a
pixel, or invalid sampling boundaries, and returns the integer fallback. Its
fractional `dx,dy` are display estimates only. Tests using analytically shifted
smooth textures recover (2.30,-1.25) as (2.2983,-1.2463), and (-0.35,0.40) as
(-0.3427,0.3931). Rejected integer matches are never refined.

This demonstrates why fractional shifts matter and supplies a bounded future
display API; it does not validate the estimate on the real DNG series. Future
subpixel display/export must explicitly resample, label that interpolation and
retain native-pixel metrics/crops. Do not feed resampled display pixels into the
current metric pipeline or claim calibrated geometric correction.

MTF scope, official capabilities, target limitations and packaging research are
in [MTF Mapper feasibility](mtf-mapper-feasibility.md).
