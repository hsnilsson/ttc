"""Service and selection regression checks; run with Python 3.10+."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest import mock
import urllib.error
import urllib.request
import struct
import sys
import zlib
import zipfile

spec = importlib.util.spec_from_file_location('ttc_local',Path(__file__).parents[1]/'local'/'ttc_local.py')
ttc = importlib.util.module_from_spec(spec); spec.loader.exec_module(ttc)


class Checks(unittest.TestCase):
    def test_folder_browser(self):
        with tempfile.TemporaryDirectory(prefix='TTC browse ') as tmp:
            root=Path(tmp)
            for name in ('zebra','Alpha','r\u00e4ksm\u00f6rg\u00e5s'):
                (root/name).mkdir()
            (root/'capture.DNG').write_bytes(b'')
            (root/'other.txt').write_text('not an image')
            result=ttc.browse_folders(str(root))
            self.assertEqual([f['name'] for f in result['folders']],['Alpha','r\u00e4ksm\u00f6rg\u00e5s','zebra'])
            self.assertEqual(result['image_count'],1)
            self.assertEqual(Path(result['parent']).resolve(),root.parent.resolve())
            self.assertTrue(result['roots'])
            child=ttc.browse_folders(str(root/'Alpha'))
            self.assertEqual(child['folders'],[])
            self.assertEqual(Path(child['parent']).resolve(),root.resolve())
            self.assertIsNone(ttc.browse_folders(root.anchor)['parent'])
            for value in (False,12,[]):
                with self.assertRaises(ValueError):ttc.browse_folders(value)
            with self.assertRaises(ValueError):ttc.browse_folders(str(root/'other.txt'))
            with self.assertRaises(OSError):ttc.browse_folders(str(root/'missing'))
            with mock.patch.object(ttc.Path,'iterdir',side_effect=PermissionError('Access denied')):
                with self.assertRaises(PermissionError):ttc.browse_folders(str(root))

    def test_apertures(self):
        self.assertEqual(ttc.aperture_from_name('capture_f5.6_repeat2.dng'),5.6)
        self.assertEqual(ttc.aperture_from_name('f8.jpg'),8)
        self.assertIsNone(ttc.aperture_from_name('_DSC3982-_DSC3997.dng'))
        for value in [True,0,-1,'nan','inf',1000]:
            with self.assertRaises(ValueError): ttc.number(value)

    def test_roi_validation(self):
        rois = [dict(id=r,x=10,y=10,width=20,height=20) for r in ttc.REGIONS]
        self.assertEqual(len(ttc.validate_rois(rois,100,100)),5)
        for key,val in [('x',-1),('width',100),('height',1),('x',1.5)]:
            invalid=copy.deepcopy(rois); invalid[0][key]=val
            with self.assertRaises(ValueError): ttc.validate_rois(invalid,100,100)
        rois[0]['id']='tl'
        with self.assertRaises(ValueError): ttc.validate_rois(rois,100,100)

    def test_whole_capture_and_spread(self):
        def frame(fid,values):
            return dict(id=fid,aperture=4.,flags=[],regions=[dict(id=r,sharpness=v,status='tracked') for r,v in zip(ttc.REGIONS,values)])
        m=dict(frames=[frame('a',[1,1,1,1,.5]),frame('b',[.9,.9,.9,.9,.9])])
        ttc.regroup(m,{})
        self.assertEqual(m['groups'][0]['selected_frame_id'],'b')
        self.assertFalse(m['frames'][0]['selected'])
        self.assertEqual(m['frames'][0]['regions'][-1]['uncertainty'],.2)
        self.assertIn('repeat-disagreement',m['groups'][0]['flags'])
        ttc.regroup(m,{'4.0':'a'})
        self.assertEqual(m['groups'][0]['selected_frame_id'],'a')
        m['frames'][0]['regions'][0]['status']='tracking-ambiguous'
        ttc.regroup(m,{})
        self.assertEqual(m['groups'][0]['selected_frame_id'],'b')
        self.assertIsNone(m['frames'][1]['regions'][0]['uncertainty'])

    def test_http_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager=ttc.Manager('unused',tmp)
            server=ttc.make_server(manager)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base=f'http://127.0.0.1:{server.server_port}'
            try:
                token=json.load(urllib.request.urlopen(base+'/api/session'))['token']
                def request(path,data=None,**headers):
                    req=urllib.request.Request(base+path,data=data,headers=headers)
                    try:
                        with urllib.request.urlopen(req) as response:return response.status
                    except urllib.error.HTTPError as error:return error.code
                self.assertEqual(request('/api/session',Host='evil.test'),403)
                self.assertEqual(request('/api/session',Origin='http://evil.test'),403)
                self.assertEqual(request('/api/jobs',b'{}',**{'Content-Type':'application/json'}),403)
                h={'Content-Type':'application/json','X-TTC-Token':token}
                self.assertEqual(request('/api/browse',b'{}',**{'Content-Type':'application/json'}),403)
                self.assertEqual(request('/api/browse',json.dumps({'path':tmp}).encode(),**h),200)
                self.assertEqual(request('/api/browse',b'{"path":false}',**h),400)
                self.assertEqual(request('/api/browse',b'{}',Origin='http://evil.test',**h),403)
                for body in [b'[]',b'{',b'null',b'{}',b'{"input_dir":false}']:
                    self.assertEqual(request('/api/jobs',body,**h),400)
                self.assertEqual(request('/api/jobs',b'x'*65537,**h),400)
                self.assertEqual(request('/../../local/ttc_local.py'),400)
                self.assertEqual(request('/jobs/1234567890abcdef/native.log'),404)
                self.assertEqual(request('/api/jobs',b'{"auto_run":"yes"}',**h),400)
                with mock.patch.object(manager,'create',return_value={'id':'1234567890abcdef'}) as create, mock.patch.object(manager,'launch',return_value={'status':'running'}) as launch:
                    self.assertEqual(request('/api/jobs',b'{"input_dir":"example","auto_run":true}',**h),201)
                    create.assert_called_once()
                    launch.assert_called_once_with('1234567890abcdef','automatic')
                    self.assertEqual(request('/api/jobs/1234567890abcdef/automatic',b'{}',**h),200)
            finally:
                server.shutdown();server.server_close();thread.join()

    def test_native_job_and_portable_archive(self):
        engine=Path(__file__).parents[1]/'build'/'ttc-integrated.exe'
        if not engine.exists():
            engine=Path(__file__).parents[1]/'build'/'ttc-cli.exe'
        if not engine.exists():
            self.skipTest('Build native executable to run integration coverage')
        def chunk(tag,data):
            return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data))
        scan=b''.join(b'\x00'+bytes(((x*17+y*31+(x*y)%71)%190+30 for x in range(96) for c in range(3))) for y in range(96))
        png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',96,96,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(scan))+chunk(b'IEND',b'')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); inputs=root/'private-input';inputs.mkdir()
            for name in ('f4_a.png','f4_b.png','f8_a.png','unknown.png'):
                (inputs/name).write_bytes(png)
            manager=ttc.Manager(engine,root/'jobs')
            rois=[dict(id=r,x=20,y=20,width=32,height=32) for r in ttc.REGIONS]
            snapshot=manager.create(dict(input_dir=str(inputs),rois=rois,track=0))
            jid=snapshot['id'];manager.launch(jid,'analyze')
            deadline=time.monotonic()+30
            while manager.snapshot(jid)['status']=='running' and time.monotonic()<deadline:time.sleep(.02)
            self.assertEqual(manager.snapshot(jid)['status'],'complete')
            m=manager.snapshot(jid)['result'];self.assertEqual(len(m['frames']),4)
            self.assertIsNone(m['frames'][-1]['aperture'])
            revision=manager.jobs[jid]['revision']
            manager.edit(jid,dict(apertures={'f0004':8},selected={'4':'f0002'},rois=rois,track=0))
            self.assertEqual(manager.jobs[jid]['revision'],revision)
            self.assertEqual(manager.snapshot(jid)['status'],'complete')
            self.assertTrue(all(len(f['regions'])==5 for f in manager.snapshot(jid)['result']['frames']))
            self.assertEqual(manager.snapshot(jid)['result']['groups'][0]['selected_frame_id'],'f0002')
            archive=manager.export(manager.jobs[jid],True)
            with zipfile.ZipFile(archive) as z:
                manifest=json.loads(z.read('manifest.json'))
                self.assertNotIn(str(inputs),z.read('manifest.json').decode())
                self.assertNotIn(str(inputs),z.read('report.html').decode())
                self.assertNotIn('report.csv',z.namelist())
                for frame in manifest['frames']:
                    for region in frame['regions']:
                        self.assertIn(region['crop_url'],z.namelist())
                    if frame['selected']:
                        self.assertIn(frame['aligned_url'],z.namelist())
            archives=set(manager.jobs[jid]['dir'].glob('*.zip'))
            copyfile=ttc.shutil.copyfile
            def cancel_after_copy(source,destination):
                result=copyfile(source,destination)
                manager.jobs[jid]['cancel']=True
                return result
            with mock.patch.object(ttc.shutil,'copyfile',side_effect=cancel_after_copy):
                with self.assertRaises(InterruptedError):manager.export(manager.jobs[jid])
            self.assertEqual(set(manager.jobs[jid]['dir'].glob('*.zip')),archives)
            manager.jobs[jid]['cancel']=False
            changed_rois=copy.deepcopy(rois);changed_rois[0]['x']+=1
            manager.edit(jid,dict(rois=changed_rois))
            self.assertEqual(manager.snapshot(jid)['status'],'ready')
            self.assertTrue(all(not f['regions'] for f in manager.snapshot(jid)['result']['frames']))
            manager.edit(jid,dict(track=32))
            self.assertEqual(manager.snapshot(jid)['result']['tracking_radius'],32)
            with self.assertRaises(ValueError):manager.edit(jid,dict(track=33))

    def test_cancel_terminates_native_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager=ttc.Manager(sys.executable,tmp)
            job=dict(schema_version=1,id='abc',status='ready',progress=dict(completed=0,total=1,message=''),
                     error=None,result=dict(rois=[{}],frames=[],groups=[]),dir=Path(tmp),overrides={},process=None,cancel=False)
            manager.jobs['abc']=job
            manager.analyze=lambda j:manager.run_native(j,['-c','import time; time.sleep(20)'])
            manager.launch('abc','analyze')
            deadline=time.monotonic()+5
            while job['process'] is None and time.monotonic()<deadline:time.sleep(.01)
            self.assertIsNotNone(job['process'])
            manager.cancel('abc')
            while manager.snapshot('abc')['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
            self.assertEqual(manager.snapshot('abc')['status'],'cancelled')
            self.assertTrue(manager.decode_lock.acquire(blocking=False))
            manager.decode_lock.release()

    def test_cancelled_preview_is_not_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager=ttc.Manager('unused',tmp)
            job=dict(dir=Path(tmp),paths=['source.dng'],result={})
            def interrupted(job,args):
                Path(args[-1]).write_bytes(b'partial png')
                raise InterruptedError('Cancelled')
            manager.run_native=interrupted
            with self.assertRaises(InterruptedError):manager.detect(job)
            self.assertFalse(list(Path(tmp).glob('preview*.png')))

    def test_failed_detection_preserves_manual_regions(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager=ttc.Manager('unused',tmp)
            (Path(tmp)/'preview.png').write_bytes(b'cached')
            result=dict(width=100,height=100,rois=[dict(id='center',x=20,y=20,width=30,height=30)],
                        frames=[dict(regions=[dict(sharpness=42)])],groups=[dict(selected_frame_id='a')])
            saved=copy.deepcopy(result)
            job=dict(id='abc',dir=Path(tmp),result=result,cancel=False,process=None)
            worker=mock.Mock(returncode=0)
            worker.communicate.return_value=(json.dumps(dict(status='manual-required',rois=[],warnings=['uncertain'])), '')
            with mock.patch.object(ttc.subprocess,'Popen',return_value=worker):
                manager.detect(job)
            for key in ('rois','frames','groups'):
                self.assertEqual(result[key],saved[key])
            self.assertIsNone(job['process'])
            self.assertIn('retained',result['warnings'][-1])

    def test_detector_timeout_reaps_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager=ttc.Manager('unused',tmp)
            (Path(tmp)/'preview.png').write_bytes(b'cached')
            job=dict(dir=Path(tmp),result=dict(width=100,height=100),cancel=False,process=None)
            worker=mock.Mock()
            worker.communicate.side_effect=[ttc.subprocess.TimeoutExpired('detector',60),('', '')]
            with mock.patch.object(ttc.subprocess,'Popen',return_value=worker):
                with self.assertRaises(TimeoutError):manager.detect(job)
            worker.terminate.assert_called_once()
            self.assertEqual(worker.communicate.call_count,2)
            self.assertIsNone(job['process'])

    def test_automatic_detection_gate_and_cancellation(self):
        for status,cancelled in [('accepted',False),('manual-required',False),('accepted',True)]:
            with self.subTest(status=status,cancelled=cancelled), tempfile.TemporaryDirectory() as tmp:
                manager=ttc.Manager('unused',tmp)
                # Existing manual ROIs must not bypass failed automatic detection.
                job=dict(result=dict(rois=[{}]*5),progress={},cancel=False)
                def detect(j):
                    j['result']['detection']={'status':status}
                    j['cancel']=cancelled
                manager.detect=mock.Mock(side_effect=detect)
                manager.analyze=mock.Mock()
                if cancelled:
                    with self.assertRaises(InterruptedError):manager.automatic(job)
                elif status!='accepted':
                    with self.assertRaisesRegex(ValueError,'could not be verified'):manager.automatic(job)
                else:
                    manager.automatic(job)
                self.assertEqual(manager.analyze.call_count,int(status=='accepted' and not cancelled))
                manager.detect.assert_called_once_with(job)


if __name__=='__main__':unittest.main()
