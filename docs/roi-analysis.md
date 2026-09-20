# Reusable ROI stack comparison

TTC can apply named rectangular regions to an ordered image stack and write a
CSV and a self-contained local HTML report (keep its PNGs beside it). This is a
first step toward target analysis: select matching physical detail once, then
compare each region across exposures or apertures. It does not identify USAF
elements, infer an aperture from a filename, measure fringing, or report lp/mm.

## Run

Create a plain-text configuration. Coordinates are **decoded, oriented,
full-resolution pixels**, zero-based, with the origin at the top left. Width
and height are pixel counts; rectangles exclude their right/bottom endpoint.

```text
# Replace these dimensions and coordinates with your own image's values.
image 6000 4000
center 2700 1700 600 600
top_left 400 400 600 600
top_right 5000 400 600 600
bottom_left 400 3000 600 600
bottom_right 5000 3000 600 600
```

Use a pixel-coordinate image viewer to choose regions containing the same
target feature. Save as `target.roi`, then run:

```shell
ttc-simple --analyze target.roi comparison f4.png f5.6.png f8.png
ttc-simple --analyze target.roi tracked-comparison --track 16 f4.dng f5.6.dng f8.dng
```

Quote paths containing spaces. Pass files explicitly in the intended order;
the first file is the reference. Shell glob expansion differs across platforms,
so explicit filenames are recommended. A single reference image also works
for checking region placement. Output must be a **new directory** whose parent
already exists: previous reports and source images are never overwritten.
No full-resolution source files are copied or modified.

Open `comparison/report.html`. It contains per-frame ROI thumbnails, measurements,
status, shifts, and a reference overview with named rectangle overlays.
`report.csv` retains source filenames and all numeric values for plotting in a
spreadsheet. `rois.conf` saves the validated original coordinates for reuse;
the report identifies the ROI metric definition as v1. Files are processed one
at a time, and only registration samples
and reference metrics are retained between images. Small report previews use
nearest-neighbor sampling and must not be used for judging fine detail.

The sample [vlads4 configuration](../examples/vlads4-19136x12752.roi) is specific
to the framing of the local `_DSC3982-_DSC3997.dng` sample at 19136 × 12752. It is
an editable starting point, not an automatically calibrated geometry model.

## Configuration validation

The first non-comment line must be `image WIDTH HEIGHT`. Every remaining line
is `NAME X Y WIDTH HEIGHT`. Blank lines and full-line `#` comments are accepted;
inline comments are not. Names must be unique, contain only ASCII letters,
digits, underscores, or hyphens, and be at most 63 characters. Up to 32 ROIs
are supported. Regions must be at least 8 × 8 and entirely inside the image.
Every stack image must match the declared dimensions exactly. TTC does not
silently resize coordinates or resample a frame to fit.

## What the numbers mean

Luminance is `Y = (0.2126 R + 0.7152 G + 0.0722 B) / 255` on the decoded RGB8
values. These are rendered, generally gamma-encoded values, **not linear sensor
measurements**. All pixel statistics use original full-resolution data.

| Field | Definition and interpretation |
| --- | --- |
| `mean_luma` | Mean Y, between zero and one. Check for exposure changes. |
| `rms_contrast` | Population standard deviation of Y divided by mean Y. |
| `percentile_contrast` | `(P95 - P5) / (P95 + P5)`, with nearest-rank percentiles from a 256-bin Y histogram. Less affected by isolated extrema. |
| `gradient_sharpness` | `sqrt(mean(horizontal adjacent differences²) + mean(vertical adjacent differences²)) / mean(Y)`. Each direction has its own pair count. A relative fine-detail energy proxy. |
| `sharpness_vs_reference` | Current gradient proxy divided by the reference value for that same ROI; 1 means equal. HTML shows percent. Blank when the reference measurement is unavailable. |
| `clipped_fraction` | Fraction with any RGB channel equal to 0 or 255. It is an endpoint warning, not proof of sensor clipping. |
| `dx`, `dy` | Integer displacement relative to the original configured ROI, never cumulative across frames. |
| `x`, `y` | Shifted measurement coordinates; original configured coordinates are `x - dx`, `y - dy`. For rejected matches these describe only the rejected candidate. |
| `correlation`, `peak_margin` | Tracking NCC and separation from the best competing shift more than two pixels away in either direction. |

The normalized contrast and gradient metrics are invariant to multiplication
of decoded values **before clipping/quantization**. They are not invariant to
black offsets, changing tone curves, white balance, vignetting, or arbitrary
exposure changes in nonlinear rendered data. Use identical processing and
similar exposure. For DNG, use TTC's corrected LibRaw rendering with fixed
daylight white balance, fixed brightness, and no automatic exposure scaling.

Higher gradient energy can mean sharper detail, but also noise, ringing,
sharpening, demosaicing artifacts, JPEG artifacts, or pixel-shift reconstruction
artifacts. It is not MTF, resolving power, or an absolute optical quality score.
Do not compare the absolute score of different target patterns (for example,
diagonal corner USAF patterns against an upright center group). Compare each
ROI to itself across the stack. There is deliberately no combined winner.

More than 1% channel-endpoint pixels produces `clipping-warning`; its metrics
remain visible for inspection. Mean below 0.01 or RMS contrast below 0.001
rejects the measurement as `too-dark` or `flat`. Clipped rows can distort a
ranking even if their relative score looks plausible.

## Optional conservative tracking

With `--track N` (3–32 pixels), TTC searches every integer shift in a square
around each original ROI. A 32-pixel context border and a grid of up to 1024
3×3-averaged samples drive zero-mean normalized cross-correlation. Context is
limited to locations safe for the entire search. Measurements themselves are
not blurred, shifted by interpolation, or resized.

TTC rejects flat registration context, NCC below 0.85, competing-peak margin
below 0.01, a best match touching the search boundary, and a shifted ROI that
would leave the image. It reports the
candidate shift but leaves measurement cells empty. Repeating bars or dots
can produce ambiguous registration; enlarge/reposition the ROI to include
distinctive nearby structure, use a better aligned stack, or use fixed ROIs
after verifying alignment manually. Correlation thresholds are conservative
heuristics, not calibrated probabilities. Downsampled registration samples
can miss subtle mismatches, so inspect the crops even after an accepted match.

The method does not correct rotation, perspective, magnification/focus breathing,
large movement, target deformation, or subpixel motion. Equal image dimensions
do not guarantee equal image scale. Even a subpixel shift can change sampled
detail energy. Keep capture geometry fixed and compare the same physical region.

Exit code 0 means all rows measured and report writes succeeded (warnings may
remain); 1 means setup/configuration failure; 2 means rejected rows, failed
decodes, or output errors. Later images cannot replace a failed reference.

## Validation

Build and run the native synthetic checks from the repository root:

```shell
mkdir -p build
gcc -O2 -DNO_LIBRAW tests/roi_checks.c -o build/roi-checks -lm
./build/roi-checks
```

On Windows use the same command with your GCC executable and `.exe` suffix.
The tests cover multiplicative exposure invariance, progressive blur on
sinusoidal detail, known translation, boundary/repetitive/flat rejection,
noise sensitivity, clipping, ROI bounds, malformed/overflowing/duplicate
configurations, failed reference, dimension mismatch, invalid tracking radius,
CSV column counts, and refusal to overwrite an existing report. The generated
`build/roi-fixture.png` and `build/roi-fixture.conf` support CLI smoke tests.
