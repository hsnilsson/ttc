"""TTC local-only CLI and HTTP service. Feature detection needs OpenCV/NumPy."""
from __future__ import annotations

import argparse
import copy
import csv
import html
import json
import math
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
import statistics
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent.parent
REGIONS = ('center', 'tl', 'tr', 'bl', 'br')
ALIASES = dict(zip(('center', 'top_left', 'top_right', 'bottom_left', 'bottom_right'), REGIONS))
ALIASES.update({k+'_usaf':v for k,v in list(ALIASES.items())})
GOOD = {'reference', 'fixed', 'tracked', 'clipping-warning'}
CREATE_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


def browse_folders(value=None):
    """List local folders inside the authenticated UI, without an OS dialog."""
    if value is not None and not isinstance(value, str):
        raise ValueError('Folder path must be a string')
    path = Path(value.strip()).expanduser() if value and value.strip() else Path.home()
    path = path.resolve(strict=True)
    if not path.is_dir():
        raise ValueError('Choose a folder, not a file')
    folders, image_count, skipped = [], 0, 0
    for entry in path.iterdir():
        try:
            if entry.is_dir():
                folders.append(dict(name=entry.name, path=str(entry)))
            elif entry.is_file() and entry.suffix.lower() in ('.dng', '.png', '.jpg', '.jpeg'):
                image_count += 1
        except OSError:
            skipped += 1
    folders.sort(key=lambda item: (item['name'].casefold(), item['name']))
    roots = [dict(name='Home', path=str(Path.home()))]
    if os.name == 'nt':
        import ctypes
        mask = ctypes.windll.kernel32.GetLogicalDrives()
        roots.extend(dict(name=f'{chr(65+i)}:', path=f'{chr(65+i)}:\\')
                     for i in range(26) if mask & (1 << i))
    else:
        roots.append(dict(name='Filesystem', path='/'))
    return dict(path=str(path), parent=str(path.parent) if path.parent != path else None,
                folders=folders, roots=roots, image_count=image_count, skipped=skipped)


def number(value):
    if isinstance(value, bool):
        raise ValueError('Expected a finite positive aperture')
    value = float(value)
    if not math.isfinite(value) or not 0.1 <= value <= 256:
        raise ValueError('Aperture must be between 0.1 and 256')
    return value


def aperture_from_name(name):
    match = re.search(r'(?:^|[ _-])f(?:/)?(\d+(?:[.,]\d+)?)(?=$|[ _.-])', Path(name).stem, re.I)
    return number(match[1].replace(',', '.')) if match else None


def native_json(engine, *args):
    done = subprocess.run([str(engine), *map(str, args)], capture_output=True,
                          text=True, errors='replace', creationflags=CREATE_FLAGS)
    if done.returncode:
        raise ValueError(done.stderr.strip() or 'Native inspection failed')
    for line in reversed(done.stdout.splitlines()):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            pass
    raise ValueError('Native engine did not return JSON')


def validate_rois(rois, width, height):
    if not isinstance(rois, list) or len(rois) != 5:
        raise ValueError('Exactly five ROIs are required')
    result = []
    for roi in rois:
        if not isinstance(roi, dict):
            raise ValueError('Each ROI must be an object')
        rid = ALIASES.get(roi.get('id'), roi.get('id'))
        values = [roi.get(k) for k in ('x', 'y', 'width', 'height')]
        if rid not in REGIONS or any(type(v) is not int for v in values):
            raise ValueError('ROI IDs and integer coordinates are required')
        x, y, w, h = values
        if min(x, y) < 0 or min(w, h) < 8 or x+w > width or y+h > height:
            raise ValueError('ROI is outside the decoded image or smaller than 8 pixels')
        result.append(dict(id=rid, x=x, y=y, width=w, height=h))
    if {r['id'] for r in result} != set(REGIONS):
        raise ValueError('ROI IDs must be unique')
    return sorted(result, key=lambda r: REGIONS.index(r['id']))


def read_rois(path):
    lines = [line.split() for line in Path(path).read_text(encoding='utf-8-sig').splitlines()
             if line.strip() and not line.lstrip().startswith('#')]
    if not lines or lines[0][0] != 'image' or len(lines[0]) != 3:
        raise ValueError('ROI configuration needs image WIDTH HEIGHT')
    width, height = map(int, lines[0][1:])
    rois = []
    for row in lines[1:]:
        if len(row) != 5:
            raise ValueError('Malformed ROI configuration')
        rois.append(dict(zip(('id', 'x', 'y', 'width', 'height'), [row[0], *map(int, row[1:])])))
    return width, height, validate_rois(rois, width, height)


def regroup(manifest, overrides):
    groups = []
    for frame in manifest['frames']:
        frame['selected'] = False
    apertures = sorted({f['aperture'] for f in manifest['frames'] if f['aperture'] is not None})
    for aperture in apertures:
        frames = [f for f in manifest['frames'] if f['aperture'] == aperture]
        usable = [f for f in frames if len(f['regions']) == 5 and all(
            r['status'] in GOOD and r['sharpness'] is not None for r in f['regions'])]
        flags = []
        for i, frame in enumerate(frames):
            frame['repeat'] = i+1
            frame['flags'] = [x for x in frame['flags'] if x not in ('repeat-disagreement', 'possible-shake')]
        for rid in REGIONS:
            vals = [next(r['sharpness'] for r in f['regions'] if r['id'] == rid) for f in usable]
            spread = (max(vals)-min(vals))/2 if len(vals) > 1 else None
            if spread is not None and statistics.mean(vals) > 0 and 2*spread/statistics.mean(vals) > .08:
                flags.append('repeat-disagreement')
            for f in frames:
                for r in f['regions']:
                    if r['id'] == rid:
                        r['uncertainty'] = spread
        chosen = None
        override = overrides.get(str(aperture))
        if override:
            chosen = next((f for f in frames if f['id'] == override), None)
            if chosen:
                flags.append('manual-selection')
        if chosen is None and usable:
            maxima = {rid: max(next(r['sharpness'] for r in f['regions'] if r['id'] == rid) for f in usable) for rid in REGIONS}
            def score(f):
                return min(r['sharpness']/max(maxima[r['id']], 1e-12) for r in f['regions'])
            chosen = max(usable, key=score)
            if len(usable) > 1:
                for f in usable:
                    if f != chosen and score(f) < .9:
                        f['flags'].append('possible-shake')
        if chosen:
            chosen['selected'] = True
        else:
            flags.append('no-trustworthy-capture')
        if len(usable) < 2:
            flags.append('repeat-spread-unavailable')
        if 'repeat-disagreement' in flags:
            for f in frames:
                f['flags'].append('repeat-disagreement')
        groups.append(dict(aperture=aperture, selected_frame_id=chosen['id'] if chosen else None,
                           frame_ids=[f['id'] for f in frames], flags=sorted(set(flags))))
    manifest['groups'] = groups


class Manager:
    def __init__(self, engine, workspace):
        self.engine = Path(engine).resolve()
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.jobs = {}
        self.lock = threading.RLock()
        self.decode_lock = threading.Lock()
        self.latest = None

    def snapshot(self, jid):
        with self.lock:
            job = self.jobs[jid]
            return copy.deepcopy({k: job[k] for k in ('schema_version', 'id', 'status', 'progress', 'error', 'result')})

    def save(self, job):
        (job['dir']/'manifest.json').write_text(json.dumps(job['result'], indent=2, allow_nan=False), encoding='utf-8')

    def create(self, data):
        if not isinstance(data.get('input_dir'), str) or not isinstance(data.get('apertures', {}), dict):
            raise ValueError('input_dir must be a path string; apertures must be an object')
        input_dir = Path(data['input_dir']).expanduser().resolve(strict=True)
        if not input_dir.is_dir():
            raise ValueError('Input must be a directory')
        paths = sorted((p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in ('.dng', '.png', '.jpg', '.jpeg')), key=lambda p:p.name.lower())
        if not paths or len(paths) > 256:
            raise ValueError('Input requires between 1 and 256 images')
        jid = secrets.token_hex(8)
        directory = self.workspace/jid
        directory.mkdir()
        frames = []
        warnings = []
        for i, path in enumerate(paths):
            try:
                metadata = native_json(self.engine, '--inspect', path)
            except ValueError as exc:
                raise ValueError(f'{path.name}: {exc}') from exc
            aperture = metadata.get('aperture')
            source = 'metadata'
            if not aperture or not math.isfinite(float(aperture)) or float(aperture) < .1:
                aperture = aperture_from_name(path.name)
                source = 'filename' if aperture else 'unknown'
            if path.name in data.get('apertures', {}):
                aperture = number(data['apertures'][path.name]); source = 'manual'
            frames.append(dict(id=f'f{i+1:04}', label=path.name, aperture=number(aperture) if aperture else None,
                               aperture_source=source, repeat=1, selected=False, status='ready',
                               flags=['aperture-required'] if aperture is None else [],
                               width=metadata['width'], height=metadata['height'], regions=[]))
        width, height = frames[0]['width'], frames[0]['height']
        for frame in frames:
            if (frame['width'], frame['height']) != (width, height):
                frame['flags'].append('dimension-mismatch')
                frame['status'] = 'review-required'
                warnings.append(frame['label']+': dimensions differ from reference; measurement will be rejected.')
        rois = []
        if data.get('roi_config'):
            rw, rh, rois = read_rois(data['roi_config'])
            if (rw, rh) != (width, height):
                raise ValueError('ROI configuration dimensions differ from reference')
        elif data.get('rois'):
            rois = validate_rois(data['rois'], width, height)
        track = data.get('track', 32)
        if type(track) is not int or track not in [0, *range(3, 33)]:
            raise ValueError('Tracking radius must be 0 or 3..32')
        manifest = dict(schema_version=1, reference=frames[0]['id'], preview_url=None, width=width, height=height, tracking_radius=track,
                        rois=rois, frames=frames, groups=[], warnings=warnings)
        job = dict(schema_version=1, id=jid, status='ready', progress=dict(completed=0,total=len(frames),message='Imported'),
                   error=None,result=manifest,dir=directory,paths=paths,track=track,overrides={},process=None,cancel=False,revision=0)
        regroup(manifest, {})
        with self.lock:
            self.jobs[jid] = job; self.latest = jid
            self.save(job)
        return self.snapshot(jid)

    def edit(self, jid, data):
        with self.lock:
            job = self.jobs[jid]
            if job['status'] == 'running':
                raise ValueError('Cancel or wait before editing')
            manifest = copy.deepcopy(job['result'])
            manifest.pop('export_url', None)
            overrides = dict(job['overrides'])
            if not isinstance(data.get('apertures', {}), dict) or not isinstance(data.get('selected', {}), dict):
                raise ValueError('Apertures and selected must be objects')
            track = data.get('track', job['track'])
            if type(track) is not int or track not in [0, *range(3, 33)]:
                raise ValueError('Tracking radius must be 0 or 3..32')
            for fid, aperture in data.get('apertures', {}).items():
                frame = next(f for f in manifest['frames'] if f['id'] == fid)
                frame['aperture'] = number(aperture); frame['aperture_source'] = 'manual'
                frame['flags'] = [x for x in frame['flags'] if x != 'aperture-required']
            for aperture, fid in data.get('selected', {}).items():
                aperture = number(aperture)
                if not any(f['id'] == fid and f['aperture'] == aperture for f in manifest['frames']):
                    raise ValueError('Selected capture does not belong to that aperture')
                overrides[str(aperture)] = fid
            rois = validate_rois(data['rois'], manifest['width'], manifest['height']) if 'rois' in data else manifest['rois']
            regions_changed = rois != manifest['rois']
            manifest['rois'] = rois
            if regions_changed or track != job['track']:
                for frame in manifest['frames']:
                    frame['regions'] = []; frame['status'] = 'ready'
                job['status'] = 'ready'
            job['track'] = track
            manifest['tracking_radius'] = track
            job['overrides'] = overrides
            job['result'] = manifest
            regroup(manifest, overrides); self.save(job)
        return self.snapshot(jid)

    def launch(self, jid, action, data=None):
        with self.lock:
            job = self.jobs[jid]
            if job['status'] == 'running' or not self.decode_lock.acquire(blocking=False):
                raise ValueError('Another operation is running; wait or cancel it')
            if action == 'analyze' and not job['result']['rois']:
                self.decode_lock.release()
                raise ValueError('Detect or define all five ROIs before analyzing')
            job.update(status='running',error=None,cancel=False)
            if action in ('analyze', 'detect', 'automatic', 'export'):
                job['result'].pop('export_url', None)
            if action == 'analyze':
                for frame in job['result']['frames']:
                    frame['regions'] = []; frame['status'] = 'ready'
                regroup(job['result'], job['overrides'])
            job['progress']['message'] = action
        threading.Thread(target=self.worker,args=(job,action,data or {}),daemon=True).start()
        return self.snapshot(jid)

    def run_native(self, job, args):
        with self.lock:
            if job['cancel']:
                raise InterruptedError('Cancelled')
            proc = subprocess.Popen([str(self.engine), *map(str,args)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                    text=True,errors='replace',creationflags=CREATE_FLAGS)
            job['process'] = proc
        lines = []
        started = 0
        with (job['dir']/'native.log').open('a',encoding='utf-8') as log:
            for line in proc.stdout:
                log.write(line); lines.append(line)
                if line.startswith('Analyzing '):
                    started += 1
                    with self.lock:
                        job['progress']['completed'] = min(job['progress']['total'], started-1)
                        job['progress']['message'] = f"Processing capture {started} of {job['progress']['total']}"
        code = proc.wait()
        proc.stdout.close()
        with self.lock:
            job['process'] = None
            if job['cancel']:
                raise InterruptedError('Cancelled')
        if code not in (0,2) or (code == 2 and args[0] != '--analyze'):
            raise RuntimeError('Native operation failed; inspect local native.log')
        return ''.join(lines), code

    def worker(self, job, action, data):
        try:
            if action == 'analyze':
                self.analyze(job)
            elif action == 'detect':
                self.detect(job)
            elif action == 'automatic':
                self.automatic(job)
            elif action == 'export':
                self.export(job, data.get('full_resolution', False))
            with self.lock:
                if job['cancel']:
                    raise InterruptedError('Cancelled')
                job['status'] = 'ready' if action == 'detect' else 'complete'
                job['progress']['message'] = 'Done'
                self.save(job)
        except InterruptedError:
            with self.lock:
                job['status'] = 'cancelled'; job['progress']['message'] = 'Cancelled'
                if action == 'export':
                    job['result'].pop('export_url', None)
        except Exception as exc:
            with self.lock:
                job['status'] = 'failed'; job['error'] = str(exc)
        finally:
            self.decode_lock.release()

    def cancel(self, jid):
        with self.lock:
            job = self.jobs[jid]
            job['cancel'] = True
            if job['process'] and job['process'].poll() is None:
                job['process'].terminate()
        return self.snapshot(jid)

    def automatic(self, job):
        with self.lock:
            job['progress'].update(completed=0, message='Finding target regions automatically…')
        self.detect(job)
        with self.lock:
            if job['cancel']:
                raise InterruptedError('Cancelled')
            if job['result'].get('detection', {}).get('status') != 'accepted' or len(job['result']['rois']) != 5:
                raise ValueError('Automatic comparison stopped: target regions could not be verified. Adjust and save the five regions, then Run comparison.')
            job['progress']['message'] = 'Regions found. Measuring and aligning the image series…'
        self.analyze(job)

    def detect(self, job):
        preview = job['dir']/'preview.png'
        if not preview.exists():
            temporary = job['dir']/('preview-'+secrets.token_hex(4)+'.png')
            try:
                self.run_native(job, ['--preview', job['paths'][0], temporary])
                temporary.replace(preview)
            finally:
                temporary.unlink(missing_ok=True)
        m = job['result']
        detector = Path(__file__).with_name('vlad_registration.py')
        with self.lock:
            if job['cancel']: raise InterruptedError('Cancelled')
            process = subprocess.Popen([sys.executable, '-I', '-B', str(detector), str(preview), str(m['width']), str(m['height'])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=CREATE_FLAGS)
            job['process'] = process
        try:
            output, error = process.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            process.terminate()
            output, error = process.communicate()
            raise TimeoutError('Feature registration timed out')
        finally:
            with self.lock: job['process'] = None
        if job['cancel']: raise InterruptedError('Cancelled')
        result = json.loads(output) if process.returncode == 0 else {"status":"manual-required","rois":[],"warnings":["Feature registration unavailable; manual regions required."]}
        with self.lock:
            m['preview_url'] = f"/jobs/{job['id']}/preview.png"
            m['detection'] = result
            detected = validate_rois(result['rois'],m['width'],m['height']) if result.get('rois') else []
            if detected:
                m['rois'] = detected
                for f in m['frames']:
                    f['regions'] = []; f['status'] = 'ready'
                regroup(m,job['overrides'])
            else:
                m['warnings'] = result.get('warnings', []) + ['Detection failed; existing saved regions and results were retained.']
                return
            m['warnings'] = result.get('warnings', [])

    def analyze(self, job):
        m = job['result']
        job['revision'] += 1
        run = job['dir']/f"run-{job['revision']}"
        config = job['dir']/'rois.conf'
        config.write_text(f"image {m['width']} {m['height']}\n"+''.join(
            f"{r['id']} {r['x']} {r['y']} {r['width']} {r['height']}\n" for r in m['rois']),encoding='ascii')
        args = ['--analyze',config,run]
        if job['track']:
            args += ['--track',job['track']]
        args += job['paths']
        job['progress']['completed'] = 0
        _, code = self.run_native(job,args)
        with (run/'report.csv').open(encoding='utf-8',newline='') as source:
            rows = list(csv.DictReader(source))
        if len(rows) != len(m['frames'])*5:
            raise RuntimeError('Native result has an incomplete row set')
        frames = copy.deepcopy(m['frames'])
        for i,frame in enumerate(frames):
            frame['regions'] = []
            for j,row in enumerate(rows[i*5:i*5+5]):
                def val(key):
                    return float(row[key]) if row[key] else None
                crop = run/f'frame-{i+1:04}-roi-{j+1:02}.png'
                frame['regions'].append(dict(id=row['roi'],**{k:int(row[k]) for k in ('x','y','width','height','dx','dy')},
                    sharpness=val('gradient_sharpness'),contrast=val('rms_contrast'),uncertainty=None,status=row['status'],
                    crop_url=f"/jobs/{job['id']}/{run.name}/{crop.name}" if crop.exists() else None))
            frame['status'] = 'ok' if all(r['status'] in GOOD for r in frame['regions']) else 'review-required'
            frame['flags'] = [f for f in frame['flags'] if f != 'clipping-warning']
            if any(r['status'] == 'clipping-warning' for r in frame['regions']):
                frame['flags'].append('clipping-warning')
        with self.lock:
            m['frames'] = frames
            job['progress']['completed'] = len(frames)
            m['preview_url'] = f"/jobs/{job['id']}/{run.name}/reference.png" if (run/'reference.png').exists() else None
            m['warnings'] = ['Some measurements were rejected; inspect capture status.'] if code else []
            regroup(m, job['overrides'])

    def export(self, job, full_resolution=False):
        def check_cancel():
            with self.lock:
                if job['cancel']:
                    raise InterruptedError('Cancelled')
        check_cancel()
        m = copy.deepcopy(job['result'])
        if not any(f['regions'] for f in m['frames']):
            raise ValueError('Analyze before exporting')
        serial = secrets.token_hex(4)
        out = job['dir']/('share-'+serial)
        out.mkdir(); (out/'assets').mkdir()
        prefix = f"/jobs/{job['id']}/"
        def asset(url):
            check_cancel()
            if not url:
                return None
            if not url.startswith(prefix):
                raise ValueError('Invalid generated asset URL')
            source = (job['dir']/url[len(prefix):]).resolve()
            if not source.is_relative_to(job['dir']):
                raise ValueError('Invalid asset path')
            name = source.parent.name+'-'+source.name
            shutil.copyfile(source, out/'assets'/name)
            return 'assets/'+name
        m['preview_url'] = asset(m.get('preview_url'))
        m.pop('export_url',None)
        for frame in m['frames']:
            for region in frame['regions']:
                region['crop_url'] = asset(region['crop_url'])
        if full_resolution:
            for i,frame in enumerate(m['frames']):
                check_cancel()
                if not frame['selected']:
                    continue
                if len(frame['regions']) != 5 or any(r['status'] not in GOOD for r in frame['regions']):
                    frame['aligned_status'] = 'unsupported-invalid-regions'
                    m['warnings'].append(frame['label']+': full image skipped; requires all five valid regions.')
                    continue
                shifts = [(r['dx'],r['dy']) for r in frame['regions']]
                if len(set(shifts)) != 1:
                    frame['aligned_status'] = 'unsupported-inconsistent-shifts'
                    m['warnings'].append(frame['label']+': full image skipped because ROI shifts disagree; aligned crops remain available.')
                    continue
                dx,dy = shifts[0]
                target = out/'assets'/f"{frame['id']}-aligned.png"
                self.run_native(job,['--export-aligned',job['paths'][i],target,dx,dy])
                frame['aligned_url'] = 'assets/'+target.name
                frame['aligned_status'] = 'integer-translation'
                frame['aligned_transform'] = dict(dx=dx,dy=dy,width=frame['width'],height=frame['height'],fill='black')
            m['warnings'].append('Full images use the common integer ROI translation; no rotation or subpixel correction.')
        encoded = json.dumps(m,ensure_ascii=True,allow_nan=False).replace('<','\\u003c')
        (out/'manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
        web = ROOT/'web'
        template = web/'index.html'
        if template.exists():
            page = template.read_text(encoding='utf-8')
            page,count = re.subn(r'(<script\b[^>]*\bid=["\']ttc-manifest["\'][^>]*>).*?(</script>)',
                                lambda match:match[1]+encoded+match[2],page,flags=re.S)
            if not count:
                raise ValueError('Offline UI template lacks script#ttc-manifest')
            for path in web.iterdir():
                if path.is_file() and path.suffix in ('.js','.css','.svg'):
                    shutil.copyfile(path,out/path.name)
        else:
            page = '<!doctype html><meta charset="utf-8"><title>TTC comparison</title><h1>TTC comparison</h1><p>Relative gradient sharpness; compare each region only with itself. Repeat spread is not calibrated uncertainty.</p>'
            for frame in m['frames']:
                page += '<h2>'+html.escape(frame['label'])+'</h2>'
                for r in frame['regions']:
                    page += '<p>'+html.escape(r['id'])+': '+str(r['sharpness'])+' ('+html.escape(r['status'])+')</p>'
                    if r['crop_url']:
                        page += '<img style="max-width:100%" src="'+r['crop_url']+'">'
        (out/'report.html').write_text(page,encoding='utf-8')
        archive = job['dir']/('share-'+serial+'.zip')
        try:
            with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
                for path in out.rglob('*'):
                    check_cancel()
                    if path.is_file():
                        info = zipfile.ZipInfo.from_file(path,path.relative_to(out).as_posix())
                        info.compress_type = zipfile.ZIP_STORED if path.suffix == '.png' else zipfile.ZIP_DEFLATED
                        with path.open('rb') as source, z.open(info,'w',force_zip64=True) as destination:
                            while block := source.read(1024*1024):
                                check_cancel()
                                destination.write(block)
        except BaseException:
            archive.unlink(missing_ok=True)
            raise
        with self.lock:
            check_cancel()
            job['result']['export_url'] = f"/jobs/{job['id']}/{archive.name}"
        return archive


class Handler(BaseHTTPRequestHandler):
    server_version = 'TTC-local/1'

    def log_message(self, *args):
        pass

    def reply(self, code, value):
        body = json.dumps(value,allow_nan=False).encode()
        self.send_response(code); self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(body)

    def trusted(self):
        expected = f'127.0.0.1:{self.server.server_port}'
        if self.headers.get('Host') != expected:
            return False
        origin = self.headers.get('Origin')
        return origin is None or origin == 'http://'+expected

    def do_GET(self):
        if not self.trusted():
            return self.reply(403,dict(error='Untrusted host or origin'))
        try:
            path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
            manager = self.server.manager
            if path == '/api/session':
                return self.reply(200,dict(token=self.server.token))
            if path == '/api/state':
                return self.reply(200,manager.snapshot(manager.latest) if manager.latest else None)
            if re.fullmatch('/api/jobs/[a-f0-9]{16}',path):
                return self.reply(200,manager.snapshot(path.split('/')[-1]))
            if path.startswith('/jobs/'):
                parts = path.split('/')
                if len(parts)<4 or parts[2] not in manager.jobs:
                    raise KeyError('Job missing')
                base = manager.jobs[parts[2]]['dir']
                file = (base/Path(*parts[3:])).resolve()
                relative = file.relative_to(base).as_posix()
                allowed = (relative == 'preview.png' or re.fullmatch(r'run-\d+/(?:reference|frame-\d{4}-roi-\d{2})\.png',relative)
                           or re.fullmatch(r'share-[a-f0-9]{8}\.zip',relative))
                if not allowed:
                    raise ValueError('Asset is not public')
            else:
                base = (ROOT/'web').resolve()
                file = (base/('index.html' if path == '/' else path.lstrip('/'))).resolve()
                if not file.is_relative_to(base) or file.suffix not in ('.html','.js','.css','.svg'):
                    raise ValueError('Invalid UI asset')
            with file.open('rb') as source:
                self.send_response(200)
                self.send_header('Content-Type',mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
                self.send_header('Content-Length',str(file.stat().st_size))
                self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Cache-Control','no-store')
                self.end_headers(); shutil.copyfileobj(source,self.wfile)
        except (ConnectionError,TimeoutError):
            return  # Browser navigation can cancel an in-flight crop download.
        except (KeyError,FileNotFoundError):
            self.reply(404,dict(error='Not found'))
        except (ValueError,OSError):
            self.reply(400,dict(error='Invalid asset request'))

    def do_POST(self):
        if not self.trusted() or not secrets.compare_digest(self.headers.get('X-TTC-Token',''),self.server.token):
            return self.reply(403,dict(error='Session token required'))
        try:
            if self.headers.get('Content-Type','').split(';')[0] != 'application/json':
                raise ValueError('Content-Type must be application/json')
            length = int(self.headers.get('Content-Length','0'))
            if length <= 0 or length > 65536:
                raise ValueError('JSON body must be 1..65536 bytes')
            self.connection.settimeout(10)
            data = json.loads(self.rfile.read(length))
            if not isinstance(data,dict):
                raise ValueError('Expected JSON object')
            manager = self.server.manager
            if self.path == '/api/shutdown':
                for jid in list(manager.jobs):
                    manager.cancel(jid)
                self.reply(200,dict(status='stopping'))
                threading.Thread(target=self.server.shutdown,daemon=True).start()
                return
            if self.path == '/api/browse':
                return self.reply(200,browse_folders(data.get('path')))
            if self.path == '/api/jobs':
                automatic = data.get('auto_run', False)
                if type(automatic) is not bool:
                    raise ValueError('auto_run must be true or false')
                snapshot = manager.create(data)
                if automatic:
                    snapshot = manager.launch(snapshot['id'], 'automatic')
                return self.reply(201,snapshot)
            match = re.fullmatch(r'/api/jobs/([a-f0-9]{16})/(analyze|detect|automatic|edit|cancel|export)',self.path)
            if not match:
                return self.reply(404,dict(error='Unknown API route'))
            jid,action = match.groups()
            if action == 'edit':
                result = manager.edit(jid,data)
            elif action == 'cancel':
                result = manager.cancel(jid)
            else:
                result = manager.launch(jid,action,data)
            self.reply(200,result)
        except (ConnectionError,TimeoutError):
            return
        except (ValueError,KeyError,TypeError,StopIteration,OSError) as exc:
            self.reply(400,dict(error=str(exc) or 'Invalid request'))


def make_server(manager, port=0):
    server = ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.manager = manager; server.token = secrets.token_urlsafe(32)
    server.daemon_threads = True
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['serve','analyze'])
    parser.add_argument('--engine',type=Path,default=ROOT/'build'/'ttc-simple.exe')
    parser.add_argument('--workspace',type=Path,default=ROOT/'build'/'local-jobs')
    parser.add_argument('--input'); parser.add_argument('--roi'); parser.add_argument('--output',type=Path)
    parser.add_argument('--apertures',type=Path,help='JSON object mapping filenames to corrected f-numbers')
    parser.add_argument('--track',type=int,default=32); parser.add_argument('--port',type=int,default=0)
    parser.add_argument('--no-browser',action='store_true'); parser.add_argument('--full-resolution',action='store_true')
    args = parser.parse_args()
    manager = Manager(args.engine,args.workspace)
    if args.command == 'serve':
        server = make_server(manager,args.port)
        url = f'http://127.0.0.1:{server.server_port}/'
        print(url,flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            for jid in list(manager.jobs):
                manager.cancel(jid)
        finally:
            server.server_close()
        return 0
    if not args.input or not args.roi or not args.output:
        parser.error('analyze requires --input --roi --output NEW_DIRECTORY')
    args.output.mkdir(parents=False,exist_ok=False)
    manager.workspace = args.output.resolve()
    job = manager.create(dict(input_dir=args.input,roi_config=args.roi,track=args.track,
                              apertures=json.loads(args.apertures.read_text()) if args.apertures else {}))
    jid = job['id']; manager.launch(jid,'analyze')
    try:
        while manager.snapshot(jid)['status'] == 'running':
            time.sleep(.2)
    except KeyboardInterrupt:
        manager.cancel(jid); return 130
    snapshot = manager.snapshot(jid)
    if snapshot['status'] != 'complete':
        print(json.dumps(snapshot)); return 1
    archive = manager.export(manager.jobs[jid],args.full_resolution)
    manager.save(manager.jobs[jid])
    print(json.dumps(dict(job=jid,manifest=str(manager.jobs[jid]['dir']/'manifest.json'),archive=str(archive))))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError,OSError) as error:
        print(str(error),file=sys.stderr); raise SystemExit(1)
