"""Experimental single-spoke slanted-edge analysis, in original image pixels.

MTF Mapper is an optional external executable; no image is uploaded. Detection
may smooth an image, but measurement crops are integer copies, linearized only.
The conservative gates are engineering checks, not an ISO certification.
"""
from __future__ import annotations

import json
import csv
import hashlib
import math
import secrets
from pathlib import Path
import subprocess
import sys

DEPS = Path(__file__).resolve().parents[1] / 'build' / 'python-deps'
if DEPS.is_dir():
    sys.path.insert(0, str(DEPS))
import cv2
import numpy as np

CREATE_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
PROVENANCE = ('Experimental MTF Mapper single-edge measurement of the captured '
              'system, including target, pixel-shift reconstruction and rendering. '
              'Original pixels; inverse LibRaw default transfer curve; linear luminance. '
              'Units: cycles per output pixel, not sensor-plane lp/mm.')

# Centers/radii in the bundled 1600 x 1066 reference, projected using its
# feature-verified homography. Small central star is deliberately tested too.
STARS = [('inset_tl',430,228,82), ('inset_tr',1174,228,82),
         ('inset_bl',430,840,82), ('inset_br',1173,840,82),
         ('outer_tl',120,122,108), ('outer_tr',1480,122,108),
         ('outer_bl',120,945,108), ('outer_br',1480,945,108),
         ('center_small',753,487,12)]


def geometry(matrix, width, height):
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape != (3,3) or not np.isfinite(matrix).all():
        raise ValueError('Invalid registered chart transform')
    result = []
    for name,x,y,r in STARS:
        points = np.array([[x,y],[x-r-5,y-r-5],[x+r+5,y-r-5],
                           [x+r+5,y+r+5],[x-r-5,y+r+5]], dtype=float)
        homogeneous = np.column_stack((points,np.ones(5))) @ matrix.T
        if np.min(np.abs(homogeneous[:,2])) < 1e-8:
            raise ValueError('Invalid star projection')
        projected = homogeneous[:,:2] / homogeneous[:,2:]
        low = np.maximum(0,np.floor(projected[1:].min(axis=0))).astype(int)
        high = np.minimum([width,height],np.ceil(projected[1:].max(axis=0))).astype(int)
        if (high-low < 8).any():
            raise ValueError('Star is outside the source image')
        radius = float(np.mean(np.linalg.norm(projected[1:]-projected[0],axis=1))/math.sqrt(2)*r/(r+5))
        result.append(dict(id=name,x=int(low[0]),y=int(low[1]),width=int(high[0]-low[0]),
                           height=int(high[1]-low[1]),center=projected[0].tolist(),radius=radius))
    return result


def linear_luminance(bgr):
    """Invert LibRaw's default .45/4.5 curve before mixing RGB channels.

    Matches the toe/offset construction in LibRaw gamma_curve. RGB8 rounding
    is irreversible; this is rendered-image SFR, not a raw-sensor measurement.
    """
    low, high = 0., 1.
    for _ in range(48):
        toe = (low + high) / 2
        if ((toe / 4.5) ** -.45 - 1) / .45 - 1 / toe > -1:
            high = toe
        else:
            low = toe
    offset = toe * (1 / .45 - 1)
    encoded = np.arange(256, dtype=np.float64) / 255
    lut = np.where(encoded < toe, encoded / 4.5,
                   ((encoded + offset) / (1 + offset)) ** (1 / .45))
    return lut[bgr] @ np.array([.0722, .7152, .2126])


def line_candidates(gray, center, radius):
    """Find radial boundaries, then choose by geometry, never by sharpness."""
    cv2.setNumThreads(1)
    lines = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(gray)[0]
    if lines is None:
        return []
    center = np.asarray(center)
    found = []
    for raw in lines.reshape(-1, 4):
        a, b = raw.astype(float).reshape(2, 2)
        length = float(np.linalg.norm(b-a))
        if length < max(100, radius * .45):
            continue
        unit = (b-a) / length
        angle = math.degrees(math.atan2(unit[1], unit[0])) % 180
        slant = min(angle % 90, 90-angle % 90)
        if not 3 <= slant <= 7:
            continue
        normal = np.array([-unit[1], unit[0]])
        if abs(float((center-a) @ normal)) > max(12, radius*.025):
            continue
        if np.linalg.norm(a-center) < np.linalg.norm(b-center):
            a, b = b, a
        outer = float(np.linalg.norm(a-center))
        if not .8*radius < outer < 1.15*radius:
            continue
        found.append(dict(line=[*a.tolist(), *b.tolist()], angle=angle,
                          direction='vertical detail' if abs(unit[0]) > abs(unit[1]) else 'horizontal detail',
                          radial_angle=math.degrees(math.atan2(a[1]-center[1], a[0]-center[0])) % 360,
                          slant=slant))
    return sorted(found, key=lambda c: (abs(c['slant']-5), c['radial_angle']))


def edge_box(candidate, start=.03, stop=.15, margin=30):
    a, b = np.array(candidate['line']).reshape(2, 2)
    p, q = a+(b-a)*start, a+(b-a)*stop
    pad = np.array([margin, 0]) if abs(q[1]-p[1]) > abs(q[0]-p[0]) else np.array([0, margin])
    low = np.floor(np.minimum(p, q)-pad).astype(int)
    high = np.ceil(np.maximum(p, q)+pad).astype(int)+1
    # Keep the long-axis pixel centres inside the chosen segment. Extending
    # floor/ceil by one pixel here can silently reduce the opposite-side margin.
    along = 1 if pad[0] else 0
    low[along] = math.ceil(min(p[along], q[along]))
    high[along] = math.floor(max(p[along], q[along]))+1
    return [*low.tolist(), *high.tolist()]


def isolated_edge(linear, candidate, box):
    """Reject neighbouring transitions, clipping and non-flat plateaus."""
    x0, y0, x1, y1 = box
    if x0 < 0 or y0 < 0 or x1 > linear.shape[1] or y1 > linear.shape[0]:
        return 'Crop leaves the source image.'
    crop = linear[y0:y1, x0:x1]
    a, b = np.array(candidate['line']).reshape(2, 2) - (x0, y0)
    if abs(b[0]-a[0]) > abs(b[1]-a[1]):
        crop = crop.T  # Detection view only, never written as measurement input.
        a, b = a[::-1], b[::-1]
    if crop.shape[0] < 80:
        return 'Less than 80 pixels of usable edge length.'
    xs = a[0] + (np.arange(crop.shape[0])-a[1])*(b[0]-a[0])/(b[1]-a[1])
    if min(float(xs.min()), float(crop.shape[1]-1-xs.max())) < 30:
        return 'Less than 30 clean pixels on a side.'
    if float(np.mean((crop <= .0005) | (crop >= .999))) > .005:
        return 'Clipped pixels in the measurement crop.'
    smooth = cv2.GaussianBlur(crop, (9, 1), 1.5)
    left, right = np.median(smooth[:, :6], axis=1), np.median(smooth[:, -6:], axis=1)
    contrast = float(abs(np.median(right-left)))
    if contrast < .03:
        return 'Insufficient linear-light edge contrast.'
    # A second edge increases total variation even if the endpoint levels match.
    variation = np.abs(np.diff(smooth, axis=1)).sum(axis=1)
    if float(np.quantile(variation, .95)) > contrast * 1.25:
        return 'Neighbouring spoke, defect, or ringing contaminates the crop.'
    xx = np.arange(crop.shape[1])[None, :]
    mask = np.abs(xx-xs[:, None]) > 18
    expected = np.where(xx < xs[:, None], left[:, None], right[:, None])
    if float(np.quantile(np.abs(smooth-expected)[mask], .95)) > contrast*.10:
        return 'The black/white margins are not sufficiently flat.'
    if max(float(np.ptp(np.quantile(left, [.05,.95]))),
           float(np.ptp(np.quantile(right, [.05,.95])))) > contrast*.15:
        return 'Uneven edge plateaus or a second transition.'
    return None


def mapper_measure(executable, linear_crop, directory, expected_angle):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    source = directory / 'input.png'
    ok,encoded = cv2.imencode('.png',np.rint(np.clip(linear_crop, 0, 1)*65535).astype(np.uint16))
    if not ok:
        raise OSError('Could not write linear measurement crop')
    encoded.tofile(source)
    command = [str(executable), '--single-roi', '-q', '-f', '-e', '-v', '1', str(source), str(directory)]
    done = subprocess.run(command, capture_output=True, text=True, timeout=30, creationflags=CREATE_FLAGS)
    (directory/'mapper.log').write_text(done.stdout+done.stderr, encoding='utf-8')
    if done.returncode:
        raise ValueError('MTF Mapper failed')
    mtf_rows = [list(map(float, s.split())) for s in (directory/'edge_mtf_values.txt').read_text().splitlines() if s.strip()]
    sfr_rows = [list(map(float, s.split())) for s in (directory/'edge_sfr_values.txt').read_text().splitlines() if s.strip()]
    rows = [(m,s) for m,s in zip(mtf_rows,sfr_rows) if len(m)>=4 and len(s)==69 and m[1]>0 and m[2]>0]
    if len(rows) != 1:
        raise ValueError('MTF Mapper did not return exactly one edge')
    m,s = rows[0]
    if not np.isfinite(m+s).all() or not 0 < m[3] < .5:
        raise ValueError('MTF50 is invalid or reaches the sampling limit')
    # Version 1 writes 64 samples at 1/64 cycles/pixel; only retain <= Nyquist.
    curve = s[5:38]
    angle = abs(s[3]) % 90
    angle = min(angle, 90-angle)
    wanted = min(expected_angle % 90, 90-expected_angle % 90)
    if abs(angle-wanted) > .5:
        raise ValueError('Measured edge angle disagrees with the detected spoke')
    if max(curve) > 1.15 or max(curve[24:]) > .15:
        raise ValueError('Strong ringing/aliasing or non-isolated edge response')
    return dict(mtf50=m[3], frequencies=[i/64 for i in range(33)], sfr=curve,
                measured_slant=angle)


def measure_candidate(linear, candidate, directory, executable, clipped=None):
    variants = [(.03, .15, 30), (.04, .15, 30), (.03, .14, 30), (.03, .15, 32)]
    values = []
    for i,(start,stop,margin) in enumerate(variants):
        box = edge_box(candidate, start, stop, margin)
        reason = isolated_edge(linear, candidate, box)
        if reason:
            return dict(status='rejected', reason=reason, box=box)
        x0,y0,x1,y1 = box
        if clipped is not None and float(np.mean(clipped[y0:y1,x0:x1])) > .005:
            return dict(status='rejected',reason='A rendered RGB channel is clipped.',box=box)
        try:
            result = mapper_measure(executable, linear[y0:y1,x0:x1], Path(directory)/f'variant-{i}', candidate['angle'])
        except ValueError as exc:
            return dict(status='rejected', reason=str(exc), box=box)
        except (OSError, subprocess.SubprocessError):
            # Shared reports must not expose executable or job directory paths.
            return dict(status='rejected',reason='MTF Mapper could not process this crop; inspect local diagnostics.',box=box)
        values.append(result)
    spread = (max(v['mtf50'] for v in values)-min(v['mtf50'] for v in values))/np.median([v['mtf50'] for v in values])
    if spread > .10:
        return dict(status='rejected', reason='MTF50 changes by more than 10% with crop extent.', crop_spread=float(spread))
    return dict(status='accepted', **values[0], box=edge_box(candidate),
                crop_spread=float(spread), variant_mtf50=[v['mtf50'] for v in values])


def analyze_star(image, center, radius, directory, executable, reference_edges=None):
    linear = linear_luminance(image)
    clipped = np.any((image == 0) | (image == 255),axis=2)
    candidates = line_candidates(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), center, radius)
    results = []
    for direction in ('horizontal detail','vertical detail'):
        choices = [c for c in candidates if c['direction']==direction]
        reference = next((e for e in reference_edges or [] if e['direction']==direction), None)
        if reference_edges is not None:
            if reference is None or reference.get('status') != 'accepted':
                results.append(dict(direction=direction, status='rejected', reason='No accepted reference edge for this direction.'))
                continue
            # Preserve physical spoke identity; no per-capture sharpest-edge selection.
            choices = [c for c in choices if abs((c['radial_angle']-reference['radial_angle']+180)%360-180)<1]
            paired = []
            for candidate in choices:
                if abs((candidate['angle']-reference['angle']+90)%180-90) > .3:
                    continue
                a,b = np.array(candidate['line']).reshape(2,2)
                unit = (b-a)/np.linalg.norm(b-a)
                original = np.array(reference['line']).reshape(2,2)
                projected = a + ((original-a) @ unit)[:,None]*unit
                if np.max(np.linalg.norm(projected-original,axis=1)) > 8:
                    continue
                # Preserve radial endpoints across captures rather than letting
                # different blur change the line detector's chosen length.
                paired.append(dict(candidate,line=projected.ravel().tolist()))
            choices = paired
        failures = []
        for index,candidate in enumerate(choices[:12]):
            result = measure_candidate(linear, candidate, Path(directory)/f'{direction.split()[0]}-{index}', executable,clipped)
            if result['status']=='accepted':
                results.append(dict(**candidate, **result))
                break
            failures.append(result['reason'])
        else:
            results.append(dict(direction=direction,status='rejected',reason='No isolated, stable spoke edge.', details=sorted(set(failures))))
    return results


def analyze_run(run, locations, executable):
    """Read native original-pixel star crops; keep the same spoke on repeats."""
    run = Path(run)
    analysis_directory = run/('sfr-'+secrets.token_hex(4))
    version = subprocess.run([str(executable),'--version'],capture_output=True,text=True,
                             timeout=10,creationflags=CREATE_FLAGS)
    if version.returncode or '0.7.40' not in version.stdout+version.stderr:
        raise ValueError('This experimental adapter is validated only with MTF Mapper 0.7.40')
    rows = list(csv.DictReader((run/'report.csv').open(encoding='utf-8',newline='')))
    if not rows or len(rows)%len(locations):
        raise ValueError('Incomplete native star crop results')
    frames, references = [], {}
    for index,row in enumerate(rows):
        frame, region = divmod(index,len(locations))
        if region == 0:
            frames.append([])
            print(f'Star measurements: capture {frame+1}',flush=True)
        location = locations[region]
        name = f'frame-{frame+1:04}-roi-{region+1:02}.png'
        image = cv2.imdecode(np.fromfile(run/name,dtype=np.uint8),cv2.IMREAD_COLOR) if (run/name).is_file() else None
        if row['roi'] != location['id']:
            raise ValueError('Native star identity mismatch')
        source_box = [int(row[k]) for k in ('x','y','width','height')]
        center = [location['center'][0]-location['x'], location['center'][1]-location['y']]
        if image is None or row['status'] not in ('reference','tracked','fixed'):
            edges = [dict(direction=d,status='rejected',reason='Star crop missing, clipped, or could not be tracked.')
                     for d in ('horizontal detail','vertical detail')]
        else:
            edges = analyze_star(image,center,location['radius'],analysis_directory/f'edges-{frame}-{region}',
                                 executable,references.get(region))
        if frame == 0:
            references[region] = edges
        preview_name = None
        if image is not None:
            scale = min(1.,600/max(image.shape[:2]))
            preview = cv2.resize(image,(round(image.shape[1]*scale),round(image.shape[0]*scale)),interpolation=cv2.INTER_AREA)
            preview_name = Path(name).stem+'-preview.png'
            ok,encoded = cv2.imencode('.png',preview)
            if not ok: raise OSError('Could not encode star display preview')
            encoded.tofile(run/preview_name)
        frames[-1].append(dict(id=location['id'],source_box=source_box,
                              crop_name=preview_name,edges=edges))
    return dict(schema_version=1,status='experimental',mapper_version='0.7.40',
                mapper_sha256=hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
                input_processing='TTC LibRaw default gamma RGB8 -> inverse transfer -> linear luminance16',
                comparison_scope='Fixed-chart series with integer-translation tracking; no cross-capture rotation correction.',
                provenance=PROVENANCE,frames=frames)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--geometry',type=Path,required=True)
    parser.add_argument('--mapper',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = analyze_run(args.run,json.loads(args.geometry.read_text()),args.mapper)
    args.output.write_text(json.dumps(result,allow_nan=False),encoding='utf-8')
