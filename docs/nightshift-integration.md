# Nightshift integration — 2026-09-21

Integrated performance commits `0990441`, `4218f96` and ROI analysis commit
`037c95b`, starting from local main `66803a8`. Existing main history is preserved.

## Results

- Correct full-resolution LibRaw RGB rendering replaces invalid RAW-byte copying.
- Measured corrected-C baseline median: 32.194 to 22.669 seconds on a 244 MP
  DNG (29.6% less time); peak working set 5131.86 to 4433.73 MiB. A second
  DNG measured 34.027 to 22.895 seconds. Source and decoded composite hashes
  matched in all comparisons. These are warm-cache measurements, not a
  comparison with the older Python release. See BENCHMARKS.md.
- Reusable named ROIs, optional conservative integer-translation tracking,
  contrast/detail metrics, clipping warnings, HTML and CSV reports.
- Standalone Windows executable with system DLL dependencies; reproducible
  checksum-pinned dependency build. License notices accompany the build.

## Combined verification

Built merged ttc-simple.c with GCC, LibRaw 0.21.2 and libdeflate 1.25 using the
performance task's verified static dependencies. Decoder PNG/malformed-DNG
checks, exhaustive synthetic crop-coordinate/PNG checks, and ROI synthetic/CLI
checks passed. ROI fixture initializer was updated for the decoder ownership
field; the warning-enabled ROI test compilation is clean.

Ran the combined executable with examples/vlads4-19136x12752.roi, --track 8,
and read-only D:/camera scanning/vlads4/_DSC3982-_DSC3997.dng and
_DSC3998-_DSC4013.dng. Both decode to 19136 x 12752. All ten rows accepted;
second-frame shifts are (0,1) for all five ROIs. Metrics exactly match the
feature task's validated report. Coordinator inspected the reference image.
All generated reports and executable are under ignored build/:

- build/ttc-simple.exe
- build/licenses/
- build/combined-real-stack/report.html
- build/combined-real-stack/report.csv

README merge conflict resolved by keeping current build/rendering instructions
and adding ROI usage, without reintroducing outdated memory/size claims.
No source images changed. No remote push or GitHub discussion writes.

## Scope and tomorrow's decisions

Analysis is relative rendered-image detail, not calibrated MTF/lp/mm or an
aperture winner. Regions are configured in a text file; there is no interactive
selection UI. Tracking does not handle scale, rotation or subpixel motion.
RGB8, daylight WB and fixed processing are deliberate current defaults.
Potential next steps: interactive ROI selection, broader geometry tracking,
calibrated USAF analysis/fringing, and a chosen scientific/color workflow.
See docs/roi-analysis.md and docs/roi-validation.md for detailed limitations.

Task worktrees and ignored benchmark/report artifacts are retained for review;
cleanup must preserve those artifacts and avoid any still-active task worktree.
