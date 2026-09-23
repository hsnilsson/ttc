"""Locate the five user-calibrated Vlad measurement centers in original pixels.

Only detection uses a rectified preview. Analysis and exported crops still use
the original decoded pixels. Missing dependencies or uncertain evidence require
manual selection, never a coordinate-only fallback.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
DEPS = HERE.parent / 'build' / 'python-deps'
if DEPS.is_dir():
    sys.path.insert(0, str(DEPS))

IDS = ('center', 'tl', 'tr', 'bl', 'br')
FULL_SIZE = (19136, 12752)
# Approximate user annotations registered from the 2026-09-23 screenshot.
CENTERS = ((9588, 5227), (2457, 2029), (17113, 2433),
           (2054, 10364), (16711, 10803))
SIZES = (650, 880, 880, 880, 880)


def rejected(reason, **evidence):
    return dict(status='manual-required', confidence=0, rois=[], candidates=[],
                warnings=[reason, 'Define or correct the five regions manually.'],
                label_convention='upright-chart', **evidence)


def detect(preview, width, height):
    if type(width) is not int or type(height) is not int or not (8 <= width <= 100000 and 8 <= height <= 100000):
        return rejected('Invalid full-resolution dimensions.')
    try:
        import cv2
        import numpy as np
    except ImportError:
        return rejected('OpenCV/NumPy detector dependencies are unavailable; rebuild the portable package.')
    cv2.setNumThreads(1)
    cv2.setRNGSeed(0)
    try:
        image = cv2.imdecode(np.fromfile(str(preview), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        with np.load(HERE / 'vlad-reference.npz', allow_pickle=False) as stored:
            reference = stored['gray']
            points = stored['points'].astype(np.float32)
            descriptors = stored['descriptors'].astype(np.float32)
    except (OSError, ValueError, KeyError, cv2.error):
        return rejected('Preview or bundled reference is unreadable.')
    if image is None or image.size > 16000000 or min(image.shape) < 100:
        return rejected('Preview is unreadable, too small, or exceeds the detection size limit.')
    ih, iw = image.shape
    if abs((iw / ih) / (width / height) - 1) > .01:
        return rejected('Preview aspect ratio differs from the oriented source image.')
    # Bound feature work independent of input preview resolution.
    factor = min(1., 1800 / max(iw, ih))
    if factor < 1:
        image = cv2.resize(image, (round(iw * factor), round(ih * factor)), interpolation=cv2.INTER_AREA)
    ih, iw = image.shape
    rh, rw = reference.shape
    sift = cv2.SIFT_create(nfeatures=0, contrastThreshold=.025, edgeThreshold=12)
    keypoints, observed = sift.detectAndCompute(image, None)
    if observed is None or len(observed) < 32:
        return rejected('Insufficient distinctive target features.')
    # A response-ranked feature cap selects almost exclusively repeated dots.
    # Keep larger landmarks; allow smaller ones than in the reference so a
    # half-size chart remains recognizable. Bound descriptor matching work.
    indices = sorted((i for i, k in enumerate(keypoints) if k.size >= 3),
                     key=lambda i: keypoints[i].size, reverse=True)[:12000]
    if len(indices) < 32:
        return rejected('Insufficient distinctive target landmarks.')
    observed = observed[indices]
    keypoints = [keypoints[i] for i in indices]
    matcher = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=80))
    pairs = matcher.knnMatch(descriptors, observed, k=2)
    # Unique destination features stop repeated reference patterns from voting
    # many times for the same point in an unrelated panel.
    unique = {}
    for pair in pairs:
        if len(pair) != 2 or pair[0].distance >= .72 * pair[1].distance:
            continue
        match = pair[0]
        if match.trainIdx not in unique or match.distance < unique[match.trainIdx].distance:
            unique[match.trainIdx] = match
    matches = list(unique.values())
    if len(matches) < 24:
        return rejected('Too few distinctive chart correspondences.', matches=len(matches))
    source = np.float32([points[m.queryIdx] for m in matches])
    target = np.float32([keypoints[m.trainIdx].pt for m in matches])
    matrix, mask = cv2.findHomography(source, target, cv2.USAC_MAGSAC, 2.5, maxIters=20000, confidence=.999)
    if matrix is None or mask is None or not np.isfinite(matrix).all():
        return rejected('No consistent chart geometry.', matches=len(matches))
    keep = mask.ravel().astype(bool)
    count = int(keep.sum())
    ratio = count / len(matches)
    evidence = dict(matches=len(matches), inliers=count, inlier_ratio=round(ratio, 4))
    # Inlier fraction alone is misleading on this highly repetitive chart:
    # genuine captures can have hundreds of distractor bar/dot matches. Judge
    # the spatial fit and independently verified five patches instead.
    if count < 24:
        return rejected('Too few consistent chart correspondences.', **evidence)
    locations = source[keep]
    coverage = cv2.contourArea(cv2.convexHull(locations)) / (rw * rh)
    evidence['reference_coverage'] = round(coverage, 4)
    quadrant_counts = [int(np.sum(((locations[:, 0] < rw / 2) == left) &
                                  ((locations[:, 1] < rh / 2) == top)))
                       for left, top in ((True, True), (False, True), (True, False), (False, False))]
    # Require a genuinely two-dimensional, four-quadrant fit; acceptance still
    # additionally requires local image evidence at ALL five outer/inner ROIs.
    span = np.ptp(locations, axis=0)
    evidence['quadrant_inliers'] = quadrant_counts
    evidence['inlier_span'] = [round(float(span[0] / rw), 4), round(float(span[1] / rh), 4)]
    if coverage < .25 or min(quadrant_counts) < 3 or span[0] < .5 * rw or span[1] < .5 * rh:
        return rejected('Matches do not cover the whole target; a repeated panel is not sufficient.', **evidence)

    def project(values):
        return cv2.perspectiveTransform(np.float32(values).reshape(-1, 1, 2), matrix).reshape(-1, 2)

    corners = project(((0, 0), (rw - 1, 0), (rw - 1, rh - 1), (0, rh - 1)))
    area = cv2.contourArea(corners, oriented=True)
    if not np.isfinite(corners).all() or not cv2.isContourConvex(corners) or not (.025 * iw * ih < area < 4 * iw * ih):
        return rejected('Mirrored, degenerate, or unsupported chart geometry.', **evidence)
    # A second chart must not silently win/lose according to descriptor noise.
    outside = [i for i, keypoint in enumerate(keypoints)
               if cv2.pointPolygonTest(corners, keypoint.pt, False) < 0]
    if len(outside) >= 24:
        alternatives = matcher.knnMatch(descriptors, observed[outside], k=2)
        other = {}
        for pair in alternatives:
            if len(pair) == 2 and pair[0].distance < .72 * pair[1].distance:
                match = pair[0]
                if match.trainIdx not in other or match.distance < other[match.trainIdx].distance:
                    other[match.trainIdx] = match
        if len(other) >= 24:
            a = np.float32([points[m.queryIdx] for m in other.values()])
            b = np.float32([keypoints[outside[m.trainIdx]].pt for m in other.values()])
            _, second_mask = cv2.findHomography(a, b, cv2.USAC_MAGSAC, 2.5, maxIters=10000, confidence=.999)
            if second_mask is not None and int(second_mask.sum()) >= 24:
                second_points = a[second_mask.ravel().astype(bool)]
                if cv2.contourArea(cv2.convexHull(second_points)) / (rw * rh) > .4:
                    return rejected('More than one plausible chart; choose the intended chart manually.', **evidence)
    residual = np.linalg.norm(project(source[keep]) - target[keep], axis=1)
    evidence['median_reprojection_error'] = round(float(np.median(residual)), 4)
    if np.percentile(residual, 90) > 2.5:
        return rejected('Chart registration is too imprecise.', **evidence)
    # No poles may cross the target plane.
    denominators = [matrix[2] @ np.array([x, y, 1.]) for x, y in ((0, 0), (rw, 0), (rw, rh), (0, rh))]
    if min(denominators) * max(denominators) <= 0:
        return rejected('Invalid perspective mapping.', **evidence)
    try:
        inverse = np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        return rejected('Singular chart mapping.', **evidence)
    rectified = cv2.warpPerspective(image, inverse, (rw, rh), flags=cv2.INTER_LINEAR)
    ref_smooth = cv2.GaussianBlur(reference, (3, 3), .6)
    rect_smooth = cv2.GaussianBlur(rectified, (3, 3), .6)
    regions = []
    scales = []
    for rid, (cx, cy), size in zip(IDS, CENTERS, SIZES):
        center = np.array([cx * rw / FULL_SIZE[0], cy * rh / FULL_SIZE[1]])
        half = np.array([size * rw / FULL_SIZE[0], size * rh / FULL_SIZE[1]]) / 2
        pattern_size = tuple(max(16, round(x * 2)) for x in half)
        radius = 4
        pattern = cv2.getRectSubPix(ref_smooth, pattern_size, tuple(center))
        search = cv2.getRectSubPix(rect_smooth, (pattern_size[0] + 2 * radius, pattern_size[1] + 2 * radius), tuple(center))
        if float(pattern.std()) < 4 or float(search.std()) < 4:
            return rejected(f'{rid}: insufficient local target contrast.', **evidence)
        scores = cv2.matchTemplate(search, pattern, cv2.TM_CCOEFF_NORMED)
        _, score, _, (bx, by) = cv2.minMaxLoc(scores)
        if not math.isfinite(score) or score < .72:
            return rejected(f'{rid}: the measuring square is missing, obscured, or does not match.', **evidence)
        if bx in (0, 2 * radius) or by in (0, 2 * radius):
            return rejected(f'{rid}: local target position is inconsistent with chart geometry.', **evidence)
        # Refine detection only. The measurement image is never resampled.
        def peak_shift(a, b, c):
            denominator = a - 2 * b + c
            return float(np.clip(.5 * (a - c) / denominator, -.5, .5)) if denominator < -1e-6 else 0.
        dx = bx - radius + peak_shift(scores[by, bx - 1], scores[by, bx], scores[by, bx + 1])
        dy = by - radius + peak_shift(scores[by - 1, bx], scores[by, bx], scores[by + 1, bx])
        refined = center + (dx, dy)
        point = project([refined])[0]
        quad = project([refined + half * signs for signs in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        # A visible center alone is insufficient: the complete measurement
        # square must be present, including rotated corners.
        if (quad < 1).any() or (quad[:, 0] >= iw - 1).any() or (quad[:, 1] >= ih - 1).any():
            return rejected(f'{rid}: measuring square is clipped.', **evidence)
        local = project([refined, refined + (1, 0), refined + (0, 1)])
        jacobian = np.column_stack((local[1] - local[0], local[2] - local[0]))
        singular = np.linalg.svd(jacobian, compute_uv=False)
        if singular[-1] <= .1 or singular[0] / singular[-1] > 3:
            return rejected(f'{rid}: unsupported local perspective or resolution.', **evidence)
        scales.append(float(np.sqrt(np.linalg.det(jacobian))))
        source_scale = np.array([width / iw, height / ih])
        point = point * source_scale
        quad = quad * source_scale
        extent = np.ceil(np.max(np.abs(quad - point), axis=0) * 2).astype(int)
        origin = np.rint(point - extent / 2).astype(int)
        if min(extent) < 8 or min(origin) < 0 or (origin + extent > (width, height)).any():
            return rejected(f'{rid}: centered crop would leave the source image.', **evidence)
        regions.append(dict(id=rid, x=int(origin[0]), y=int(origin[1]), width=int(extent[0]), height=int(extent[1]),
                            center_x=round(float(point[0]), 3), center_y=round(float(point[1]), 3),
                            confidence=round(float(score), 5), status='accepted'))
    if max(scales) / min(scales) > 3:
        return rejected('Perspective changes scale too strongly across the target.', **evidence)
    angle = math.degrees(math.atan2(corners[1, 1] - corners[0, 1], corners[1, 0] - corners[0, 0]))
    return dict(status='accepted', confidence=min(r['confidence'] for r in regions), rois=regions,
                candidates=regions, orientation_degrees=round(angle, 2), label_convention='upright-chart',
                warnings=['Centers follow the user-calibrated reference; inspect all five squares. '
                          'Corner names refer to the upright chart, not the screen. '
                          'Confidence is local image correlation, not a probability.'], **evidence)


if __name__ == '__main__':
    try:
        if len(sys.argv) != 4:
            raise ValueError('Usage: vlad_registration.py PREVIEW WIDTH HEIGHT')
        result = detect(Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    except (ValueError, OSError) as error:
        result = rejected(str(error))
    print(json.dumps(result, allow_nan=False))
