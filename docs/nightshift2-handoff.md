# Nightshift 2 handoff — 2026-09-21

## Delivered workflow

Portable Windows local browser application and CLI share the native TTC engine.
Import a directory, read aperture metadata (filename then manual fallback),
recognize the five Vlad regions from image content, inspect/correct them, and
analyze. Review five heatmap rows across numerically sorted apertures, select
one whole repeat capture per aperture, and flip full-detail crops with shared
zoom/pan. Export portable HTML/assets ZIPs and crops. Optional full-frame exports
require consistent measured integer shifts across all five regions.

The package includes a private Python standard-library runtime; no Python
installation is needed. Processing stays on the computer. This is an unsigned
Windows x64 portable folder, not a signed installer.

## Validation

Coordinator combined and compiled all three task branches. Native ROI checks,
content-detector negative/transform checks, optional alignment-helper checks,
full-detail export pixel/no-overwrite checks, seven service tests and eight
viewer tests passed. JavaScript syntax and Git whitespace checks passed.
The optional subpixel helper is tested but is not used by the delivered viewer.

The actual GUI imported all sixteen PS16 DNGs from D:/camera scanning/vlads4,
recognized eight aperture groups with two repeats each, detected five regions,
saved/restored an edited region without changing metadata provenance, and ran
the series. The original 16-pixel search hit the boundary for later captures.
Inspection showed high correlation at that boundary. The default was increased
to 32, and the search range is editable; all rejection thresholds stayed fixed.
The bounded repeat run accepted all 80 regions: five reference and 75 tracked.
All eight apertures (f/3.5,4,4.5,5,5.6,6.3,7.1,8) have a whole-capture selection.

The GUI verified five-by-eight heatmap values, repeat spreads, complete-capture
overrides, retained pixel zoom/pan and keyboard switching. The shared report
contains all sixteen frame records and 80 native-sized crops (650x650 center,
880x880 corners). Its embedded manifest equals manifest.json, asset paths are
relative, and private source paths, native logs and DNG files are excluded.
The standalone report was browser-tested through a loopback static server;
direct file:// opening and a clean-machine Windows run remain untested.

## Delivery artifacts

Ignored build/ contains the final portable application folder/ZIP, native
executable, and TTC-vlads4-comparison/ plus TTC-vlads4-comparison.zip.
Extract the application ZIP fully and double-click Launch TTC.vbs. If Windows
policy disables VBScript, run ttc.cmd serve. Use Stop local service in the UI;
closing a browser tab alone does not stop the local helper.

## Questions saved for later

- Validate the unsigned package and native folder chooser on a clean Windows PC.
- Decide whether fractional-pixel display alignment is worth interpolation;
  current measurement/crop alignment remains integer-only.
- Detection templates support the tested Vlad design and bounded geometry,
  not arbitrary charts. More independent capture setups would broaden validation.
- Current scores are relative rendered-image detail; repeat spread is not a
  calibrated confidence interval. Noise, processing and target content matter.
- The five USAF boxes do not justify MTF curves. See the separate MTF feasibility
  research for suitable-edge validation and exact-release licensing work.

Source images and the original ditch-python checkout are preserved. No remote
push or GitHub discussion writes were performed. Worker worktrees and ignored
QA artifacts are retained for review; cleanup must preserve them and avoid
active worktrees.
