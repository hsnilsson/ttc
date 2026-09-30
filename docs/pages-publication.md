# Public guide and download delivery

The public guide is in `site/`; the loopback application stays in `web/`.
`scripts/build-pages.ps1` stages only the guide, stylesheet and two explicitly
selected README screenshots. It does not publish local jobs, captures, reports,
build tools or executable files. Use a fresh output destination for each build.

The Pages workflow deploys main through the `github-pages` environment. Enable
GitHub Actions as the repository's Pages source. The public address is
https://hsnilsson.github.io/ttc/. There are no browser scripts, external fonts,
tracking or image uploads in the guide. A restrictive HTML CSP blocks script,
object, form and connection requests. GitHub Pages supplies hosting headers;
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
