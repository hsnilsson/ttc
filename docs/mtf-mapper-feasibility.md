# MTF Mapper feasibility for TTC

Research checked 2026-09-21. This is an integration assessment, not a measurement
of the local DNGs. No MTF Mapper binary was installed or run during this research.

## Decision for this release

Ship the five-region Vlad comparison using TTC's explicitly relative sharpness
scores and full-detail crops. Do not rename the existing rendered-RGB8 gradient
score to MTF, MTF50, resolution, or lp/mm. MTF Mapper is a plausible future local
CLI adapter, but the current five USAF-pattern boxes are not validated slanted-edge
measurement ROIs. Automatic Vlad recognition does not establish MTF suitability.

## What the official project supports

MTF Mapper detects dark approximately rectangular targets on light backgrounds
and estimates edge response using a slanted-edge method. It supports Windows and
Linux, command-line processing, image/RAW input, and GUI comparisons of SFR curves.
Some alignment and focus features require its own chart designs. These are
documented upstream capabilities, not features implemented in TTC.
[Official project](https://sourceforge.net/projects/mtfmapper/)

For an already isolated edge, the author's documented invocation is:

```text
mtf_mapper.exe --single-roi -q image.png output_dir
```

This bypasses rectangle detection and assumes exactly one edge. The author
recommends at least 30 pixels of space on both sides. The `-q` outputs include
edge positions, MTF50 and SFR samples, making an external-process adapter feasible.
The adapter must preserve crop-to-source coordinates and pair corresponding
physical edges across captures, rather than treating output order as identity.
[Author's single-edge documentation](https://mtfmapper.blogspot.com/2017/05/)

Angle is a measurement condition, not just a detection concern. The author
describes critical sampling angles and recommends approximately 4–6 degrees
from a sensor axis as a practical conservative choice. Algorithmic improvements
cannot make every edge angle safe from aliasing.
[Author's critical-angle analysis](https://mtfmapper.blogspot.com/2019/08/)

## Suitability of the Vlad USAF regions

The following is an engineering inference from the method above and the current
TTC ROI contract, not an upstream certification of this target:

- A box containing several horizontal/vertical bar triplets is not the isolated
  step edge expected by `--single-roi`. Neighboring bars, labels, and bar endpoints
  can contaminate an edge-spread estimate. Small near-axis bar edges also risk
  inadequate sampling geometry.
- An individual sufficiently large, isolated, naturally slanted edge on this
  physical target could be investigated. Its angle, length, surrounding clear
  area, target edge quality, exposure and repeatability must be checked first.
  No such candidate has been validated by this research.
- Rotating or resampling an image to manufacture a slant changes its spatial
  response; it is not a substitute for a suitable captured edge. Measure original
  pixels. Resampled alignment belongs to display/export, with that provenance
  recorded separately.
- USAF bar visibility or contrast can support a different resolution/contrast
  experiment when element identity, physical dimensions, magnification and
  capture processing are known. It must not be silently converted into an MTF
  curve or equated with TTC's gradient score.

For a defensible future MTF mode, use a characterized slanted-edge chart with
appropriate edges at the center and four corners, controlled illumination and
geometry, and repeated captures. Retain edge-level results and failure states.
Establish the input transfer function and a fixed linearization/rendering
pipeline; record sharpening, demosaicing and pixel-shift reconstruction. A
result from this chain characterizes the captured imaging system, not the lens
alone. Sensor-plane lp/mm additionally needs verified sampling pitch for the
actual output grid; PS16 output dimensions alone are not that calibration.

TTC's present RGB8 metric limitations are already documented in
[ROI analysis](roi-analysis.md). Its heatmap should compare apertures within each
region, retain numeric values and repeat disagreement, and avoid universal MTF
or optical-quality claims.

## Packaging and licensing

The official project identifies its license as BSD. However, the exact upstream
`license.txt` could not be retrieved through the research browser, so the BSD
variant and the complete distribution notices are not verified here. The source
tree exposes that file and its installer configuration refers to it. Before
redistribution, inspect the license from the exact pinned release and retain all
required notices; audit every bundled dependency separately. A project-page
license label does not establish the licensing of a complete Windows installer.
[Project license label](https://sourceforge.net/projects/mtfmapper/),
[official source tree](https://sourceforge.net/p/mtfmapper/code/HEAD/tree/trunk/)

The inspected upstream CMake snapshot declares OpenCV, TCLAP and Eigen3, with
optional zlib; its package configuration also lists gnuplot, exiv2 and dcraw.
This is materially more packaging work than a small TTC detector module. Exact
requirements must be checked against the selected release, not assumed from this
snapshot. No dependency is added to TTC by this document.
[Official build configuration](https://sourceforge.net/p/mtfmapper/code/HEAD/tree/trunk/CMakeLists.txt)

Start any future adapter with a user-installed executable and explicit version
detection. Run it locally in a separate output directory, without uploading
images. Pin and record executable version, arguments, input processing, edge
geometry and failures. A later bundled distribution needs its own dependency
and license review. Shareable reports can contain the resulting data and plots
without needing MTF Mapper installed on the recipient's machine.

## Bounded follow-up validation

1. Select a pinned release and inspect its included guide, executable help,
   licenses and dependency inventory. The author recommends the guide shipped
   with the installed version to avoid stale documentation.
   [Guide guidance](https://mtfmapper.blogspot.com/2018/02/improved-user-documentation.html)
2. Validate the adapter on synthetic edges with known blur, several edge angles,
   noise/clipping cases and invalid multi-edge crops; define rejection behavior.
3. Capture a suitable physical chart with independent repeats. Check edge
   pairing, output units and repeat uncertainty before exposing MTF in the GUI.
4. Only then evaluate any suitable individual Vlad edge experimentally; report
   unsupported regions rather than filling five cells with invented results.

These follow-ups do not block content-based Vlad ROI detection or the local TTC
comparison product. This document contains no measured MTF curves or values.
