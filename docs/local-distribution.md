# Portable Windows distribution

Published packages are available at [GitHub Releases](https://github.com/hsnilsson/ttc/releases/latest).
Choose `TTC-windows-x64.zip`, not the source archives. The release workflow builds
the native engine, runs service/viewer checks, smoke-tests the isolated packaged
runtime and detector, and publishes the ZIP with `SHA256SUMS.txt` and GitHub
build-provenance attestation. Verify the ZIP with `Get-FileHash -Algorithm SHA256`
before extraction. Matching hashes detect changed bytes; they do not prove safety.
`distribution.json` records the source commit and SHA256 for every packaged file
except itself, including the runtime and launchers. It is provenance, not a signature.
See the [public guide](https://hsnilsson.github.io/ttc/#safety) for a read-only,
network-disabled Windows Sandbox trial. Signing and a clean-machine trial remain
separate from these automated package checks.

`local/package_windows.py` copies an existing Windows CPython runtime, the
native processing executable and license notices, the shared CLI/service, and
the browser assets into a new self-contained folder. It does not install
software, download dependencies, register services or contact external systems.
End users do not need a system Python installation.

Build after native compilation and GUI integration, from a writable checkout:

First install the pinned detector dependencies into ignored `build/python-deps`:
`python -m pip install --target build/python-deps -r local/requirements-vlad.txt`.

```powershell
& 'C:\Users\henri\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' local/package_windows.py `
  --runtime 'C:\Users\henri\.cache\codex-runtimes\codex-primary-runtime\dependencies\python' `
  --engine build/ttc-simple.exe `
  --licenses 'C:\Users\henri\.codex\worktrees\1380\ttc\build\licenses' `
  --output build/TTC-windows --zip
```

The output folder and optional sibling ZIP must not exist. Required GUI assets
are checked before creating output. The builder excludes third-party
unrelated site-packages, Python tools/tests/cache and the unused GUI toolkit; it retains
the standard library, extension DLLs, interpreter DLLs, CRT DLLs and licenses.
It smoke-tests the copied service with isolated Python and the copied native
engine. It adds pinned OpenCV/NumPy (including their license notices), the
compact grayscale reference and the registration module, then tests a rotated
reference in the isolated packaged runtime. A failed smoke test leaves the new folder for inspection; do not
distribute that folder. Use a fresh output path after correcting the failure.

Extract the entire ZIP. `Launch TTC.vbs` uses the included `pythonw.exe` to
open the local browser service with a hidden process. `ttc.cmd serve` runs the
same service with a console for diagnostics and Ctrl+C shutdown. `ttc.cmd
analyze ...` runs the same processing logic as the GUI. Jobs default to
`build/local-jobs` inside the extracted folder, so choose a writable location
with sufficient space. The launcher passes the included engine explicitly.

This is an unsigned Windows x64 folder distribution. Code signing, an installer,
automatic updates, clean-machine Windows testing, and cross-platform packaging
are not provided. Windows may show reputation warnings; organizational policy
may disable VBScript, in which case use `ttc.cmd serve`. Closing the browser
does not terminate the hidden service; use the UI's Stop service action
(POST /api/shutdown) or the console launcher for clean shutdown. Apart from the
documented grayscale detector reference, no input images,
private job paths, cached user sessions, or generated reports are bundled.

Retain the included notices when redistributing. Native library source
availability and license terms remain described in `licenses/native`; this
packager does not replace the native build's license obligations.
