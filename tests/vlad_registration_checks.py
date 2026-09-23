"""Known-transform center errors and negative tests, not independent captures."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'local'), str(ROOT / 'build' / 'python-deps')]
import cv2
import numpy as np
import vlad_registration as detector


class RegistrationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with np.load(ROOT / 'local' / 'vlad-reference.npz') as data:
            cls.reference = data['gray']
        cls.h, cls.w = cls.reference.shape
        cls.centers = np.float32(detector.CENTERS) * (cls.w / 19136, cls.h / 12752)

    def run_image(self, image, dimensions=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'preview.png'
            cv2.imwrite(str(path), image)
            return detector.detect(path, *(dimensions or (image.shape[1], image.shape[0])))

    def check_transform(self, matrix, shape, name):
        warped = cv2.warpPerspective(self.reference, matrix, shape, borderValue=45)
        result = self.run_image(warped)
        self.assertEqual(result['status'], 'accepted', (name, result))
        predicted = cv2.perspectiveTransform(self.centers.astype(np.float32).reshape(-1, 1, 2), matrix).reshape(-1, 2)
        actual = np.float32([[r['center_x'], r['center_y']] for r in result['rois']])
        errors = np.linalg.norm(predicted - actual, axis=1)
        print(name, 'max center error', round(float(errors.max()), 3), 'preview pixels', flush=True)
        self.assertLess(float(errors.max()), 2.0, (name, errors))
        self.assertEqual([r['id'] for r in result['rois']], list(detector.IDS))

    def test_rotation_scale_padding(self):
        for angle, scale in ((0, .5), (13, .8), (37, .7), (90, 1), (180, .75), (270, .8), (-67, 1.15)):
            with self.subTest(angle=angle, scale=scale):
                theta = np.deg2rad(angle)
                width = int(scale * (abs(np.cos(theta)) * self.w + abs(np.sin(theta)) * self.h)) + 160
                height = int(scale * (abs(np.sin(theta)) * self.w + abs(np.cos(theta)) * self.h)) + 160
                affine = cv2.getRotationMatrix2D((self.w / 2, self.h / 2), angle, scale)
                affine[:, 2] += (width / 2 - self.w / 2, height / 2 - self.h / 2)
                self.check_transform(np.vstack([affine, (0, 0, 1)]), (width, height), f'angle={angle},scale={scale}')

    def test_perspective(self):
        source = np.float32(((0, 0), (self.w - 1, 0), (self.w - 1, self.h - 1), (0, self.h - 1)))
        target = np.float32(((180, 110), (1680, 30), (1560, 1160), (70, 1000)))
        self.check_transform(cv2.getPerspectiveTransform(source, target), (1780, 1240), 'perspective')

    def test_missing_measurement_regions(self):
        for rid, (cx, cy), size in zip(detector.IDS, self.centers, detector.SIZES):
            with self.subTest(region=rid):
                image = self.reference.copy()
                half = round(size * self.w / 19136 / 2) + 5
                image[round(cy) - half:round(cy) + half, round(cx) - half:round(cx) + half] = 60
                self.assertEqual(self.run_image(image)['status'], 'manual-required', rid)

    def test_negative_and_ambiguous(self):
        rng = np.random.default_rng(720)
        yy, xx = np.indices(self.reference.shape)
        for name, image in (
            ('blank', np.full_like(self.reference, 100)),
            ('noise', rng.integers(0, 256, self.reference.shape, dtype=np.uint8)),
            ('bars', np.uint8((xx // 12 % 2) * 200)),
            ('checkerboard', np.uint8(((xx // 15 + yy // 15) % 2) * 200)),
            ('mirrored', cv2.flip(self.reference, 1)),
            ('two identical charts', np.hstack([self.reference, self.reference])),
        ):
            with self.subTest(case=name):
                self.assertEqual(self.run_image(image)['status'], 'manual-required', name)

    def test_clipped_and_wrong_dimensions(self):
        self.assertEqual(self.run_image(self.reference[200:, 200:])['status'], 'manual-required')
        self.assertEqual(self.run_image(self.reference, (1000, 1000))['status'], 'manual-required')


if __name__ == '__main__':
    unittest.main()
