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
native processing executable, `build/TTC.exe` launcher and license notices,
the shared CLI/service, and browser assets into a new self-contained folder. It does not install
software, download dependencies, register services or contact external systems.
End users do not need a system Python installation.

Build after native compilation and GUI integration, from a writable checkout:

First install the pinned detector dependencies into ignored `build/python-deps`:
`python -m pip install --target build/python-deps -r local/requirements-vlad.txt`.

```powershell
$runtime = python -c "import sys; print(sys.base_prefix)"
python -B local/package_windows.py `
  --runtime "$runtime" `
  --engine build/ttc-simple.exe `
  --licenses build/licenses `
  --output build/TTC-windows --zip
```

The Windows build compiles both the engine and the small native `TTC.exe`
launcher. `--launcher PATH` can select a separately built launcher.

The output folder and optional sibling ZIP must not exist. Required GUI assets
are checked before creating output. The builder excludes third-party
unrelated site-packages, Python tools/tests/cache and the unused GUI toolkit; it retains
the standard library, required extension DLLs, interpreter DLLs, CRT DLLs and licenses.
It excludes Python installers/helper executables, Tcl/Tk DLLs and `_tkinter`,
and OpenCV's unused FFmpeg video DLL. NumPy/OpenCV remain bundled for automatic
target detection; removing them would change functionality.
It smoke-tests the copied service with isolated Python and the copied native
engine. It adds pinned OpenCV/NumPy (including their license notices), the
compact grayscale reference and the registration module, then tests a rotated
reference in the isolated packaged runtime. A failed smoke test leaves the new folder for inspection; do not
distribute that folder. Use a fresh output path after correcting the failure.
It also starts the actual `TTC.exe` with `--no-browser`, retrieves the local UI
and session token, and verifies authenticated shutdown and a successful exit.
The generated startup log is removed before checksumming/archiving.
`python -B tests/package_checks.py build/TTC-windows.zip` then checks the
extracted ZIP's hashes, trimmed contents, executable analysis/export with
developer Python/PATH hidden, and runtime termination when the launcher stops.

Extract the entire ZIP. Double-click `TTC.exe` to open the local browser service
without a console. This native launcher runs the included `python.exe` directly,
using its own folder even when launched from another working directory.
It does not need VBScript, system Python, or a shell. `TTC.exe` must remain with
the complete extracted package; it is not a single-file application.
Startup/runtime failures show an error dialog, with diagnostics saved in
`build/ttc-launch.log`. The launcher supervises its runtime and child processes;
they stop if the launcher is terminated. `ttc.cmd serve` runs the
same service with a console for diagnostics and Ctrl+C shutdown. `ttc.cmd
analyze ...` runs the same processing logic as the GUI. Jobs default to
`build/local-jobs` inside the extracted folder, so choose a writable location
with sufficient space. The launcher passes the included engine explicitly.

This is an unsigned Windows x64 folder distribution. Code signing, an installer,
automatic updates, clean-machine Windows testing, and cross-platform packaging
are not provided. Windows may show reputation warnings; organizational policy
may block unsigned executables. Closing the browser
does not terminate the hidden service; use the UI's Stop service action
(POST /api/shutdown) or the console launcher for clean shutdown. Apart from the
documented grayscale detector reference, no input images,
private job paths, cached user sessions, or generated reports are bundled.

Retain the included notices when redistributing. Native library source
availability and license terms remain described in `licenses/native`; this
packager does not replace the native build's license obligations.
