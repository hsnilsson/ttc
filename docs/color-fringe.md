# Relative edge color fringe (RGB8 v1)

TTC measures local color residual around edges of an assumed monochrome target.
This is an empirical comparison statistic, not a standard chromatic-aberration
measurement, calibrated lp/mm, a perceptual color difference, or lens-only
performance. Compare the **same ROI** at similar exposure and geometry with
identical rendering. Do not sum the five regions or use this to recommend an
aperture. The separate sharpness metric and capture selection are unchanged.

## Definition

The input is the original decoded full-resolution RGB8 ROI at its accepted
integer tracking offset. Let C be each channel divided by 255, and let
Y = 0.2126 R + 0.7152 G + 0.0722 B on those normalized rendered channels.
These are generally gamma-encoded values, not linear sensor data.

1. Compute S = P95(Y) - P5(Y), using the existing 256-bin nearest-rank convention.
2. Select edge seeds with normalized 3x3 Sobel gradient magnitude at least
   max(0.03, 0.08 S). The horizontal kernel is [-1 0 1; -2 0 2; -1 0 1]/8;
   the vertical kernel is its transpose. Dilate seeds by a two-pixel square.
3. Exclude the outer three ROI pixels, Y below 0.05, and any channel <=4 or
   >=251. Remaining pixels in the dilated band form E. All remaining non-band
   pixels form B, the baseline. Neighborhood filtering is for selection only;
   no measured channel or exported crop is resampled or blurred.
4. On B, least-squares fit each channel C = a_C + b_C Y. This removes a global
   affine cast (channel offsets/gains as represented in rendered RGB). Define
   q(p) = sum_C (C(p) - a_C - b_C Y(p))^2 / 3.
5. Report **100 sqrt(max(0, mean_E(q) - mean_B(q))) / S** as a percentage of
   the region luminance span. Report baseline noise sqrt(mean_B(q)) separately.
   All eligible edge pixels have equal weight. The subtraction is an empirical
   baseline correction, not an uncertainty estimate or proof of absence of color.
6. Report global cast separately as
   **100 sqrt(sum_C (a_C + 0.5 b_C - 0.5)^2 / 3)**: fitted RGB departure from
   neutral at mid-gray, in percent of full RGB scale. This is not white-balance
   temperature or a perceptual color metric. It can extrapolate beyond sampled
   luminances; use it as a diagnostic only.

Affine casts leave zero residual in exact arithmetic. RGB8 quantization leaves
small residuals, and nonlinear white balance/tone curves can leave larger ones.
A real color fringe can contaminate the baseline beyond the two-pixel band and
be partly fitted away. Edge orientation, blur, sampling phase, and edge density
change band membership and normalization; **this is not fringe width in pixels**.
No monotonic score across arbitrary blur or offset sizes is promised. Large
channel displacement, broad halos, colored subjects, ink, uneven illumination,
demosaicing, sharpening, compression and noise can confound the statistic.
Use a neutral black/white target and inspect crops and mask, especially when a
score falls after a rendering/exposure change. A zero can mean color is below
the estimated baseline noise floor.

## Conservative suitability gates

Thresholds are fixed heuristics, not calibrated confidence levels. Evaluation
stops at the first failed gate. Rejection produces a status and no score/mask;
it does not invalidate an otherwise usable sharpness measurement.

| Status | Rule |
| --- | --- |
| `invalid-region` | ROI out of bounds or smaller than 8 pixels in either dimension |
| `too-dark` | Mean Y < 0.05 |
| `clipped` | More than 1% of all ROI pixels have any channel <=4 or >=251 |
| `low-contrast` | S < 0.15 |
| `insufficient-edges` | Fewer than 32 edge pixels or less than 0.2% of the full ROI |
| `insufficient-baseline` | Fewer than 32 baseline pixels, less than 10% of the full ROI, or baseline Y variance < 0.0025 |
| `noise-warning` | Baseline RGB residual RMS > 0.015, or RMS of Y minus its four-neighbor average on B > 0.025 |
| `allocation-failed` | Required selection/overlay allocation failed |
| `overlay-missing` | Service found an accepted native result without both crop and mask assets |

Existing decode/tracking rejection statuses propagate without attempting
fringe analysis. Dark and flat ROIs receive the independent fringe gates. A very blurred edge may be `insufficient-edges`. Dense USAF
patterns may be `insufficient-baseline`; a score must not be invented for them.
The noise gate can reject real fine texture and miss structured edge-only noise.
Sparse near-clipped/dark pixels are excluded individually even below the 1% gate.
The three-pixel border means very small ROIs normally lack enough samples.

## Provenance and compatibility

`frame-NNNN-roi-NN-fringe.png` is a lossless RGBA image with exactly the same
width, height and origin as its original tracked ROI crop. Green (0,255,80,150)
marks E, blue (0,100,255,65) marks B; zero alpha marks excluded pixels. Thus both
score samples and samples contributing indirectly through the cast/noise fit are
visible. Colors encode membership, **not severity**. The source ROI's shifted
x/y and dx/dy in the manifest/CSV determine source-image coordinates. No display
merge, resize, interpolation, or browser pixel readback contributes to analysis.
The viewer offers a mask toggle, native-size scrolling, Fit crop and mask download.
Display scaling/device pixel ratio can affect appearance but not the statistic.

CSV appends `fringe_status`, `fringe_score`, `fringe_pixels`,
`fringe_baseline_pixels`, `fringe_noise`, `fringe_cast`, `fringe_luma_span`.
Score is blank unless accepted. Counts and diagnostics in rejected rows are
partial algorithm state and must not be interpreted as valid measurements.
The optional region `fringe` object identifies `algorithm: rgb-edge-residual-v1`;
see [the service contract](nightshift2-contract.md). Old native CSVs and old
manifests remain readable; missing fringe fields display "Not measured", not zero.
The same viewer and relative PNG assets work in live and offline reports.
The public demo's existing simulated sample has no measured fringe data and says
so; it must not compute measurements on its display WebPs. Demo export supports
optional mask URLs if a future verified example supplies them.

## Validation

`tests/fringe_checks.c` checks sharp and blurred achromatic edges, affine global
cast, controlled one/two-pixel channel offsets, offset plus cast, low/high color
noise, luminance noise, flat/dark/near-clipped/edge-free/dense/out-of-bounds ROIs,
sparse clipping exclusion, translated coordinates, horizontal/vertical symmetry,
and exact native overlay membership/counts. `tests/fringe_service_checks.py`
checks the actual native CSV through service parsing and ZIP export, RGBA mask
sizes, rejection propagation, missing masks and legacy CSV compatibility.

Synthetic blurred-edge scores were 0% neutral, 8.70085% with a one-pixel red/blue
shift, and 16.69001% with two pixels. An affine cast alone gave 0% on the sharp
edge and 0.22192% on a quantized blurred edge; this illustrates the rendering
limitation. These fixtures validate the defined statistic, not optical accuracy.
Real camera/target repeatability and diagnostic value remain unvalidated.
