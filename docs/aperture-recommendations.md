# Aperture recommendations

The shared live, demo and offline viewer derives **best center**, **best corners**,
and **best balanced** from the current whole-capture selections. Older manifests
work without additional fields. Recommendations compare rendered detail in this
capture series, not calibrated MTF, optical quality percentages, or statistical
confidence. The public demo uses simulated measurements.

## Normalize each target pattern separately

For region r, let M_r be the largest finite, nonnegative accepted sharpness score
in the **selected** captures at assigned apertures. The normalized region ratio
at aperture a is q_(a,r) = sharpness_(a,r) / M_r. A positive M_r is required;
a region with only zero or missing scores provides no usable reference.
Rejected regions, unknown apertures and unselected repeats never set M_r.
Clipping-warning scores remain eligible with a visible warning.

This multiplicative normalization preserves each region's aperture ordering.
Changing the units or gain of one target pattern does not change the aggregate
ranking. It prevents a pattern with larger raw scores from dominating. It does
not remove exposure, processing, target, alignment or capture artifacts. The
references depend on this series and its selections; changing either can change
all normalized scores. Compare the same target positions with consistent capture
and rendering settings. Raw ROI scores and their heatmap remain available.

- **Center:** q_center.
- **Corners:** (q_tl + q_tr + q_bl + q_br) / 4.
- **Balanced:** 0.5 * q_center + 0.5 * corners.

Every corner has equal weight. Center and the corner group have equal weight in
balance; each corner therefore contributes 12.5%. This is an explicit preference
for center versus corner coverage. A mean rewards average corner detail and can
hide a weak corner: inspect individual rows and crops for flatness/asymmetry.
The viewer shows these ratios multiplied by 100 as **normalized points**. They
are not quality percentages. No raw cross-pattern sum is displayed.

## Completeness and close choices

Center needs its one valid region; corners need all four; balance needs all five.
Missing/rejected regions or nonpositive references leave the affected score empty.
There is no averaging over surviving corners or borrowing from another repeat.
The card lists excluded apertures and reasons. A manual selection can leave center
available while corner/balanced summaries are incomplete. A group with no selected
capture contributes no scores. At least two complete candidates are required
for each recommendation; a lone candidate can show a score but no winner.
A recommendation among remaining candidates does not rank excluded apertures.

Scores within 1e-12 of the highest are exact numerical ties. All choices within
0.02 of the highest normalized aggregate are shown as close choices, including
exact ties. This two-point threshold is a practical display heuristic. It is not
a measurement uncertainty estimate or significance test. The table stars exact
highest scores and separately labels close choices; no tie is broken arbitrarily.

## Whole captures, repeats and caveats

Automatic capture selection remains the service's existing rule: select one
complete repeat at each aperture by its weakest within-aperture regional ratio.
Aperture recommendations then compare those selected captures across apertures.
Browsing another repeat changes only the detail preview. **Use this whole capture**
changes the selection and recomputes every recommendation/reference together.
Manual selection is flagged in live, demo and offline reports. Offline changes
apply only to the current viewing session and do not rewrite the saved report.

For each recommendation, each eligible repeat is scored as one whole capture
using the same selected-capture references. No imaginary best-of-each-region
capture is constructed. Repeat scores can exceed 1 if an unselected repeat has
more detail than the selected reference. Repeat min/max ranges are descriptive.
The viewer warns when any required region's observed repeat range exceeds 8% of
its mean, when fewer than two repeats can be scored, or when some repeats are
unusable. Center repeats need a valid center; corner/balance repeats need all
regions required by their metric. Existing raw ROI +/- remains the service's
half-range over complete five-region repeats, so availability can differ.

If a recommended/close candidate's observed aggregate repeat range overlaps
another comparable aperture's range and at least one range varies, the card warns
that the order may change. This is an observed-range check, not a probability,
confidence interval, or proof of a robust winner. Partial repeats can still expose
regional disagreement, but cannot set aggregate repeat ranges. Clipping warnings
in selected regions and repeats stay visible. Review crops and these caveats
before using a recommendation.

## Verification

`node --test web/tests/recommendations.test.cjs web/tests/viewer.test.cjs web/tests/demo.test.cjs`
checks normalization under independent pattern scaling, distinct center/corner/
balance choices, invalid/zero/missing data, exact/near ties, whole-repeat scoring,
repeat disagreement/overlap, clipping, overrides and legacy manifest adaptation.
`python -B tests/local_checks.py` checks that automatic whole-capture selection
rejects nonfinite/negative scores and duplicate region IDs while preserving an
explicit manual override. The shared rendering and exported viewer carry the
same method; there is no second server-side recommendation algorithm.

Local QA (2026-10-05): all 37 Node checks and all 12 service checks passed.
Service integration used the existing v1.3.3 native engine with the current
Python service and synthetic PNGs, including report export. The synthetic offline
viewer and staged public demo were inspected in the Codex browser: recommendation
buttons selected the matching column/detail, close choices stayed visible, the
repeat-overlap disclosure listed affected apertures, and an offline whole-capture
override updated the table and manual-selection flag. No real lens accuracy,
new native build, release packaging, or deployment is claimed by these checks.
