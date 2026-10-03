"""Verify the real LibRaw build patch across Windows/Unix line endings.

Usage: python -B tests/build_patch_checks.py build/LibRaw-0.21.2.tar.gz
"""
import argparse
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile


def check(archive):
    root = Path(__file__).resolve().parents[1]
    script = (root/'build-windows.ps1').read_text(encoding='utf-8-sig')
    start = script.index('function Enable-SelectiveDngTiles {')
    end = script.index('Enable-SelectiveDngTiles $rawRoot', start)
    function = script[start:end]+'\nEnable-SelectiveDngTiles $args[0]\n'
    with tarfile.open(archive) as package:
        source = package.extractfile('LibRaw-0.21.2/src/decoders/dng.cpp').read().decode()
    powershell = Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    with tempfile.TemporaryDirectory(prefix='TTC build patch ') as temporary:
        directory = Path(temporary)
        target = directory/'src'/'decoders'/'dng.cpp'
        target.parent.mkdir(parents=True)
        probe = directory/'patch.ps1'
        for script_ending in ('\n', '\r\n'):
            probe.write_bytes(function.replace('\n', script_ending).encode())
            for source_ending in ('\n', '\r\n'):
                target.write_bytes(source.replace('\n', source_ending).encode())
                command = [str(powershell), '-NoProfile', '-ExecutionPolicy', 'Bypass',
                           '-File', str(probe), str(directory)]
                result = subprocess.run(command, capture_output=True, text=True, timeout=20)
                if result.returncode:
                    raise RuntimeError(f'Line-ending combination failed: {result.stderr}')
                patched = target.read_bytes()
                text = patched.decode('utf-8-sig')
                assert text.count('extern "C" int ttc_selective_dng_tile_needed') == 1
                assert text.count('!ttc_selective_dng_tile_needed(tcol, trow, tile_width, tile_length)') == 1
                result = subprocess.run(command, capture_output=True, text=True, timeout=20)
                assert result.returncode == 0, result.stderr
                assert target.read_bytes() == patched, 'Applying the patch twice changed the source'
        target.write_bytes(b'Unexpected upstream source\n')
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        assert result.returncode != 0, 'Unrecognized source must fail'
        assert target.read_bytes() == b'Unexpected upstream source\n'
    print('LibRaw patch: four line-ending combinations, idempotency and context rejection passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    check(args.archive)
