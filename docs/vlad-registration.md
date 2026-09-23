# Vlad measuring-square registration

The local browser service now uses `local/vlad_registration.py`, replacing its
old native preset-oriented detector. The old native CLI remains available for
compatibility; it does not gain this detector's rotation support.

SIFT landmarks register a bundled example of this specific Vlad chart to the
input preview. Larger features avoid the repeated dot grid dominating the
match. Robust projective fitting handles rotation, framing, scale and moderate
perspective. Each of the five small lp/mm / USAF squares must also pass a local
image correlation and visibility check. There is no coordinate-only automatic
fallback. Uncertain detection asks for manual regions and preserves previously
saved regions/results. Detection is cancellable and limited to 60 seconds.

The anchors are approximate centers recovered from the user's corrected
2026-09-23 screenshot; see `web/QA.md` for registration evidence and coordinates.
Coordinates describe the reference landmarks, not fixed positions in new
images. The intended center is projected as a point and locally refined.
Corner names follow the upright physical chart, even when it is rotated.
The GUI shows a crosshair at each ROI center and places labels outside it.

Only the detection preview is rectified. Original measurement pixels are never
rotated or resampled. Output ROIs are axis-aligned rectangles enclosing the
transformed reference square, centered on the projected point. Consequently,
this change does not make sharpness values calibrated/comparable between
separately rotated sessions, nor make series tracking rotation invariant.

## Reference and reproducibility

`local/vlad-reference.npz` contains a 1600 x 1066 grayscale preview and 1,993
SIFT descriptors from the user's local Vlad capture, not a full-resolution DNG.
Source: previous comparison `assets/run-1-reference.png`, SHA-256
`ebcdf96b131a80f7d057896dba14b641c2ae1d3db9d7e6260797746efe4ec254`.
Regenerate with `python tests/make_vlad_reference.py PATH_TO_PREVIEW`.
No external model, training service or upload is used.

Install pinned dependencies into ignored `build/python-deps` with
`python -m pip install --target build/python-deps -r local/requirements-vlad.txt`.
The portable builder includes those dependencies and their notices in its
private runtime, plus the reference and detector. It verifies versions and
detects a rotated reference using isolated packaged Python before finishing.

## Validation and limits

`python tests/vlad_registration_checks.py` checks known center positions after
rotation, scaling, padding and a projective transform. These transformed
reference tests validate geometry, not independent capture accuracy. Cases
include 0, 13, 37, 90, 180, 270 and -67 degrees with scales 0.5 through 1.15.
Missing individual squares, clipping, mirroring, blank/noise/bar/checkerboard
images and a duplicated-chart image must be rejected. Service tests cover
preserving manual ROIs/results on failure and reaping a timed-out detector.
All five test methods passed (including transform/negative subcases); the
largest synthetic center error was 0.225 preview pixels, excluding screenshot
annotation uncertainty. Ten service tests (including native analysis/export)
and nine viewer tests passed. Normal/390 px UI checks are in `web/QA.md`.

The independent `_DSC4222-_DSC4237.dng` preview is recognized with all five
local correlations at least 0.9676, 672 geometric inliers and median preview
reprojection error 0.178 pixels. Correlation is not a probability. This is
evidence for the supplied chart/capture family, not arbitrary scans. Severe
blur, occlusion, extreme perspective, very small charts or other Vlad chart
variants can require manual selection. All five measuring squares must be
visible; always inspect the overlaid centers before measurement.

The first `_DSC3982-_DSC3997.dng` was independently decoded again and gave
all five correlations 1.0. It is the reference capture, so this confirms the
native-preview convention rather than independent generalization.
