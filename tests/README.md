# Decoder verification

Windows release package checks: `python -B tests/package_checks.py
build/TTC-windows-x64.zip` extracts into a temporary folder containing spaces
and Swedish characters. It checks file hashes and removed payloads, launches
`TTC.exe` without developer Python/PATH dependencies, analyzes synthetic PNGs
through the actual local API/native engine, exports a private-path-free report,
and verifies clean shutdown and child cleanup when the launcher is terminated.

Local service checks: `python tests/local_checks.py` verifies request/path
guards, aperture fallback, whole-capture selection and repeat spread. With
`build/ttc-simple.exe` present it also exercises native analysis, manual edits,
ROI invalidation, full-image export and portable ZIP assets. Build
`tests/export_checks.c` like `tests/roi_checks.c` to check integer translations,
black fill, extreme displacements, exclusive output creation and full-detail
crop pixels. Python 3.10+ is required for the service checks.

From the repository root in PowerShell, after `build-windows.ps1`:

```powershell
$raw = 'build/dependencies/libraw-sequential/LibRaw-0.21.2'
build/w64devkit/bin/gcc.exe -std=c99 -O2 -fno-strict-aliasing "-I$raw" tests/verify_decoder.c -o build/verify_decoder.exe "$raw/lib/libraw.a" -lstdc++ -lws2_32
build/verify_decoder.exe
build/verify_decoder.exe 'D:/path/to/full-resolution.dng' --reference
```

The quick invocation verifies exact synthetic PNG pixels and rejects malformed
DNG input. A DNG argument additionally prints output dimensions and FNV-1a-64
over every RGB byte. `--reference` decodes again using an independently configured
LibRaw instance and the PPM file writer, then compares dimensions and a streaming
hash of all output pixels. A mismatch returns a nonzero exit status. Include a
camera-rotated DNG to exercise orientation; dimensions come from the rendered
output, not the raw sensor buffer.

Both paths request full resolution, camera/as-shot white balance, RGB8 sRGB output,
fixed brightness, no automatic brightness and no content-dependent maximum
adjustment. Default LibRaw gamma, demosaic and camera orientation apply. This
checks TTC's extraction against LibRaw's separate output writer, not LibRaw's
color science against an external reference; the hash is a regression check,
not a cryptographic proof.

Temporary PNG, invalid DNG and reference PPM files are uniquely reserved in the
Windows temporary directory and deleted afterward. A 244 MP reference PPM needs
about 732 MB free disk space. The app RGB allocation is released before reference
decoding and the PPM is read in 64 KiB chunks. Run real-DNG checks sequentially,
away from benchmark timing windows. Abrupt termination may leave temporary files.

Do not commit executables, generated images, or source DNGs.

## Composite coordinates and PNG encoding

```powershell
build/w64devkit/bin/gcc.exe -O2 -fno-strict-aliasing -DNO_LIBRAW -DTTC_LIBDEFLATE '-Ibuild/dependencies/libdeflate-1.25' tests/verify_composite.c -o build/verify_composite.exe build/libdeflate-static/libdeflate.a
build/verify_composite.exe
```

This verifies every output pixel against a coordinate oracle, including black
padding, odd/even dimensions, portrait/landscape and tiny inputs. Omit
`-DTTC_LIBDEFLATE`, its include and its archive to test the stb fallback.

## Performance and full-output regression

After `build-windows.ps1`, compile the benchmark (PowerShell):

```powershell
$raw = 'build/dependencies/libraw-sequential/LibRaw-0.21.2'
build/w64devkit/bin/gcc.exe -std=c99 -O2 -fno-strict-aliasing -static -DTTC_LIBDEFLATE "-I$raw" '-Ibuild/dependencies/libdeflate-1.25' tests/benchmark.c -o build/benchmark.exe "$raw/lib/libraw.a" build/libdeflate-static/libdeflate.a -lstdc++ -lws2_32 -lpsapi
build/benchmark.exe 'D:/photos/sample.dng' 'build/composite.png'
```

The harness measures wall-clock loading and composite creation separately using
Windows performance counters. Hashing/PNG rereading is outside timed sections.
It reports full RGB source and decoded composite FNV-1a hashes and process peak
working set measured before verification. Process startup and source hashing
are excluded from the reported phase sum. Peak working set includes hashing.
Use the same LibRaw/compiler/settings for baseline and optimized builds. Repeat
alternating baseline/optimized runs sequentially, with other image jobs stopped.
No cache flushing is performed, so report results as warm-cache measurements.

`TTC_SOURCE` can select a saved baseline source, for example:

```powershell
git show 0990441:ttc-simple.c | Set-Content build/correct-baseline.c
build/w64devkit/bin/gcc.exe -std=c99 -O2 -fno-strict-aliasing -I. '-DTTC_SOURCE="../build/correct-baseline.c"' "-I$raw" tests/benchmark.c -o build/benchmark-baseline.exe "$raw/lib/libraw.a" -lstdc++ -lws2_32 -lpsapi
```

Correctness checks compare decoded pixels, never compressed PNG bytes. See
[BENCHMARKS.md](../BENCHMARKS.md) for the measured source commit and results.
The harness is Windows-specific; no Linux test run is claimed.
