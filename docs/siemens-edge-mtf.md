# Siemens-spoke slanted-edge experiment

## Center pinwheel follow-up (2026-10-15)

The existing images now provide accepted measurements at all five primary
locations. The center uses two broad pinwheel boundaries, at approximately 30
and 120 degrees to image horizontal, rather than requiring 3–7-degree edges.
The previous center failure was a geometry restriction, not evidence that no
usable central edge existed. No images are rotated or resampled for measurement.

All 32 center measurements pass across the sixteen captures. Maximum repeat
difference is 7.22% of pair mean; maximum crop sensitivity is 1.00%. Together with
the unchanged 128 outer-corner measurements this gives 160/160 primary results,
and 267/288 including inset stars. Each center direction uses the same physical
edge across captures, selected by geometry/validity rather than highest MTF50.
No second isolated pinwheel edge passed for either direction, so independent
supporting-edge agreement remains unavailable and is shown as such.

The center's **detail directions are oblique**, approximately 30 and 120 degrees;
they are not horizontal/vertical corner measurements. Compare center apertures
within each direction. Do not combine them with the corner results into an
overall MTF score or infer a direction-matched center/corner ranking. Result
metadata records `method: pinwheel-oblique-edge` and `detail_angle_degrees`;
the historical `direction` keys remain grouping keys for viewer compatibility.

54 additional analytic cases cover edges at 28/30/32 and 118/120/122 degrees,
Gaussian blur sigma 1/2/3 pixels, and three subpixel phases. Each must meet the
existing 3% MTF50 error, 3% crop-spread, and 0.03 absolute curve-error bounds.
The normal clipping, isolation, tracking, reference identity and 10% crop-spread
gates remain in force. This is experimental captured-system SFR, not certified
ISO measurement or independently calibrated lens MTF. Repeatability does not
remove possible bias from the target, reconstruction or rendering.

Evidence: `build/mtf-center-series/measurements.json`; updated report pointer:
`build/mtf-center-series/latest-report.txt`.

## Previous verdict (2026-10-15; superseded above)

The user's proposed method works on some outer segments of Vlad's Siemens
stars. It does **not** currently provide a complete, reliable center-and-four-
corners MTF map. Keep the established five-region gradient score; expose this
as a separate opt-in experiment, with missing results and rejection reasons.

## Reliability follow-up (2026-10-15)

The revised run accepts **235 / 288** primary measurements, versus 100 / 288 in
its baseline. All **128 outer-corner measurements** pass: four corners, both
directions, all sixteen captures. Context tracking passes for all 144 crops.
The remaining 53 rejections are 21 inset-star measurements and all 32 center
measurements. There are no remaining tracking or first-reference cascade failures
in this dataset. The center block searches four small stars and the larger
pinwheel; none yielded a geometry-eligible near-axis boundary in any capture.
This does not establish that center sharpness is poor or that another method
could not measure it.

112 repeat pairs have both primary measurements accepted. The maximum repeat
difference is **9.24% of pair mean**, also the maximum among the 64 outer-corner
pairs. Of 383 accepted supporting-spoke checks, five differ from their primary
by over 20% (maximum 26.19%); the report flags these without replacing the primary.
Repeatability and crop stability do not establish absolute physical accuracy.

| Location | Horizontal accepted / 16 | Vertical accepted / 16 |
| --- | ---: | ---: |
| Outer top left | 16 | 16 |
| Outer top right | 16 | 16 |
| Center test block | 0 | 0 |
| Outer bottom left | 16 | 16 |
| Outer bottom right | 16 | 16 |
| Inset top left | 16 | 5 |
| Inset top right | 15 | 13 |
| Inset bottom left | 12 | 16 |
| Inset bottom right | 16 | 14 |

Evidence is in `build/mtf-reliable-final/measurements.json` and
`build/mtf-reliable-final/latest-report.txt`. Sixteen fixed context crop sets were
extracted with the native engine; the larger central contexts reuse original
native crops from the same captures. The first central crop was compared against
a fresh native extraction: every RGB byte in their 1615 x 1555 overlap agrees.
The expanded center box is also exercised through the local service integration.

The main curve view prioritizes outer top left, outer top right, center, outer
bottom left and outer bottom right. Inset curves are additional evidence in a
separate disclosure. Coverage is computed for the displayed whole capture and
never filled with another region or another metric.

## Initial baseline

The initial baseline run on all 16 local `vlads4` PS16 DNGs (eight apertures, two
captures each) accepted 100 of 288 possible location/direction measurements.
There were 42 pairs with both repeats accepted; their largest difference was
6.24% of the pair mean. This measures repeatability on this dataset, not absolute
accuracy or statistical confidence. The initial fixed-box investigation had
87 accepted results; the final result uses registered locations, native tracking,
and fixed physical radial endpoints across captures. The follow-up implementation
below supersedes its first-capture and sparse-tracking policies.

| Location / detail direction | Accepted captures / 16 |
| --- | ---: |
| Inset top left / horizontal | 16 |
| Inset top left / vertical | 5 |
| Inset top right / horizontal | 13 |
| Inset top right / vertical | 13 |
| Inset bottom left / horizontal | 0 |
| Inset bottom left / vertical | 16 |
| Inset bottom right / horizontal | 16 |
| Inset bottom right / vertical | 14 |
| Outer bottom left / vertical | 1 |
| Outer bottom right / vertical | 6 |
| Other outer directions and small central star | 0 |

On the accepted inset results, the top tends to peak around f/5–f/5.6 and the
bottom around f/4.5. These are different physical locations from TTC's USAF
regions, with incomplete directional coverage. Do not combine them into a
replacement overall recommendation or silently fill missing cells with the
gradient score. Selected whole captures remain those selected in the existing
comparison, including manual whole-capture overrides.

## Method and rejection policy

1. Use the existing SIFT chart registration to project nine investigation areas:
   four inset stars, four outer partial stars, and a center test block containing
   all four small central stars plus the larger pinwheel.
   Coordinates seed the search; measured boundaries must be found in the image.
2. Extract original-resolution RGB8 crops through TTC's native decoder. The
   optional stage adds a second extraction pass with fixed context boxes.
   Independently verify translations using unique SIFT context matches, RANSAC,
   spatial coverage and residual gates. Search alternative context anchors when
   coverage is incomplete; select by registration coverage, never MTF50. Cache
   features once per capture and location. Measurements use original pixels,
   shifting coordinates rather than resampling. Rotation above 0.08 degrees,
   scale change above 0.1%, or translation above 32 pixels is unsupported.
   The first chart itself can be rotated and is feature-registered.
3. Find long straight radial boundaries with OpenCV LSD, 3–7 degrees from a
   pixel axis. Rank by geometry (closeness to 5 degrees), never measured MTF.
   Compare the same spoke on later captures, within angle/position tolerances,
   preserving its radial endpoints despite blur changing detected line lengths.
   Fit the intersection of long radial boundaries to refine each star center.
   Search captures in order for each direction's first valid reference; a failed
   first capture does not poison the remaining series. Up to two additional
   physical spokes are frozen as supporting checks, never averaged into or
   substituted for the primary score. Over 20% disagreement is a visible caution,
   not proof that one edge is wrong.
   Exception: the large central pinwheel searches edge angles 28–32 and
   118–122 degrees, yielding two perpendicular oblique detail directions. Other
   stars retain their original near-axis gate. Unsupported chart rotations are
   rejected rather than digitally rotated into the allowed range.
4. Initially, the outer half was tested. Neighbouring spokes contaminated many
   of those rectangles and sometimes returned plausible but incorrect values.
   The accepted implementation measures about 3–15% inward along the detected
   spoke from its outer endpoint, leaving the circular border outside. This is
   typically about 100 pixels long on an inset star in this dataset. For shorter
   boundaries, extend the nominal span toward 100 pixels, capped at 45% inward;
   all four extent variants must still pass the same isolation and stability gates.
5. Require at least 80 pixels of edge length and 30 pixels on each side. Reject
   insufficient contrast, clipped luminance or RGB channels, non-flat margins,
   excessive total variation, and apparent extra transitions. These are
   conservative engineering gates; they do not certify the printed edge.
6. Invert LibRaw's default 0.45/4.5 transfer curve per RGB channel, using its
   computed toe and offset, then form linear luminance and write a 16-bit PNG.
   RGB8 rounding cannot be undone. PNG/JPEG input is deliberately unsupported
   by this experimental stage because its transfer function is unspecified.
7. Run MTF Mapper 0.7.40 with `--single-roi -q -f -e -v 1`. Require exactly one
   edge, finite MTF50 below Nyquist, matching edge angle, and conservative
   limits on overshoot/high-frequency response. Keep 33 SFR samples from
   0 through 0.5 cycles per output pixel.
8. Repeat with four crop variants (different inner/outer endpoints and widths).
   Reject a relative MTF50 range above 10%. Display this crop sensitivity
   separately from the repeat half-range. Repeats differing by over 10%, or
   missing a measurement, are visibly flagged in the table.

The result includes the target, pixel-shift reconstruction, rendering, optics,
and sensor sampling. It is not lens-only MTF, a calibrated resolution limit,
or sensor-plane lp/mm. There is no spatial resampling in the measurement
pipeline. Display-only previews are reduced to 600 pixels on their longest
side; green rectangles retain original-source coordinates.

## Running the prototype

Normal TTC behaviour is unchanged unless an executable is explicitly supplied:

```powershell
scripts/codex-run-ttc-local.ps1 -MtfMapper 'C:\path\to\mtf_mapper.exe'
```

Alternatively pass `--mtf-mapper` to `local/ttc_local.py serve`, or set
`TTC_MTF_MAPPER` for the process launching TTC. Use Python 3.11+ with the normal
Vlad dependencies. Choose **Open & compare automatically**: detection, ordinary
analysis, and experimental star measurements then run sequentially. If starting
from manually placed regions, run chart detection first so registered star
geometry is available. A failed experimental stage does not erase ordinary
measurements; the report explains why star results are unavailable.

The report leads with overlaid curves for all apertures and repeats, a 50%
contrast line, and MTF50 markers. Plain-language text explains cycles per output
pixel and the reciprocal pixels per line pair. Repeat coverage/agreement, crop
variation, supporting-spoke agreement and context tracking are separate observed
checks, not statistical confidence. A chart overview identifies actual MTF search
locations; they are not TTC's USAF boxes. Numeric tables and source overlays remain
available in disclosures, with explicit missing-result reasons. Aperture-column selection and
the capture-repeat control update the evidence. Offline ZIPs contain the
measurements and display previews; the recipient does not need MTF Mapper.
Raw diagnostic outputs and original-pixel measurement crops stay in the local
job's `mtf-N` directory, excluded from the shared archive.

MTF Mapper is **not bundled in the distributable TTC package**. A private copy
of the official Windows release was extracted under ignored
`build/mtf-investigation/mapper` for this local experiment, without installing
it system-wide. Redistribution/licensing review remains separate from this
prototype. The version and executable SHA256 are recorded in each result.

## Reproduction and evidence

Pinned Windows download:
[MTF Mapper 0.7.40](https://sourceforge.net/projects/mtfmapper/files/windows/mtfmapper-0.7.40-win64.exe/download).
Installer SHA256:
`44d7f6380777ff25e1fb646d2c42458a12d43583523a5fcf982aacfbbd39cb1b`.
Evaluated executable SHA256:
`6bdb50911e80ce00e35465b9c44a304eccc84667ed7bcd7834c8624b86f3a273`.

```powershell
$env:TTC_MTF_MAPPER = 'C:\path\to\mtf_mapper.exe'
python -B tests/star_mtf_checks.py
python -B tests/local_checks.py
python -B tests/vlad_registration_checks.py
node --test web/tests/viewer.test.cjs web/tests/demo.test.cjs web/tests/star-mtf.test.cjs
```

Synthetic Gaussian edges use sigma 1, 2 and 3 pixels, each at 3, 5 and 7 degrees.
Expected MTF is `exp(-2*pi*pi*sigma*sigma*f*f)`; MTF50 is
`sqrt(2*ln(2))/(2*pi*sigma)`. All nine cases pass a 3% MTF50 error bound,
3% crop-variation bound and 0.03 absolute curve-error bound. Negative checks
cover extra transitions, flat/clipped input, short edges, clipped RGB channels,
missing executable, and undefined input transfer/registration. A low-noise
case verifies the isolation gate does not reject all noisy input. Follow-up tests
cover context translation, unrelated/rotated crop rejection, a damaged first
context, a valid reference established by a later capture, coordinate immutability,
all five central feature seeds and medium-length analytic edges.

Local evidence (ignored, not repository assets):

- `build/mtf-investigation/jobs/f90494099b5a618f`: real 16-image automatic run,
  native logs, source-pixel crops, registration geometry and measurements.
- `build/mtf-investigation/latest-report.txt`: final offline report location.
- `build/mtf-investigation/end-to-end.log`: automatic run and export completion.
- `build/mtf-investigation/stars`: initial wider-area feasibility crops.

Browser verification checks column selection, evidence overlays and curves,
repeat switching, and absence of browser errors. Synthetic tests validate the
adapter against known blur; they do not establish that the physical target's
edges have negligible blur. No comparison to an independently characterized
physical target has been performed.

Primary method references:
[single-edge input and margins](https://mtfmapper.blogspot.com/2017/05/),
[sampling angles](https://mtfmapper.blogspot.com/2015/06/critical-angles.html).

## Questions saved for later

- Center coverage is now available from the existing pinwheel, but its oblique
  directions differ from the corners. A known near-axis slanted-edge target
  would still be useful for independent validation and direction-matched results.


- Is a partial, explicitly labelled inset-star MTF comparison useful enough to
  keep in the user-facing product, or should this remain an investigation tool?
- Would you like a separate slanted-edge capture to establish centre/corner
  coverage and compare against the Vlad estimates? None is required to inspect
  this prototype, and no new capture has been assumed.
- Should eventual presentation emphasize MTF50, a normalized relative score,
  or contrast at a chosen detail size? Keep the underlying curves either way.
