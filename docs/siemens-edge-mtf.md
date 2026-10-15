# Siemens-spoke slanted-edge experiment

## Verdict (2026-10-15)

The user's proposed method works on some outer segments of Vlad's Siemens
stars. It does **not** currently provide a complete, reliable center-and-four-
corners MTF map. Keep the established five-region gradient score; expose this
as a separate opt-in experiment, with missing results and rejection reasons.

The integrated run on all 16 local `vlads4` PS16 DNGs (eight apertures, two
captures each) accepted 100 of 288 possible location/direction measurements.
There were 42 pairs with both repeats accepted; their largest difference was
6.24% of the pair mean. This measures repeatability on this dataset, not absolute
accuracy or statistical confidence. The initial fixed-box investigation had
87 accepted results; the final result uses registered locations, native tracking,
and fixed physical radial endpoints across captures.

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
   four inset stars, four outer partial stars, and one small central star.
   Coordinates seed the search; measured boundaries must be found in the image.
2. Extract original-resolution RGB8 crops through TTC's native decoder. The
   optional stage currently adds a second extraction pass. Track integer
   translations, retaining failures instead of using untracked crops. This
   experiment assumes a fixed-chart series; it does not correct rotation between
   captures. The first chart itself can be rotated and is feature-registered.
3. Find long straight radial boundaries with OpenCV LSD, 3–7 degrees from a
   pixel axis. Rank by geometry (closeness to 5 degrees), never measured MTF.
   Compare the same spoke on later captures, within angle/position tolerances,
   preserving its radial endpoints despite blur changing detected line lengths.
4. Initially, the outer half was tested. Neighbouring spokes contaminated many
   of those rectangles and sometimes returned plausible but incorrect values.
   The accepted implementation measures about 3–15% inward along the detected
   spoke from its outer endpoint, leaving the circular border outside. This is
   typically about 100 pixels long on an inset star in this dataset.
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

The report has a separate MTF50 table, direction labels, repeat flags, curves,
measurement overlays, and failure explanations. Aperture-column selection and
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
case verifies the isolation gate does not reject all noisy input.

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

- Is a partial, explicitly labelled inset-star MTF comparison useful enough to
  keep in the user-facing product, or should this remain an investigation tool?
- Would you like a separate slanted-edge capture to establish centre/corner
  coverage and compare against the Vlad estimates? None is required to inspect
  this prototype, and no new capture has been assumed.
- Should eventual presentation emphasize MTF50, a normalized relative score,
  or contrast at a chosen detail size? Keep the underlying curves either way.
