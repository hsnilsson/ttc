"""Validate the independent 10–90% edge-width diagnostic against known blur."""
from pathlib import Path
import importlib.util,math,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit',ROOT/'scripts/audit-corner-mtf.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
np=a.np
class EdgeWidthChecks(unittest.TestCase):
    def test_flat_patch_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'contrast'):
            a.edge_width(np.ones((100,100))*.5,dict(line=[10,50,90,50]),(10,18,90,82))

    def test_known_blur_both_directions_and_polarities(self):
        y,x=np.mgrid[:500,:500]
        for angle in (5,95):
            rad=math.radians(angle);u=np.array([math.cos(rad),math.sin(rad)])
            n=np.array([-u[1],u[0]]);p=np.array([250,250])-180*u;q=p+360*u
            edge=dict(line=[*p,*q])
            distance=(x-p[0])*n[0]+(y-p[1])*n[1]
            for sigma in (1,2,3,5):
                image=.1+.7*(.5+.5*np.vectorize(math.erf)(distance/(sigma*math.sqrt(2))))
                box=a.m.edge_box(edge,.1,.8,32)
                for sign in (1,-1):
                    with self.subTest(angle=angle,sigma=sigma,sign=sign):
                        width=a.edge_width(sign*image,edge,box)['width']
                        self.assertLess(abs(width/(2.563103131*sigma)-1),.03)
if __name__=='__main__':unittest.main()
