"""Build an offline Windows TTC folder with a private Python runtime.

Copies existing files and validates them through a local loopback smoke test.
Does not install packages, download files, or contact external services.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def ignored(directory, names):
    return [name for name in names if name.lower() in {
        'site-packages', '__pycache__', 'test', 'tests', 'idlelib', 'ensurepip',
        'tkinter', 'turtledemo', 'venv', 'distutils',
        '_tkinter.pyd', 'tcl86t.dll', 'tk86t.dll',
    } or name.lower().endswith(('.pyc', '.pyo'))
        or (name.lower().startswith('opencv_videoio_ffmpeg') and name.lower().endswith('.dll'))]


def check_launcher(output: Path):
    """Exercise the real GUI executable, loopback service and clean shutdown."""
    log = output/'build'/'ttc-launch.log'
    process = subprocess.Popen([str(output/'TTC.exe'), '--no-browser'], cwd=output.parent)
    url = None
    succeeded = False
    try:
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError('Packaged TTC.exe stopped before the service was ready')
            if log.is_file():
                for line in log.read_text(encoding='utf-8', errors='replace').splitlines():
                    if line.startswith('http://127.0.0.1:'):
                        url = line.strip()
                        break
            if url:
                break
            time.sleep(.1)
        if not url:
            raise RuntimeError('Packaged TTC.exe did not start its local service within 30 seconds')
        with urllib.request.urlopen(url, timeout=10) as response:
            if b'TTC' not in response.read():
                raise RuntimeError('Packaged TTC.exe did not serve the browser interface')
        with urllib.request.urlopen(url+'api/session', timeout=10) as response:
            token = json.load(response)['token']
        request = urllib.request.Request(url+'api/shutdown', data=b'{}',
                    headers={'Content-Type':'application/json', 'X-TTC-Token':token})
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
        if process.wait(timeout=15):
            raise RuntimeError('Packaged TTC.exe did not shut down cleanly')
        succeeded = True
    finally:
        if process.poll() is None:
            # The launcher's Windows job object also stops its private children.
            process.kill()
            process.wait(timeout=10)
        if succeeded and log.exists():
            log.unlink()


def build(runtime: Path, engine: Path, licenses: Path, output: Path, web: Path, revisions=(), launcher=None):
    runtime, engine, licenses, web = [p.resolve() for p in (runtime, engine, licenses, web)]
    launcher = (launcher or ROOT/'build'/'TTC.exe').resolve()
    dependencies = ROOT/'build'/'python-deps'
    for path in (runtime/'python.exe', runtime/'LICENSE.txt',
                 runtime/'Lib'/'encodings'/'__init__.py', engine, launcher,
                 ROOT/'local'/'ttc_local.py', web/'index.html', web/'viewer.js', web/'viewer.css'):
        if not path.is_file():
            raise ValueError(f'Required distribution file is missing: {path}')
    if not licenses.is_dir() or not any(licenses.iterdir()):
        raise ValueError('Supply the native build licenses directory; notices are mandatory')
    output.mkdir(parents=False, exist_ok=False)
    private = output/'runtime'
    private.mkdir()
    # Copy the interpreter and runtime libraries, never installers/helper EXEs.
    # The service uses browser UI and still images, so omit Tcl/Tk and FFmpeg.
    for item in runtime.iterdir():
        if item.is_file() and (item.suffix.lower() in {'.dll', '._pth'}
                               or (item.name.lower().startswith('python') and item.suffix.lower() == '.zip')
                               or item.name in {'python.exe', 'LICENSE.txt'}):
            shutil.copy2(item, private/item.name)
    for directory in ('Lib', 'DLLs'):
        shutil.copytree(runtime/directory, private/directory, ignore=ignored)
    (output/'build').mkdir()
    shutil.copy2(engine, output/'build'/'ttc-simple.exe')
    shutil.copy2(launcher, output/'TTC.exe')
    shutil.copytree(licenses, output/'licenses'/'native')
    shutil.copy2(ROOT/'LICENSE', output/'licenses'/'TTC-LICENSE')
    (output/'local').mkdir()
    shutil.copy2(ROOT/'local'/'ttc_local.py', output/'local'/'ttc_local.py')
    if (ROOT/'local'/'vlad_registration.py').is_file():
        if not dependencies.is_dir():
            raise ValueError('Feature detector requires build/python-deps; install local/requirements-vlad.txt there first')
        shutil.copy2(ROOT/'local'/'vlad_registration.py', output/'local'/'vlad_registration.py')
        for asset in ('vlad-reference.npz',):
            if not (ROOT/'local'/asset).is_file(): raise ValueError(f'Feature detector asset missing: {asset}')
            shutil.copy2(ROOT/'local'/asset, output/'local'/asset)
        shutil.copytree(dependencies, private/'Lib'/'site-packages', dirs_exist_ok=True, ignore=ignored)
        for distribution in ('numpy-2.3.3.dist-info', 'opencv_python_headless-4.11.0.86.dist-info'):
            notices = list((dependencies/distribution).glob('LICENSE*'))
            if not notices:
                raise ValueError(f'Dependency license notices missing: {distribution}')
            destination = output/'licenses'/'python-deps'/distribution
            destination.mkdir(parents=True)
            for notice in notices:
                shutil.copy2(notice, destination/notice.name)
        shutil.copy2(ROOT/'local'/'requirements-vlad.txt', output/'licenses'/'python-deps'/'requirements-vlad.txt')
    shutil.copytree(web, output/'web', ignore=ignored)
    (output/'ttc.cmd').write_text('''@echo off
"%~dp0runtime\\python.exe" -I -B "%~dp0local\\ttc_local.py" %* --engine "%~dp0build\\ttc-simple.exe"
exit /b %errorlevel%
''', encoding='utf-8')
    (output/'README.txt').write_text('''TTC local comparison — portable Windows folder

Extract the complete folder before launch. Double-click TTC.exe to
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

TTC.exe starts the bundled runtime without a console. Use the browser's Stop
service action to stop it. Closing a browser tab alone does not stop it.
Startup/runtime errors show a dialog; details are in build/ttc-launch.log.
The console command also supports clean Ctrl+C shutdown. Keep TTC.exe with
the complete extracted folder; it is not a standalone single-file application.

This is an unsigned local build. Windows or enterprise policy may warn about
unsigned programs. The folder targets Windows x64 and is not a macOS/Linux package.
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
    detector_check = '''import sys, tempfile
from pathlib import Path
import cv2, numpy as np
assert cv2.__version__ == '4.11.0' and np.__version__ == '2.3.3'
sys.path.insert(0, sys.argv[1])
import vlad_registration as detector
with np.load(Path(sys.argv[1])/'vlad-reference.npz') as data:
    image=data['gray']
with tempfile.TemporaryDirectory() as tmp:
    preview=Path(tmp)/'test.png'
    cv2.imwrite(str(preview), cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE))
    result=detector.detect(preview,image.shape[0],image.shape[1])
    assert result['status']=='accepted' and len(result['rois'])==5, result
'''
    check = subprocess.run([str(private/'python.exe'), '-I', '-B', '-c', detector_check,
                            str(output/'local')], capture_output=True, text=True, timeout=60)
    if check.returncode:
        raise RuntimeError(f'Packaged feature detector smoke test failed: {check.stderr}')
    check_launcher(output)
    source = subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}','-C',str(ROOT),'rev-parse','HEAD'],
                            capture_output=True,text=True)
    tracked = subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}','-C',str(ROOT),'status','--porcelain','--untracked-files=no'],
                             capture_output=True,text=True)
    hashes = {path.relative_to(output).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(output.rglob('*'))
              if path.is_file()}
    (output/'distribution.json').write_text(json.dumps({
        'format_version': 1, 'platform': 'windows-x64',
        'runtime': 'private CPython; license in runtime/LICENSE.txt',
        'validation': ['isolated Python service --help', 'native engine --help', 'isolated OpenCV/NumPy versions and rotated reference detection', 'TTC.exe loopback UI/session and clean shutdown'],
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
    parser.add_argument('--launcher', type=Path, default=ROOT/'build'/'TTC.exe')
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
    build(args.runtime, args.engine, args.licenses, output, args.web,args.component_revision, args.launcher)
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
