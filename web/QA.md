# Viewer integration QA · 2026-09-21

Production assets contain no fixtures, remote dependencies, uploads or telemetry.
Eight Node tests cover restrained tie colors, rejected states, numeric aperture
ordering, whole-capture selection, missing selection, unknown aperture retention,
native crop dimensions, escaping, provenance-preserving edits, and bounded manual
ROI initialization. `node --check web/viewer.js` also passes.

Browser QA used the Codex in-app browser against authorized loopback servers.
The explicitly synthetic `web/tests/serve-fixture.cjs` fixture checked keyboard
aperture/repeat flips, zoom retention, all-five and focused layouts, repeat flags,
and session-only whole-capture override. Native backend fixture job
`751203911d470931` also loaded successfully, including native PNG crops.

## Actual PS16 DNG workflow

Through the GUI on `http://127.0.0.1:8765`, imported read-only
`D:\camera scanning\vlads4`, creating job `31e2c1bcb549d5f7`.
All sixteen frames appeared as eight apertures (3.5, 4, 4.5, 5, 5.6, 6.3,
7.1, 8), two repeats each, with aperture source metadata.

- Ran target detection through the GUI; inspected the real reference preview
  and five detected boxes. Center 650×650; four corners 880×880.
- Saved center x from 9255 to 9256, verified it, then restored 9255. All sixteen
  aperture sources stayed metadata. This exposed and fixed the initial frontend
  bug that sent unchanged aperture values as manual corrections.
- Started all-sixteen analysis through Run comparison. Progress/cancel appeared,
  and editing/export controls were disabled during processing.
- Radius 16 reached the vertical tracking boundary for later apertures: five
  reference, 39 tracked, 36 tracking-boundary rows. The first four apertures had
  selected complete captures; f/5.6–f/8 stayed unranked. The UI displays
  **No valid capture** with actual tracking-boundary reasons in the tooltip and
  individual region statuses in the crop viewer. No thresholds were relaxed.
- Verified all eight numeric aperture columns and five region rows, with repeat
  half-ranges and restrained within-row colors.
- Verified actual image `naturalWidth`/`naturalHeight`: 650×650 center,
  880×880 corners. Set zoom 125%, dragged by 50×25 CSS pixels, and verified the
  same transform (zoom 1.25, pan 40×20 source pixels) survived aperture and
  keyboard repeat changes.
- Selected the alternate f/4.5 whole capture; all five crop URLs changed to
  frame-0005 and the heatmap column changed consistently. Restored frame-0006.
- Triggered default ZIP export through the GUI. `share-f31fc3fd.zip` retains
  all sixteen frame records and eight groups, with 44 accepted native crops.
  Rejected crops are honestly unavailable. Structural validation passed native
  dimensions, embedded manifest equality, relative assets, and no absolute
  source paths or remote URLs. The actual standalone report rendered correctly
  at `http://127.0.0.1:8767`, including explicit rejection warnings.

The separate radius-32 retry with identical sources, ROIs and thresholds,
job `5f68cf68457c8032`, completed with **5 reference + 75 tracked** measurements
and no rejected regions. All eight apertures have a selected whole capture.
Original radius-16 evidence remains.

The GUI rendered all forty numeric cells and repeat half-ranges, then exported
`share-0b750264.zip`. Structural checks passed for sixteen frames, eight groups,
and **80 native-dimension crops**, with embedded manifest equality, relative
assets and no private source paths. The resulting standalone report was loaded
at port 8767: verified five table body rows, eight aperture columns plus the
region heading, and all forty numeric cells. Selected f/8 and confirmed its
five image URLs all point to frame-0016, with natural dimensions 650×650 and
880×880. There are no sample values in either real report.

## Failure and manual correction checks

Imported an isolated tiny PNG with no aperture metadata/filename hint. The GUI
retained it in Unassigned aperture, with no heatmap ranking. Explicit manual ROI
initialization produced twenty editable coordinate/size fields, a not-detected
draft warning, and a disabled Run button until Save corrections succeeded.
Saved a manual f/4 assignment; provenance became manual. Export before analysis
failed visibly with **Analyze before exporting** in both status and error area.
Against the final service source in a separate loopback process on port 8768,
verified the default search radius was 32, changed it to 24 through the GUI,
saved and verified 24 persisted, then stopped that isolated service using its
Stop local service button. No DNG was decoded by this separate check.

## Remaining manual checks

Direct file:// opening of the extracted ZIP, the native Windows chooser dialog,
and end-user browser/OS scaling have not been exercised. The plain offline
scripts and relative images avoid file:// fetch dependence. GUI cancellation was
not used to interrupt the expensive real run; backend process-cancellation tests
are owned by the service task. Full-image optional export was verified by the
backend; inconsistent region translations must remain explicitly flagged.
