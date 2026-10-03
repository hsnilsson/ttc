# Public guide and download delivery

The public guide is in `site/`; the loopback application stays in `web/`.
`scripts/build-pages.ps1` stages the guide, stylesheet, two explicitly selected
README screenshots and the browser demo at `demo/`. It does not publish DNGs,
local jobs, native logs, build tools or executable files. Use a fresh output
destination for each build.

The Pages workflow deploys main through the `github-pages` environment. Enable
GitHub Actions as the repository's Pages source. The public address is
https://hsnilsson.github.io/ttc/. There are no browser scripts, external fonts,
tracking or image uploads in the guide. A restrictive HTML CSP blocks script,
object, form and connection requests. The optional demo has a separate policy
allowing same-origin scripts/assets and local blob images for merged crops;
it has no analytics, uploads or native backend. GitHub Pages supplies hosting headers;
the HTML policy is not a replacement for a full HTTP-header policy.

Release builds use the existing Windows native builder and portable packager,
not the removed PyInstaller application. A manual workflow dispatch on main
accepts a new semantic-version tag; tag pushes also build releases. Each build
must pass service/viewer checks and packaged-runtime/engine/detector smoke tests
before publishing. All third-party workflow actions are pinned to commit IDs.
The ZIP checksum, GitHub provenance and packaged file hashes support inspection;
they do not replace signing, antivirus or independent security review.

Validation for the initial guide:

- 11 Python local service checks passed with the current native engine.
- 14 viewer tests and JavaScript syntax check passed.
- Portable packaging passed isolated service, engine and rotated detector checks.
- All 1,191 package payload file hashes verified, including launchers and runtime.
- Pages staging produced only the five intended public files.
- Browser inspection covered the desktop layout, 390 px mobile layout,
  section navigation and expanded sandbox instructions.
- `git diff --check` passed.

The Windows Sandbox configuration is documented using Microsoft's supported
options. A live Sandbox run and a separate clean Windows machine were not
tested in this task. Large PS16 memory needs still depend on the capture size.

## Interactive online demo

`site/demo/index.html` explicitly installs `demo.js` before the shared
`web/viewer.js`. Pages staging copies the current viewer, stylesheet and report
template into the demo, so its layout and interaction controls stay in sync with
the local application. Production and offline entry points do not load the
simulated transport. The demo does not call `/api/`, read session storage or
browse visitors' files; its folder picker shows a fictitious `D:\Demo captures`.
Reloading or Restart demo starts a fresh session. Staging versions the demo's
script and stylesheet URLs with their content hashes so browser caches cannot
reuse an older transport after deployment.

Import, preview/detection, comparison, cancellation, ROI/aperture corrections,
whole-capture selection and offline-report export are simulated in browser
memory. Stage delays are illustrative, never a performance benchmark. Scores
are deterministic example numbers; corrections alter the simulated setup but
reuse published example crops and illustrative scores. The page and exported
reports retain an explicit simulation warning. Full source-image export is
unavailable in this demo. Crop ZIPs and offline example reports are real browser
downloads assembled from the published assets.

The sample uses all 16 DNG capture labels and aperture assignments from the
user-selected series, starting with `_DSC3982-_DSC3997.dng`. Eight apertures have
two repeats each. A fresh native preview of the supplied reference DNG was
verified pixel-for-pixel against the selected existing TTC job. That job's
native log establishes each source filename. The overview and 80 aligned crops
are converted to lossless WebP, preserving crop dimensions and decoded pixels;
all 80 conversions were verified pixel-for-pixel. No original DNGs, private
source paths, EXIF metadata or native measurements are included. The complete
example image set is about 68 MB; detail assets load when comparison runs,
and repeat crops load when selected or exported.

To regenerate assets with Pillow, render the source reference using the same
native engine as the selected job, then run `scripts/build-demo-assets.py` with
`--source-dir`, `--job-dir`, `--destination` (a fresh folder) and
`--reference-preview`. Review the generated sample and copy only `assets/`
and `sample.json` into `site/demo/`.

Run `node --test web/tests/viewer.test.cjs web/tests/demo.test.cjs` and syntax
checks for both JavaScript entry points. Stage with `scripts/build-pages.ps1`
and serve the resulting directory to check the guide and demo together.

Demo validation: 29 viewer/demo checks and all 11 local-service checks passed,
including native archive coverage. The staged Pages payload contains exactly
93 public files; shared viewer assets match their production sources. A real
68 MB example report ZIP passed CRC, manifest, privacy and all 80 crop-dimension
checks. Live browser checks covered fake folder browsing, automatic comparison,
heatmap/crop rendering, repeat override, retained zoom, ROI saves, cancellation
and a 390 px layout. A sample-before-viewer loading-order regression test covers
ZIP-writer registration for report downloads.
