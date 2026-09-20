# Contributing

Build the native Windows executable with `build-simple.bat` or
`powershell -NoProfile -ExecutionPolicy Bypass -File .\build-windows.ps1`.
Dependencies and generated artifacts belong in ignored `build/`.

Run the checks in [tests/README.md](tests/README.md). Decoder or performance
changes should include full-resolution DNG verification, decoded-pixel comparison,
and reproducible timings against a correct baseline. Avoid concurrent image
benchmarks. Never commit test photos, dependency sources or binaries.

Keep patches focused and preserve existing crop coordinates unless changing them
is the explicit purpose of the task. Record rendering policy changes clearly.

Contributions to this project are under its MIT license.
