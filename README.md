# Test Target Cropper (native C)

Create a lossless PNG composite containing a center crop and four corner crops
for comparing lens sharpness and film/sensor flatness. Source pixels are copied
at 1:1 resolution; there is no resizing or JPEG recompression.

## Windows build

Run `build-simple.bat`, or from PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build-windows.ps1
.\build\ttc-simple.exe 'D:\photos' -o .\output
```

The build script downloads checksum-pinned portable tools and source dependencies
into ignored `build/`, builds static libraries, and creates `build/ttc-simple.exe`.
It does not install system software or require `C:\libraw`. The first build needs
network access and disk space for the compiler. Subsequent builds reuse downloads.
The executable uses Windows system DLLs; no separately installed LibRaw or
libdeflate DLL is required. Keep the generated dependency license notices when
redistributing it. See [benchmark report](BENCHMARKS.md) for measured performance
and [test instructions](tests/README.md) for reproduction.

PNG encoding uses libdeflate with adaptive PNG filtering. This changes compression
bytes and file size, not decoded pixel values. A manual build without
`TTC_LIBDEFLATE` falls back to the original stb encoder.

## DNG rendering

DNGs go through LibRaw unpacking, processing and RGB bitmap export at full
resolution. Embedded previews and half-size decoding are never substituted.
Rendering uses daylight white balance, sRGB primaries, LibRaw's default gamma
curve/demosaic quality, fixed brightness, and metadata orientation. Automatic
white balance, automatic brightness and content-dependent white-level adjustment
are disabled so target brightness does not drive per-shot normalization.
Daylight WB may differ visibly from the camera's selected WB. Camera metadata
and calibration still affect rendering; this is RGB8 analysis output, not a
linear scientific RAW export or a color-managed reproduction workflow.

Earlier native code copied 16-bit RAW bytes as RGB8 without proper processing.
Its output was invalid and cannot serve as a color or performance reference.
The corrected output intentionally differs from that version.

Processing is sequential across files. A 244 MP DNG still requires several GB of
RAM during rendering. Decoded dimensions reflect LibRaw's active image and camera
orientation, not necessarily the entire sensor storage rectangle or DNG DefaultCrop.

## Usage

```powershell
.\build\ttc-simple.exe                 # Current directory
.\build\ttc-simple.exe 'D:\photos'     # Directory of PNG/JPG/DNG files
.\build\ttc-simple.exe . -o results    # Existing parent, create output directory
```

The output is a square canvas: center at the top, left/right corner pairs in
two rows below it, black padding in unused areas. The layout and crop coordinates
are unchanged by the performance work. Files are read from the selected directory,
not recursively. The legacy command-line scanner has narrower format support
than the underlying stb loader; use `.png`, `.jpg` or `.dng` inputs.

## Compare a stack with reusable ROIs

`ttc-simple --analyze target.roi new-results f4.dng f5.6.dng f8.dng` applies
named pixel-coordinate regions across a stack and produces an HTML report and
CSV with relative sharpness, contrast, clipping, and optional translation
tracking. See [ROI analysis usage and limitations](docs/roi-analysis.md).
These measurements are relative image-detail proxies, not calibrated lp/mm.

## License

TTC is MIT licensed; see [LICENSE](LICENSE). Dependencies retain their own
licenses. Build sources and generated binaries are excluded from Git.
