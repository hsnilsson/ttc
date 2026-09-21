"""Build an offline Windows TTC folder with a private Python runtime.

Only copies existing files: does not install packages or access the network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def ignored(directory, names):
    return [name for name in names if name.lower() in {
        'site-packages', '__pycache__', 'test', 'tests', 'idlelib', 'ensurepip',
        'tkinter', 'turtledemo', 'venv', 'distutils',
    } or name.lower().endswith(('.pyc', '.pyo'))]


def build(runtime: Path, engine: Path, licenses: Path, output: Path, web: Path, revisions=()):
    runtime, engine, licenses, web = [p.resolve() for p in (runtime, engine, licenses, web)]
    for path in (runtime/'python.exe', runtime/'pythonw.exe', runtime/'LICENSE.txt',
                 runtime/'Lib'/'encodings'/'__init__.py', engine,
                 ROOT/'local'/'ttc_local.py', web/'index.html', web/'viewer.js', web/'viewer.css'):
        if not path.is_file():
            raise ValueError(f'Required distribution file is missing: {path}')
    if not licenses.is_dir() or not any(licenses.iterdir()):
        raise ValueError('Supply the native build licenses directory; notices are mandatory')
    output.mkdir(parents=False, exist_ok=False)
    private = output/'runtime'
    private.mkdir()
    # The supplied CPython installation is relocated intact except third-party
    # packages, developer tools, GUI toolkit and tests, none used by TTC.
    for item in runtime.iterdir():
        if item.is_file() and (item.suffix.lower() in {'.dll', '.exe', '.zip', '._pth'}
                               or item.name == 'LICENSE.txt'):
            shutil.copy2(item, private/item.name)
    for directory in ('Lib', 'DLLs'):
        shutil.copytree(runtime/directory, private/directory, ignore=ignored)
    (output/'build').mkdir()
    shutil.copy2(engine, output/'build'/'ttc-simple.exe')
    shutil.copytree(licenses, output/'licenses'/'native')
    shutil.copy2(ROOT/'LICENSE', output/'licenses'/'TTC-LICENSE')
    (output/'local').mkdir()
    shutil.copy2(ROOT/'local'/'ttc_local.py', output/'local'/'ttc_local.py')
    shutil.copytree(web, output/'web', ignore=ignored)
    (output/'Launch TTC.vbs').write_text('''Option Explicit
Dim shell, fs, base, quote, command
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
base = fs.GetParentFolderName(WScript.ScriptFullName)
quote = Chr(34)
shell.CurrentDirectory = base
command = quote & base & "\\runtime\\pythonw.exe" & quote & " -I -B " & quote & base & "\\local\\ttc_local.py" & quote & " serve --engine " & quote & base & "\\build\\ttc-simple.exe" & quote
shell.Run command, 0, False
''', encoding='utf-8')
    (output/'ttc.cmd').write_text('''@echo off
"%~dp0runtime\\python.exe" -I -B "%~dp0local\\ttc_local.py" %* --engine "%~dp0build\\ttc-simple.exe"
exit /b %errorlevel%
''', encoding='utf-8')
    (output/'README.txt').write_text('''TTC local comparison — portable Windows folder

Extract the complete folder before launch. Double-click Launch TTC.vbs to
open the browser interface. No Python installation, account, upload or
internet connection is required. Keep runtime, web, local, build and licenses
together. Jobs are saved under build/local-jobs in this folder; use a writable
location with ample free space. Originals are read only.

For visible diagnostics or to stop cleanly with Ctrl+C:
    ttc.cmd serve
For CLI help:
    ttc.cmd --help
For CLI processing:
    ttc.cmd analyze --input "D:\\images" --roi "D:\\regions.conf" --output "D:\\new-report"

Launch TTC.vbs starts a hidden pythonw.exe process. Use the browser's Stop
service action to stop it. Closing a browser tab alone does not stop it.
The console command also supports clean Ctrl+C shutdown.

This is an unsigned local build. Windows or enterprise policy may warn about
unsigned programs or disable VBScript. Use ttc.cmd serve if VBScript is
unavailable. The folder targets Windows x64 and is not a macOS/Linux package.
The native decoder and private Python runtime retain their license notices.
''', encoding='utf-8')
    # Run with isolated mode so a developer's installed packages cannot mask
    # a missing stdlib module in the packaged runtime.
    check = subprocess.run([str(private/'python.exe'), '-I', '-B',
                            str(output/'local'/'ttc_local.py'), '--help'],
                           capture_output=True, text=True, timeout=30)
    if check.returncode:
        raise RuntimeError(f'Packaged runtime smoke test failed: {check.stderr}')
    check = subprocess.run([str(output/'build'/'ttc-simple.exe'), '--help'],
                           capture_output=True, text=True, timeout=30)
    if check.returncode:
        raise RuntimeError(f'Packaged engine smoke test failed: {check.stderr}')
    source = subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}','-C',str(ROOT),'rev-parse','HEAD'],
                            capture_output=True,text=True)
    tracked = subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}','-C',str(ROOT),'status','--porcelain','--untracked-files=no'],
                             capture_output=True,text=True)
    hashes = {path.relative_to(output).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
              for path in [output/'local'/'ttc_local.py', output/'build'/'ttc-simple.exe', *sorted((output/'web').glob('*'))]
              if path.is_file()}
    (output/'distribution.json').write_text(json.dumps({
        'format_version': 1, 'platform': 'windows-x64',
        'runtime': 'private CPython; license in runtime/LICENSE.txt',
        'validation': ['isolated Python service --help', 'native engine --help'],
        'signed': False,
        'source_commit': source.stdout.strip() if source.returncode == 0 else None,
        'tracked_source_dirty': bool(tracked.stdout.strip()) if tracked.returncode == 0 else None,
        'component_revisions': list(revisions),
        'sha256': hashes,
    }, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True, help='Existing Windows CPython directory')
    parser.add_argument('--engine', type=Path, default=ROOT/'build'/'ttc-simple.exe')
    parser.add_argument('--licenses', type=Path, required=True, help='Native build notices directory')
    parser.add_argument('--web', type=Path, default=ROOT/'web')
    parser.add_argument('--output', type=Path, required=True, help='New destination directory')
    parser.add_argument('--zip', action='store_true', help='Also create a new sibling .zip')
    parser.add_argument('--component-revision', action='append', default=[], help='Additional component provenance, e.g. detector=COMMIT')
    args = parser.parse_args()
    output = args.output.resolve()
    archive = output.with_name(output.name+'.zip')
    if args.zip and archive.exists():
        parser.error(f'Archive already exists: {archive}')
    build(args.runtime, args.engine, args.licenses, output, args.web,args.component_revision)
    if args.zip:
        with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
            for path in sorted(output.rglob('*')):
                if path.is_file():
                    package.write(path, Path(output.name)/path.relative_to(output))
    print(output)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
