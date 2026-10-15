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
from unittest.mock import patch
import json
import csv

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
        self.assertEqual(len(locations[-1]['search_stars']),5)
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


class SeriesChecks(unittest.TestCase):
    def test_radial_center_is_found_from_image_not_seed(self):
        y,x=np.mgrid[:700,:700]
        center=np.array([350.,345.])
        theta=np.arctan2(y-center[1],x-center[0])
        image=np.where(np.sin(theta*32)>0,220,30).astype(np.uint8)
        image[np.hypot(x-center[0],y-center[1])>280]=120
        fitted=mtf.refine_center(image,center+[24,-19],280)
        np.testing.assert_allclose(fitted,center,atol=2)

    def test_context_translation_and_unrelated_crop(self):
        rng=np.random.default_rng(29)
        image=np.full((700,700,3),120,np.uint8)
        for _ in range(100):
            point=tuple(int(v) for v in rng.integers(25,675,2))
            mtf.cv2.circle(image,point,int(rng.integers(3,15)),tuple(int(v) for v in rng.integers(10,245,3)),-1)
        translated=mtf.cv2.warpAffine(image,np.float32([[1,0,6],[0,1,-4]]),(700,700))
        result=mtf.register_crop(image,translated)
        self.assertEqual(result['status'],'accepted',result)
        np.testing.assert_allclose(result['shift'],[6,-4],atol=.3)
        self.assertEqual(mtf.register_crop(image,np.zeros_like(image))['status'],'rejected')
        rotated=mtf.cv2.warpAffine(image,mtf.cv2.getRotationMatrix2D((350,350),1,1),(700,700))
        self.assertEqual(mtf.register_crop(image,rotated)['status'],'rejected')

    def test_reference_can_come_from_later_capture(self):
        directions=('horizontal detail','vertical detail')
        def analyze(image,center,radius,directory,executable,reference_edges=None,search_stars=None):
            if reference_edges is None and image[0,0,0]==10:
                return [dict(direction=d,status='rejected') for d in directions]
            if reference_edges is None:
                return [dict(direction=d,status='accepted',line=[10.,10.,20.,110.],mtf50=.1) for d in directions]
            self.assertEqual(len(reference_edges),2)
            return [dict(e) for e in reference_edges]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);exe=root/'mapper';exe.write_bytes(b'test')
            with (root/'report.csv').open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=['roi','x','y','width','height','status']);writer.writeheader()
                for frame,value in enumerate([10,20],1):
                    writer.writerow(dict(roi='test',x=0,y=0,width=120,height=120,status='fixed'))
                    ok,png=mtf.cv2.imencode('.png',np.full((120,120,3),value,np.uint8));png.tofile(root/f'frame-{frame:04}-roi-01.png')
            with patch.object(mtf.subprocess,'run',return_value=type('Result',(),dict(returncode=0,stdout='0.7.40',stderr=''))()), \
                 patch.object(mtf,'register_crop',return_value=dict(status='accepted',shift=[0,0])), \
                 patch.object(mtf,'analyze_star',side_effect=analyze):
                result=mtf.analyze_run(root,[dict(id='test',center=[60,60],radius=50)],exe)
            for frame in result['frames']:
                self.assertTrue(all(e['reference_capture']==2 for e in frame[0]['edges']))
                self.assertTrue(all(e['status']=='accepted' for e in frame[0]['edges']))

    def test_bad_first_context_does_not_poison_later_captures(self):
        images=[np.full((5,5,3),v,np.uint8) for v in [0,1,2]]
        def register(a,b,*features):
            if a[0,0,0]==0 or b[0,0,0]==0: return dict(status='rejected',reason='No landmarks')
            return dict(status='accepted',shift=[0,0])
        with patch.object(mtf,'register_crop',side_effect=register):
            anchor,results=mtf.register_series(images)
        self.assertEqual(anchor,1)
        self.assertEqual([r['status'] for r in results],['rejected','accepted','accepted'])

    def test_shift_preserves_original_reference(self):
        original=[dict(status='accepted',line=[1,2,3,4])]
        shifted=mtf.shifted_edges(original,np.array([5,-2]))
        self.assertEqual(shifted[0]['line'],[6,0,8,2])
        self.assertEqual(original[0]['line'],[1,2,3,4])


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

    def test_medium_star_edge_uses_sufficient_outer_span(self):
        image,candidate=edge()
        candidate['line'][2:]=[100+500*math.tan(math.radians(5)),600.]
        with tempfile.TemporaryDirectory() as tmp:
            result=mtf.measure_candidate(image,candidate,Path(tmp),Path(os.environ['TTC_MTF_MAPPER']))
            self.assertEqual(result['status'],'accepted',result)
            expected=math.sqrt(2*math.log(2))/(4*math.pi)
            self.assertLess(abs(result['mtf50']/expected-1),.03)

    def test_missing_executable_is_not_a_measurement(self):
        image,candidate=edge()
        with tempfile.TemporaryDirectory() as tmp:
            result=mtf.measure_candidate(image,candidate,Path(tmp),Path(tmp)/'absent.exe')
            self.assertEqual(result['status'],'rejected')
            self.assertNotIn(tmp,result['reason'])


if __name__=='__main__': unittest.main()
