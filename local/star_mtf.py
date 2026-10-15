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
         ('center_small',800,535,65)]


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
        search_stars = []
        if name == 'center_small':
            for sx,sy,sr in ((753,487,12),(847,487,12),(753,582,12),(847,582,12),(800,535,40)):
                point = matrix @ np.array([sx,sy,1.])
                search_stars.append(dict(center=(point[:2]/point[2]).tolist(),radius=radius*sr/r))
        result.append(dict(search_stars=search_stars,id=name,x=int(low[0]),y=int(low[1]),width=int(high[0]-low[0]),
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


def refine_center(gray, center, radius):
    """Fit the intersection of long spoke boundaries near the registered seed."""
    lines = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(gray)[0]
    if lines is None: return np.asarray(center,dtype=float)
    normals, constants = [], []
    center = np.asarray(center,dtype=float)
    for line in lines.reshape(-1,4):
        a,b = line.reshape(2,2).astype(float)
        length = np.linalg.norm(b-a)
        if length<max(60,.35*radius): continue
        normal = np.array([a[1]-b[1],b[0]-a[0]])/length
        if abs((center-a)@normal)>.15*radius: continue
        if min(np.linalg.norm(a-center),np.linalg.norm(b-center))>.6*radius: continue
        normals.append(normal); constants.append(normal@a)
    if len(normals)<12: return center
    normals,constants = np.array(normals),np.array(constants)
    estimate = center.copy()
    for _ in range(8):
        residual = np.abs(normals@estimate-constants)
        weights = 1/np.maximum(residual,2.)
        estimate = np.linalg.lstsq(normals*weights[:,None],constants*weights,rcond=None)[0]
    keep = np.abs(normals@estimate-constants)<4
    if keep.sum()<12 or np.linalg.cond(normals[keep])>5 or np.linalg.norm(estimate-center)>.15*radius:
        return center
    return np.linalg.lstsq(normals[keep],constants[keep],rcond=None)[0]


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
    length = float(np.linalg.norm(np.array(candidate['line'][2:])-candidate['line'][:2]))
    stop = min(.45,max(.15,.03+100/max(length,1)))
    variants = [(.03, stop, 30), (.04, stop, 30), (.03, stop-.01, 30), (.03, stop, 32)]
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
    return dict(status='accepted', **values[0], box=edge_box(candidate,.03,stop),
                crop_spread=float(spread), variant_mtf50=[v['mtf50'] for v in values])


def analyze_star(image, center, radius, directory, executable, reference_edges=None, search_stars=None):
    linear = linear_luminance(image)
    clipped = np.any((image == 0) | (image == 255),axis=2)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    candidates = []
    for feature,star in enumerate(search_stars or [dict(center=center,radius=radius)]):
        fitted = refine_center(gray,star['center'],star['radius'])
        candidates.extend(dict(c,feature_id=feature) for c in line_candidates(gray,fitted,star['radius']))
    candidates.sort(key=lambda c:(abs(c['slant']-5),c['feature_id'],c['radial_angle']))
    results = []
    for direction in ('horizontal detail','vertical detail'):
        choices = [c for c in candidates if c['direction']==direction]
        reference = next((e for e in reference_edges or [] if e['direction']==direction), None)
        if reference_edges is not None:
            if reference is None or reference.get('status') != 'accepted':
                results.append(dict(direction=direction, status='rejected', reason='No accepted reference edge for this direction.'))
                continue
            # Preserve physical spoke identity; no per-capture sharpest-edge selection.
            choices = [c for c in choices if c.get('feature_id',0)==reference.get('feature_id',0) and abs((c['radial_angle']-reference['radial_angle']+180)%360-180)<1]
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
        accepted = []
        for index,candidate in enumerate(choices[:12]):
            if any(candidate.get('feature_id',0)==e.get('feature_id',0) and abs((candidate['radial_angle']-e['radial_angle']+180)%360-180)<1 for e in accepted):
                continue
            result = measure_candidate(linear, candidate, Path(directory)/f'{direction.split()[0]}-{index}', executable,clipped)
            if result['status']=='accepted':
                accepted.append(dict(**candidate, **result))
                if reference_edges is not None or len(accepted)>=3:
                    break
            else:
                failures.append(result['reason'])
        if accepted:
            primary = accepted[0]
            primary['supporting_edges'] = accepted[1:]
            if reference is not None:
                # Supporting spokes remain fixed too. They diagnose spatial
                # disagreement; their values never replace or boost the primary.
                for index,support in enumerate(reference.get('supporting_edges',[])):
                    candidate = dict(support)
                    result = measure_candidate(linear,candidate,Path(directory)/f'{direction.split()[0]}-support-{index}',executable,clipped)
                    candidate.update(result)
                    primary['supporting_edges'].append(candidate)
            results.append(primary)
        else:
            results.append(dict(direction=direction,status='rejected',reason='No isolated, stable spoke edge.', candidates_tested=min(12,len(choices)), details=sorted(set(failures))))
    return results


def context_features(image):
    cv2.setNumThreads(1)
    scale = min(1.,1200/max(image.shape[:2]))
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
    keys,descriptors = cv2.SIFT_create(contrastThreshold=.025).detectAndCompute(gray,None)
    return gray,keys,descriptors,scale


def register_crop(reference, image, reference_features=None, image_features=None):
    """Verify translation from distinctive features in the whole context crop.

    Resizing is detection-only. Returned translations are applied to edge
    coordinates; measurement pixels are never warped or resampled.
    """
    a,ka,da,scale = reference_features or context_features(reference)
    b,kb,db,other_scale = image_features or context_features(image)
    if a.shape!=b.shape or scale!=other_scale:
        return dict(status='rejected',reason='Context crop dimensions differ.')
    failure = dict(status='rejected', reason='Context landmarks do not establish a reliable translation.')
    if da is None or db is None or len(da)<12 or len(db)<12:
        return failure
    matches = cv2.BFMatcher().knnMatch(da, db, k=2)
    unique = {}
    for pair in matches:
        if len(pair)==2 and pair[0].distance < .7*pair[1].distance:
            m = pair[0]
            if m.trainIdx not in unique or m.distance<unique[m.trainIdx].distance:
                unique[m.trainIdx] = m
    if len(unique)<12:
        return failure
    source = np.float32([ka[m.queryIdx].pt for m in unique.values()])
    target = np.float32([kb[m.trainIdx].pt for m in unique.values()])
    cv2.setRNGSeed(0)
    matrix, mask = cv2.estimateAffinePartial2D(source,target,method=cv2.RANSAC,
                                             ransacReprojThreshold=.8,maxIters=5000,confidence=.999)
    if matrix is None or mask is None:
        return failure
    keep = mask.ravel().astype(bool)
    offsets = (target-source)[keep]/scale
    if len(offsets)<12 or keep.mean()<.5:
        return failure
    shift = np.median(offsets,axis=0)
    residual = np.linalg.norm(offsets-shift,axis=1)
    coverage = cv2.contourArea(cv2.convexHull(source[keep]))/(a.shape[0]*a.shape[1])
    rotation = math.degrees(math.atan2(matrix[1,0],matrix[0,0]))
    magnification = math.hypot(matrix[0,0],matrix[1,0])
    if (coverage<.12 or np.quantile(residual,.9)>1.5 or
        abs(rotation)>.08 or abs(magnification-1)>.001 or np.max(np.abs(shift))>32):
        return dict(status='rejected',reason='Context geometry exceeds the validated translation-only comparison limits.')
    return dict(status='accepted',shift=shift.tolist(),inliers=len(offsets),
                coverage=float(coverage),residual_p90=float(np.quantile(residual,.9)))


def register_series(images):
    """Select the context anchor covering most captures; retry incomplete anchors.

    Selection uses geometric coverage only, never measured sharpness. A damaged
    first capture must not prevent two later usable captures being compared.
    """
    best_anchor = None
    best = [dict(status='rejected',reason='No mutually verifiable chart context in this series.') for _ in images]
    best_count = 0
    available = sum(image is not None for image in images)
    features = [context_features(image) if image is not None else None for image in images]
    for anchor,reference in enumerate(images):
        if reference is None: continue
        own = register_crop(reference,reference,features[anchor],features[anchor])
        if own['status']!='accepted': continue
        registered = []
        for index,image in enumerate(images):
            if image is None:
                result = dict(status='rejected',reason='Original-pixel context crop unavailable.')
            elif index==anchor:
                result = dict(own,shift=[0.,0.],anchor=True)
            else:
                result = register_crop(reference,image,features[anchor],features[index])
            registered.append(result)
        count = sum(r['status']=='accepted' for r in registered)
        if count>best_count:
            best_anchor,best,best_count = anchor,registered,count
        if count==available:
            break
    return best_anchor,best


def shifted_edges(edges, shift):
    result = []
    for edge in edges:
        copied = dict(edge)
        if edge.get('status')=='accepted':
            copied['line'] = (np.array(edge['line']).reshape(2,2)+shift).ravel().tolist()
            if edge.get('supporting_edges'):
                copied['supporting_edges'] = shifted_edges(edge['supporting_edges'],shift)
        result.append(copied)
    return result


def analyze_run(run, locations, executable):
    """Select each physical reference from the series, then measure it consistently."""
    run = Path(run)
    analysis_directory = run/('sfr-'+secrets.token_hex(4))
    version = subprocess.run([str(executable),'--version'],capture_output=True,text=True,
                             timeout=10,creationflags=CREATE_FLAGS)
    if version.returncode or '0.7.40' not in version.stdout+version.stderr:
        raise ValueError('This experimental adapter is validated only with MTF Mapper 0.7.40')
    with (run/'report.csv').open(encoding='utf-8',newline='') as stream:
        rows = list(csv.DictReader(stream))
    if not rows or len(rows)%len(locations):
        raise ValueError('Incomplete native star crop results')
    count = len(rows)//len(locations)
    frames = [[] for _ in range(count)]
    for region,location in enumerate(locations):
        print(f'Star measurements: location {region+1}/{len(locations)}',flush=True)
        images, records, registrations = [], [], []
        for frame in range(count):
            row = rows[frame*len(locations)+region]
            if row['roi'] != location['id']:
                raise ValueError('Native star identity mismatch')
            name = f'frame-{frame+1:04}-roi-{region+1:02}.png'
            image = cv2.imdecode(np.fromfile(run/name,dtype=np.uint8),cv2.IMREAD_COLOR) if (run/name).is_file() else None
            if row.get('status') not in ('reference','fixed','tracked'):
                image = None
            if image is not None and image.shape[:2] != (int(row['height']),int(row['width'])):
                image = None
            images.append(image)
            preview_name = None
            if image is not None:
                scale = min(1.,600/max(image.shape[:2]))
                preview = cv2.resize(image,(round(image.shape[1]*scale),round(image.shape[0]*scale)),interpolation=cv2.INTER_AREA)
                preview_name = Path(name).stem+'-preview.png'
                ok,encoded = cv2.imencode('.png',preview)
                if not ok: raise OSError('Could not encode star display preview')
                encoded.tofile(run/preview_name)
            records.append(dict(id=location['id'],source_box=[int(row[k]) for k in ('x','y','width','height')],crop_name=preview_name))
        anchor,registrations = register_series(images)
        # References are selected in capture order by validity, never max MTF50.
        # A later usable capture can establish a direction missing in capture 1.
        references = {}
        discovery = {}
        def search_stars(shift):
            return [dict(center=(np.array(star['center'])-np.array(records[anchor or 0]['source_box'][:2])+shift).tolist(),radius=star['radius']) for star in location.get('search_stars',[])] or None
        base_center = np.array(location['center'])-np.array(records[anchor or 0]['source_box'][:2])
        for frame,(image,registration) in enumerate(zip(images,registrations)):
            if len(references)==2: break
            if registration['status']!='accepted': continue
            shift = np.array(registration['shift'])
            measured = analyze_star(image,base_center+shift,location['radius'],
                                    analysis_directory/f'discover-{region}-{frame}',executable,search_stars=search_stars(shift))
            for edge in measured:
                audit = discovery.setdefault(edge['direction'],dict(candidates_tested=0,details=set()))
                audit['candidates_tested'] += edge.get('candidates_tested',0)
                audit['details'].update(edge.get('details',[]))
                if edge['status']=='accepted' and edge['direction'] not in references:
                    normalized = shifted_edges([edge],-shift)[0]
                    normalized['reference_capture'] = frame+1
                    references[edge['direction']] = normalized
        for frame,(image,registration) in enumerate(zip(images,registrations)):
            if registration['status']!='accepted':
                edges = [dict(direction=d,status='rejected',reason=registration['reason'])
                         for d in ('horizontal detail','vertical detail')]
            else:
                shift = np.array(registration['shift'])
                edges = analyze_star(image,base_center+shift,location['radius'],
                                     analysis_directory/f'measure-{region}-{frame}',executable,
                                     shifted_edges(list(references.values()),shift),search_stars=search_stars(shift))
                for edge in edges:
                    ref = references.get(edge['direction'])
                    if ref:
                        edge['reference_capture'] = ref['reference_capture']
                    else:
                        edge['reason'] = 'No isolated edge passed validation anywhere in this series.'
                        audit = discovery.get(edge['direction'],{})
                        edge['candidates_tested'] = audit.get('candidates_tested',0)
                        edge['details'] = sorted(audit.get('details',[]))
                        if location['id']=='center_small':
                            edge['reason'] += ' The four small central stars and the central pinwheel were searched; none supplied a valid near-axis slanted edge with sufficient clean margins.'
            records[frame].update(edges=edges,tracking=registration)
            frames[frame].append(records[frame])
    return dict(schema_version=2,status='experimental',mapper_version='0.7.40',
                method_settings=dict(slant_degrees=[3,7],minimum_edge_pixels=80,minimum_margin_pixels=30,
                    maximum_crop_spread=.10,reference_selection='First valid physical edge in capture order; never highest MTF50',
                    supporting_spokes='Up to two additional fixed spokes; no substitution or averaging'),
                mapper_sha256=hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
                input_processing='TTC LibRaw default gamma RGB8 -> inverse transfer -> linear luminance16',
                comparison_scope='Context-landmark verified translation; series-wide reference search; original measurement pixels.',
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
