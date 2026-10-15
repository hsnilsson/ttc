"""Analytic blur, contamination and original-pixel geometry checks.

Run with Python 3.11+ and build/python-deps. Optional TTC_MTF_MAPPER enables
real external-engine accuracy tests; those are skipped explicitly otherwise.
"""
from pathlib import Path
import math
import os
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'local'))
import star_mtf as mtf
np=mtf.np


def edge(sigma=2.,angle=5.):
    y,x=np.mgrid[:1400,:350]
    radians=math.radians(angle)
    line_x=100+(y-100)*math.tan(radians)
    distance=(x-line_x)*math.cos(radians)
    image=.1+.7*(.5+.5*np.vectorize(math.erf)(distance/(sigma*math.sqrt(2))))
    candidate=dict(line=[100.,100.,100+1200*math.tan(radians),1300.],angle=90-angle)
    return image,candidate


class GeometryChecks(unittest.TestCase):
    def test_registered_locations_and_bounds(self):
        locations=mtf.geometry([[12,0,0],[0,12,0],[0,0,1]],19200,12792)
        self.assertEqual(len(locations),9)
        self.assertEqual(locations[0]['center'],[5160,2736])
        for location in locations:
            self.assertGreaterEqual(location['x'],0)
            self.assertLessEqual(location['x']+location['width'],19200)
        with self.assertRaises(ValueError): mtf.geometry([[1,2]],100,100)

    def test_linearization(self):
        samples=np.array([[[0,0,0],[255,255,255],[128,128,128]]],np.uint8)
        output=mtf.linear_luminance(samples)
        self.assertAlmostEqual(output[0,0],0)
        self.assertAlmostEqual(output[0,1],1)
        self.assertTrue(.25<output[0,2]<.27)

    def test_clean_edge_and_contamination(self):
        image,candidate=edge()
        box=mtf.edge_box(candidate)
        self.assertIsNone(mtf.isolated_edge(image,candidate,box))
        y,x=np.mgrid[:1400,:350]
        line_x=100+(y-100)*math.tan(math.radians(5))
        contaminated=np.where(x>line_x+22,.1,image)
        self.assertIsNotNone(mtf.isolated_edge(contaminated,candidate,box))

    def test_clipping_flat_and_short(self):
        image,candidate=edge()
        box=mtf.edge_box(candidate)
        self.assertIsNotNone(mtf.isolated_edge(np.ones_like(image),candidate,box))
        self.assertIsNotNone(mtf.isolated_edge(np.full_like(image,.2),candidate,box))
        self.assertIsNotNone(mtf.isolated_edge(image,candidate,mtf.edge_box(candidate,.03,.06)))

    def test_low_noise_and_channel_clipping(self):
        image,candidate=edge()
        noisy=image+np.random.default_rng(42).normal(0,.001,image.shape)
        self.assertIsNone(mtf.isolated_edge(noisy,candidate,mtf.edge_box(candidate)))
        # Even when luminance is not clipped, a clipped RGB channel invalidates
        # the result before invoking an executable.
        result=mtf.measure_candidate(image,candidate,ROOT/'build'/'unused-mtf',Path('absent'),np.ones(image.shape,bool))
        self.assertEqual(result['reason'],'A rendered RGB channel is clipped.')

    def test_no_candidates_on_blank(self):
        self.assertEqual(mtf.line_candidates(np.zeros((500,500),np.uint8),(250,250),200),[])


@unittest.skipUnless(os.environ.get('TTC_MTF_MAPPER'),'Set TTC_MTF_MAPPER for external-engine validation')
class MapperChecks(unittest.TestCase):
    def test_known_gaussian_blur_and_crop_stability(self):
        mapper=Path(os.environ['TTC_MTF_MAPPER'])
        for sigma in (1.,2.,3.):
            for angle in (3.,5.,7.):
                with self.subTest(sigma=sigma,angle=angle), tempfile.TemporaryDirectory() as tmp:
                    image,candidate=edge(sigma,angle)
                    result=mtf.measure_candidate(image,candidate,Path(tmp),mapper)
                    self.assertEqual(result['status'],'accepted',result)
                    expected=math.sqrt(2*math.log(2))/(2*math.pi*sigma)
                    self.assertLess(abs(result['mtf50']/expected-1),.03)
                    self.assertLess(result['crop_spread'],.03)
                    expected_curve=np.exp(-2*math.pi**2*sigma**2*np.array(result['frequencies'])**2)
                    self.assertLess(float(np.max(np.abs(expected_curve-np.array(result['sfr'])))),.03)

    def test_missing_executable_is_not_a_measurement(self):
        image,candidate=edge()
        with tempfile.TemporaryDirectory() as tmp:
            result=mtf.measure_candidate(image,candidate,Path(tmp),Path(tmp)/'absent.exe')
            self.assertEqual(result['status'],'rejected')
            self.assertNotIn(tmp,result['reason'])


if __name__=='__main__': unittest.main()
