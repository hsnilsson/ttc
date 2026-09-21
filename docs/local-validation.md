# Local service/export validation

Backend source: `135da88`, `8f6f6c1`, `0f45dee` on `codex/local-service-export`.
Native detector supplied independently by `fd35cc91b8b68f849d3f85151ef2ae075b2597c6`.
GUI has its own commits; the coordinator builds the final distribution from the
combined clean integration revision. Copied integration assets were not committed
on this backend branch.

## Checks

- `python tests/local_checks.py`: seven tests passed. Covers malformed HTTP/host/
  origin/token/path requests; aperture filename fallback and invalid values;
  whole-capture selection and repeat spread; native analysis, aperture corrections,
  override preservation, ROI/tracking invalidation, archive path privacy and full
  image export; process cancellation, interrupted preview retry and export cancel.
- `build/export-checks.exe`: exact synthetic RGB pixels for positive/negative
  translations, extreme displacements, black fill, no-overwrite, full-detail crops.
- `build/roi-checks.exe`: existing native metric/tracking/configuration tests pass.
- Portable runtime: copied CPython in isolated mode, native help, hidden pythonw
  loopback launch, session token retrieval and clean `/api/shutdown` all passed.
  No system Python install or download was required.
- `git diff --check`: clean after final changes.

## Real input validation

Input directory was opened read-only: `D:\camera scanning\vlads4`. All 16 PS16
DNGs report 19136 x 12752 oriented decoded pixels. Native metadata produced two
captures at each f-number: 3.5, 4, 4.5, 5, 5.6, 6.3, 7.1, 8. No filename guesses
or manual aperture substitutions were needed. Original files were never written.

Two independent full-decode previews passed content detection: minimum NCC
0.964087 on `_DSC3982-_DSC3997.dng`; about 0.9632 on `_DSC4222-_DSC4237.dng`.
These are template matching heuristics, not calibrated probabilities.

Initial browser-driven job `31e2c1bcb549d5f7` retained all 16 frames and 80 ROI rows.
At radius 16 it reported 5 reference, 39 tracked, 36 tracking-boundary rows. Later
frames moved past the search boundary (high NCC, dy=16). Four later aperture
groups correctly had no automatic trustworthy capture. The original results
remain available; no thresholds were weakened and no rejected captures hidden.
The original share ZIP includes 16 frames, 8 aperture groups and 44 accepted
full-detail ROI crops (650x650 center,880x880 corners), 49 entries, 44,183,086 bytes.
All asset links resolve within the ZIP; no DNG/CSV/log/private source paths are
included. GUI QA verified zoom 125% and pan 40,20 retained while switching frames,
and a manual f4.5 whole-capture override changed all five regions together.

One bounded retry uses the same source images and detected ROIs with radius 32:
job `5f68cf68457c8032`. It completed with 5 reference and 75 tracked rows: all 80 regions accepted, all 16 frames retained and all 8 aperture groups selected. Selected frame IDs by ascending aperture are f0001, f0004, f0006, f0008, f0010, f0011, f0013, f0016. Final GUI export share-0b750264.zip contains all 80 full-detail crops and passed offline report verification.
The wider supported search radius is now the default and remains editable;
changing it invalidates prior measurements.

Full-frame native export was validated on `_DSC3982-_DSC3997.dng` with dx=2,dy=-1:
`build/full-aligned.png` is 19136x12752 RGB8, with black newly exposed edges.
Synthetic tests establish the exact sampling sign: output(x,y)=source(x+dx,y+dy).
Whole-image report export requires five valid agreeing ROI shifts; inconsistent
shifts skip that full image with an explicit warning while preserving crops.
No rotation, scale, or subpixel correction is claimed.

## Runtime and limitations

Tested live command used the bundled Python interpreter and the shared
`local/ttc_local.py` Manager/server API, with `build/ttc-integrated.exe` at
`http://127.0.0.1:8765/`. Generated jobs live under `build/qa-jobs/` in this worktree.
The standard user launch is `ttc.cmd serve`, or hidden `Launch TTC.vbs` in the
portable package. `ttc.cmd analyze --input DIR --roi CONFIG --output NEW_DIR`
uses the same orchestration. Close the service through the UI Stop action.

The app keeps only one full native decode active per service. A 244 MP decode
still uses several GB. Native source paths containing non-ASCII Windows
characters have not been validated. The distribution is unsigned, Windows x64,
and has not been tested on a clean machine. Jobs are saved as manifests/assets;
process restart does not yet resume an in-progress job or reload the job list.
Rejected registration rows retain their status but have no aligned crop asset.

## Final measured-transform export

The bounded full-image check completed after the 16-capture retry, with no
simultaneous native decoder. A clearly labeled validation subset exported
original f4 frame f0004 using its measured common dx=-8,dy=13. The PNG header
confirms 19136x12752. Original f4.5 frame f0006 had differing regional shifts and
was skipped as `unsupported-inconsistent-shifts`; the manifest and offline UI
show the explicit skip warning. Both frames' 10 aligned crops remain present.
Artifact: `build/qa-jobs/31e2c1bcb549d5f7/share-dc4cdcf1.zip` (331,725,118 bytes).
The final complete 16-capture report is
`build/qa-jobs/5f68cf68457c8032/share-0b750264.zip` (77,366,040 bytes).

The live QA service was cleanly shut down through its authenticated endpoint
only after GUI testing and export completion. No helper server owned by this
backend task remains running. Browser-cancelled crop requests seen during QA
are handled without attempting a second response on a closed connection.
