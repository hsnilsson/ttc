"""End-to-end fringe CSV, service and portable report checks (run native fringe_checks first)."""
import csv
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import tempfile
import zipfile
import threading
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ttc_local',ROOT/'local/ttc_local.py')
ttc=importlib.util.module_from_spec(spec);spec.loader.exec_module(ttc)

def run(root):
    inputs=root/'inputs';inputs.mkdir()
    shutil.copyfile(ROOT/'build/fringe-f4.png',inputs/'fringe-f4.png')
    shutil.copyfile(ROOT/'build/invalid-f8.png',inputs/'invalid-f8.png')
    manager=ttc.Manager(ROOT/'build/ttc-cli.exe',root/'jobs')
    rois=[dict(id=id,x=i*128,y=16,width=128,height=128) for i,id in enumerate(ttc.REGIONS)]
    state=manager.create(dict(input_dir=str(inputs),rois=rois,track=0))
    job=manager.jobs[state['id']]
    manager.analyze(job)
    regions=job['result']['frames'][0]['regions']
    assert len(regions)==5
    scores=[]
    for region in regions:
        f=region['fringe'];assert f['status']=='accepted', f
        scores.append(f['score'])
        assert f['algorithm']=='rgb-edge-residual-v1' and f['pixels']>=32 and f['baseline_pixels']>=32
        assert region['crop_url'] and f['overlay_url']
    assert scores[0]<1e-6 and all(a<b for a,b in zip(scores,scores[1:])),scores
    rejected=job['result']['frames'][1]['regions']
    assert [r['fringe']['status'] for r in rejected]==['low-contrast','too-dark','clipped','insufficient-edges','insufficient-baseline']
    assert all(r['fringe']['score'] is None and r['fringe']['overlay_url'] is None for r in rejected)
    # Verify the real HTTP allowlist, not merely files present on disk.
    server=ttc.make_server(manager)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        for region in regions:
            with urllib.request.urlopen(base+region['fringe']['overlay_url']) as response:
                assert response.headers['Content-Type']=='image/png'
                assert response.read(8)==b'\x89PNG\r\n\x1a\n'
        for name in ['native.log','run-1/report.csv','run-1/frame-0001-roi-01-fringe-other.png']:
            try:
                urllib.request.urlopen(base+f"/jobs/{job['id']}/"+name)
                raise AssertionError('Nonpublic asset exposed')
            except urllib.error.HTTPError as error:
                assert error.code==400
    finally:
        server.shutdown();server.server_close();thread.join()
    archive=manager.export(job)
    with zipfile.ZipFile(archive) as z:
        m=json.loads(z.read('manifest.json'))
        assert str(root) not in z.read('manifest.json').decode()
        for region in m['frames'][0]['regions']:
            mask=z.read(region['fringe']['overlay_url'])
            assert struct.unpack('>II',mask[16:24])==(128,128) and mask[25]==6
            assert region['crop_url'] in z.namelist()
        report=root/'report';z.extractall(report)
    # A legacy native CSV without new columns remains readable and exportable.
    rows=list(csv.DictReader((job['dir']/'run-1/report.csv').open(newline='')))
    def legacy_native(job,args):
        run=Path(args[2]);run.mkdir()
        fields=[k for k in rows[0] if not k.startswith('fringe_')]
        with (run/'report.csv').open('w',newline='') as out:
            writer=csv.DictWriter(out,fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
        return '',0
    manager.run_native=legacy_native
    manager.analyze(job)
    assert all('fringe' not in r for r in job['result']['frames'][0]['regions'])
    # Accepted CSV results without a matching mask must not become trusted scores.
    def missing_mask(job,args):
        run=Path(args[2]);run.mkdir()
        with (run/'report.csv').open('w',newline='') as out:
            writer=csv.DictWriter(out,rows[0].keys());writer.writeheader();writer.writerows(rows)
        return '',0
    manager.run_native=missing_mask;manager.analyze(job)
    assert all(r['fringe']['status']=='overlay-missing' and r['fringe']['score'] is None for r in job['result']['frames'][0]['regions'])
    print('Fringe integration passed; scores:',scores)
    print('QA report:',report)
    return report

if __name__=='__main__':
    # Keep generated data under ignored build for reproducible browser QA.
    root=Path(tempfile.mkdtemp(prefix='fringe-qa-',dir=ROOT/'build'))
    run(root)
