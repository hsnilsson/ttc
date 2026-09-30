# Local comparison viewer

`index.html`, `report.html`, `viewer.css` and `viewer.js` are dependency-free
production assets. Serve `index.html` through the TTC loopback server. The live
viewer uses `/api/session` and `/api/jobs` with the documented session token;
it never uploads images or contacts external services. Import uses a local
directory path or the server's native Windows folder chooser. No browser upload
is involved. `?job=ID` opens an existing local job without altering another job.

For an offline report, copy `report.html`, `viewer.css`, `viewer.js` into the
ZIP root alongside crop assets, and replace the `null` text of
`script#ttc-manifest` with the manifest JSON. Escape every `<` as `\u003c`
before inserting JSON into HTML. `window.TTC_MANIFEST` is also supported.
Use relative asset URLs and remove private source paths before packaging.
The embedded manifest starts offline mode, without fetch or local storage.
All image assets must be the actual aligned native crops at their full pixel
dimensions. Ordinary scripts and relative images work without a file:// fetch.

The same rendering code handles live and offline manifests. Backend fields
`frames`, `groups`, `regions`, `sharpness`, and `crop_url` are adapted once at
the boundary; processing and capture selection remain backend responsibilities.
Offline whole-capture overrides affect only the current viewing session.

Colors stretch each row's loaded accepted minimum-to-maximum over a purple,
teal, and yellow spectrum. Small differences use the full range; equal values
share a neutral middle color. Rejected values are excluded. Colors indicate
relative position, not statistical significance. Clicking a column header or
any of its five values selects that aperture for all detail panes. The matrix
has no cell gaps or borders; focus-region selection is a separate control. A missing selected frame remains unranked, and unknown apertures
remain in the edit list until corrected. `±` means repeat half-range, not a
confidence interval. Five regions always come from one selected frame.

Keyboard: Left/Right switch apertures, `[`/`]` switch repeats, with focus kept
on explicit controls. Native form fields retain their usual keyboard behavior.
The 100% view uses one CSS pixel per source pixel (device/browser scaling may
still apply). Dragging, wheel zoom and zoom buttons share one pixel transform
across all regions and captures. No thumbnails are used for detail comparison.
Alignment is integer translation; a visible caveat explains residual motion.
The search radius is editable (0 or 3–32 pixels) through the shared backend.
When detection cannot accept five regions, **Define regions manually** creates
five clearly identified draft boxes. Run remains disabled until these are saved.
The page end can download a consolidated five-crop ZIP for the selected capture:
corner crops form a larger square and the center crop is drawn over the middle.
The target overlay marks the center of each small lp/mm / USAF measurement
square with a crosshair and dot. Its region name is placed outside the measured
pixels; coordinate edits and dragging remain drafts until **Save corrections**.
Corner names are chart-relative (the target's upright orientation), so they do
not claim a screen position when a scan is rotated.

## Verification

Run `node --test web/tests/viewer.test.cjs` and `node --check web/viewer.js`.
For explicit synthetic browser QA only, run `node web/tests/serve-fixture.cjs`
and open `http://127.0.0.1:8766`. The fixture is never loaded by production.

Browser checks completed: table row/column accessibility, ascending apertures,
near-tie colors, five full-size crop panes, focus-region layout, repeat
disagreement warning, whole-frame override, keyboard aperture/repeat flipping,
and zoom retained while flipping. Real backend/DNG checks are recorded in
`QA.md`. Direct file:// opening and the native OS folder chooser remain manual
QA gaps; the extracted report is tested through an authorized loopback server.

Verify generated report packaging with
`node web/tests/verify-report.cjs EXTRACTED_REPORT_DIR`. This checks embedded
manifest equality, local asset paths, absence of private absolute source paths,
and native PNG dimensions. Serve that directory for browser QA with
`node web/tests/serve-report.cjs EXTRACTED_REPORT_DIR` (port 8767).

ROI editing supports multi-step undo and Reset ROIs to saved (or last detected
positions before a save). Reset can itself be undone. Saving or detecting starts
a fresh undo history. Coordinate edits update overlays immediately. Target
zoom ranges from 100% to 800%, with scrollbars and Fit target; zoom does not
change source coordinates. Each drag is one undo action, including when zoomed.

The heatmap orders regions Top left, Top right, Center, Bottom left, Bottom right.
A total row follows after 5 CSS pixels: raw sum of all five valid region scores
from the selected whole capture. Missing/rejected regions leave the total unranked.
Highest totals (including ties) are starred. This is a practical summary of the
existing metric, not a calibrated global optical measurement.

**Open & compare automatically** imports a folder and starts the server-side
`automatic` job: generate preview, detect all five ROIs, then analyze the series.
**Detect & run comparison** starts the same pipeline on the loaded series.
No browser-timed follow-up request is needed; refreshing the page does not
interrupt the job. Cancel stops the active stage. Unaccepted detection stops
with manual-correction instructions, even when older ROIs already exist.
The manual Open folder / Detect / Run workflow remains available.
