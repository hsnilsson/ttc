"""Windows release checks against an extracted ZIP, not the developer runtime.

Usage: python -B tests/package_checks.py build/TTC-windows-x64.zip
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import time
import unittest
import urllib.request
import zipfile
import zlib


class PackageChecks(unittest.TestCase):
    def start(self):
        # Hide all developer Python packages and executables from the child.
        env = dict(os.environ, PATH=str(Path(os.environ['SystemRoot'])/'System32'),
                   PYTHONPATH='does-not-exist', PYTHONHOME='does-not-exist')
        log = self.root/'build'/'ttc-launch.log'
        log.unlink(missing_ok=True)
        process = subprocess.Popen([str(self.root/'TTC.exe'), '--no-browser'],
                                   cwd=self.root.parent, env=env)
        self.addCleanup(self.stop, process)
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            self.assertIsNone(process.poll(), 'Launcher exited before service startup')
            if log.exists():
                for line in log.read_text(encoding='utf-8', errors='replace').splitlines():
                    if line.startswith('http://127.0.0.1:'):
                        self.url = line.strip()
                        self.token = self.request('api/session')['token']
                        return process
            time.sleep(.1)
        self.fail('Executable did not start the service within 30 seconds')

    @staticmethod
    def stop(process):
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)

    def request(self, path, data=None):
        request = urllib.request.Request(self.url+path)
        if data is not None:
            request.data = json.dumps(data).encode()
            request.add_header('Content-Type', 'application/json')
            request.add_header('X-TTC-Token', self.token)
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)

    def completed(self, jid):
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            result = self.request('api/jobs/'+jid)
            if result['status'] != 'running':
                self.assertEqual(result['status'], 'complete', result)
                return result['result']
            time.sleep(.05)
        self.fail('Packaged native job timed out')

    def test_package_contents(self):
        manifest = json.loads((self.root/'distribution.json').read_text())
        self.assertTrue(manifest['sha256'])
        for relative, expected in manifest['sha256'].items():
            with self.subTest(file=relative):
                self.assertEqual(hashlib.sha256((self.root/relative).read_bytes()).hexdigest(), expected)
        self.assertFalse(list(self.root.rglob('*.vbs')))
        self.assertFalse(list(self.root.rglob('ttc-simple.exe')))
        self.assertEqual([p.name for p in (self.root/'runtime').glob('*.exe')], ['python.exe'])
        for pattern in ('*ffmpeg*.dll', 'tcl*.dll', 'tk*.dll', '_tkinter.pyd'):
            self.assertFalse(list(self.root.rglob(pattern)), pattern)
        for relative in ('TTC.exe', 'build/ttc-cli.exe', 'runtime/LICENSE.txt', 'licenses/TTC-LICENSE',
                         'licenses/python-deps/numpy-2.3.3.dist-info',
                         'licenses/python-deps/opencv_python_headless-4.11.0.86.dist-info'):
            self.assertTrue((self.root/relative).exists(), relative)
        # GUI subsystem proves that double-click launch needs no console window.
        executable = (self.root/'TTC.exe').read_bytes()
        pe_offset = struct.unpack_from('<I', executable, 0x3c)[0]
        self.assertEqual(struct.unpack_from('<H', executable, pe_offset+24+68)[0], 2)

    def test_executable_analysis_export_and_shutdown(self):
        process = self.start()
        with tempfile.TemporaryDirectory(prefix='TTC private input ') as temporary:
            inputs = Path(temporary)
            def chunk(tag, data):
                return struct.pack('>I', len(data))+tag+data+struct.pack('>I', zlib.crc32(tag+data))
            scan = b''.join(b'\0'+bytes((x*17+y*31+x*y%71)%190+30
                            for x in range(96) for _ in range(3)) for y in range(96))
            png = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB',96,96,8,2,0,0,0))
            png += chunk(b'IDAT', zlib.compress(scan))+chunk(b'IEND', b'')
            for name in ('f4_a.png', 'f4_b.png', 'f8_a.png'):
                (inputs/name).write_bytes(png)
            rois = [dict(id=rid,x=20,y=20,width=32,height=32)
                    for rid in ('center','tl','tr','bl','br')]
            snapshot = self.request('api/jobs', dict(input_dir=str(inputs),rois=rois,track=0))
            jid = snapshot['id']
            self.request('api/jobs/'+jid+'/analyze', {})
            manifest = self.completed(jid)
            self.assertEqual(len(manifest['frames']), 3)
            self.assertEqual(len(manifest['groups']), 2)
            self.assertTrue(all(len(f['regions']) == 5 for f in manifest['frames']))
            self.request('api/jobs/'+jid+'/export', {})
            manifest = self.completed(jid)
            with urllib.request.urlopen(self.url.rstrip('/')+manifest['export_url'], timeout=10) as response:
                report = response.read()
            with zipfile.ZipFile(io.BytesIO(report)) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn('report.html', archive.namelist())
                exported = archive.read('manifest.json')
                self.assertNotIn(str(inputs), exported.decode())
                self.assertNotIn(str(inputs), archive.read('report.html').decode())
                frames = json.loads(exported)['frames']
                self.assertEqual(len(frames), 3)
                crops = [region['crop_url'] for frame in frames for region in frame['regions']]
                self.assertEqual(len(crops), 15)
                for crop in crops:
                    pixels = archive.read(crop)
                    self.assertEqual(struct.unpack_from('>II', pixels, 16), (32, 32))
            self.assertTrue(all((inputs/name).read_bytes() == png for name in ('f4_a.png','f4_b.png','f8_a.png')))
        self.request('api/shutdown', {})
        self.assertEqual(process.wait(timeout=15), 0)

    def test_launcher_termination_stops_runtime(self):
        process = self.start()
        process.kill()
        process.wait(timeout=10)
        deadline = time.monotonic()+10
        while time.monotonic() < deadline:
            try:
                self.request('api/session')
            except OSError:
                return
            time.sleep(.1)
        self.fail('Killing TTC.exe left its private service running')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('These release checks require Windows')
    with tempfile.TemporaryDirectory(prefix='TTC package r\u00e4ksm\u00f6rg\u00e5s ') as temporary:
        with zipfile.ZipFile(args.archive) as archive:
            archive.extractall(temporary)
        PackageChecks.root, = [p for p in Path(temporary).iterdir() if p.is_dir()]
        # Inventory must run before the launch checks create logs and jobs.
        suite = unittest.TestSuite(PackageChecks(name) for name in
            ('test_package_contents', 'test_executable_analysis_export_and_shutdown',
             'test_launcher_termination_stops_runtime'))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(0 if result.wasSuccessful() else 1)
