"""Read-only audit of stored original-pixel corner crops; writes new diagnostics only."""
from pathlib import Path
import argparse,csv,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'local'))
import star_mtf as m
np=m.np

def edge_width(image,edge,box):
    x0,y0,x1,y1=box
    a,b=np.array(edge['line']).reshape(2,2)
    u=(b-a)/np.linalg.norm(b-a);n=np.array([-u[1],u[0]])
    y,x=np.mgrid[y0:y1,x0:x1]
    distance=(x-a[0])*n[0]+(y-a[1])*n[1]
    bins=np.floor((distance.ravel()+32)*2).astype(int)
    keep=(bins>=0)&(bins<128)
    count=np.bincount(bins[keep],minlength=128)
    sums=np.bincount(bins[keep],weights=image[y0:y1,x0:x1].ravel()[keep],minlength=128)
    d=(np.arange(128)+.5)/2-32
    valid=(count>=5)&(np.abs(d)<26)
    d=d[valid];p=sums[valid]/count[valid]
    if not np.any(d<-20) or not np.any(d>20):raise ValueError('Insufficient plateau samples')
    left=np.median(p[d<-20]);right=np.median(p[d>20])
    if not np.isfinite([left,right]).all() or abs(right-left)<.03:raise ValueError('Insufficient edge contrast')
    p=(p-left)/(right-left)
    def crossing(level):
        idx=np.flatnonzero((p[:-1]<level)&(p[1:]>=level))
        if not len(idx):raise ValueError('No edge crossing')
        i=idx[np.argmin(np.abs(d[idx]))]
        return float(d[i]+(level-p[i])*(d[i+1]-d[i])/(p[i+1]-p[i]))
    width=crossing(.9)-crossing(.1)
    if not 0<width<40:raise ValueError('Invalid transition width')
    return dict(width=width,distance=d.tolist(),response=p.tolist())

def run(source,manifest,output,mapper):
    output.mkdir(parents=True,exist_ok=False)
    result=json.loads((source/'measurements.json').read_text())
    captures=json.loads(manifest.read_text())['frames'];records=[]
    if len(captures)!=len(result['frames']):raise ValueError('Capture count mismatch')
    with (source/'report.csv').open(newline='',encoding='utf-8') as stream:rows=list(csv.DictReader(stream))
    offset=0
    for i,frame in enumerate(result['frames']):
        print(f'Capture {i+1}/{len(captures)}',flush=True)
        if Path(rows[offset]['image']).name!=captures[i]['label']:raise ValueError('Capture identity mismatch')
        offset+=len(frame)
        for region,star in enumerate(frame):
            if not star['id'].startswith('outer_'):continue
            image=m.cv2.imread(str(source/f'frame-{i+1:04}-roi-{region+1:02}.png'))
            if image is None or image.shape[:2]!=(star['source_box'][3],star['source_box'][2]):raise ValueError('Missing or mismatched original crop')
            linear=m.linear_luminance(image)
            for j,edge in enumerate(star['edges']):
                if edge['status']!='accepted':continue
                record=dict(frame=i+1,aperture=captures[i]['aperture'],region=star['id'],direction=edge['direction'],mtf50=edge['mtf50'],slant=edge['slant'],tracking=star['tracking'],line=edge['line'],supporting=[e['mtf50'] for e in edge.get('supporting_edges',[]) if e['status']=='accepted'])
                record['linear_edge']=edge_width(linear,edge,edge['box'])
                record['encoded_width']=edge_width(image.mean(axis=2)/255,edge,edge['box'])['width']
                record['green_width']=edge_width(image[:,:,1]/255,edge,edge['box'])['width']
                record['alternatives']=[]
                for k,(start,stop) in enumerate(((.06,.18),(.10,.22))):
                    box=m.edge_box(edge,start,stop,32);reason=m.isolated_edge(linear,edge,box)
                    if reason:record['alternatives'].append(dict(status='rejected',reason=reason));continue
                    x0,y0,x1,y1=box
                    if np.mean(np.any((image[y0:y1,x0:x1]==0)|(image[y0:y1,x0:x1]==255),axis=2))>.005:
                        record['alternatives'].append(dict(status='rejected',reason='RGB clipping'));continue
                    try:
                        value=m.mapper_measure(mapper,linear[y0:y1,x0:x1],output/f'{i}-{region}-{j}-{k}',edge['angle'])
                        record['alternatives'].append(dict(status='accepted',mtf50=value['mtf50']))
                    except ValueError as exc:record['alternatives'].append(dict(status='rejected',reason=str(exc)))
                records.append(record)
    (output/'audit.json').write_text(json.dumps(records,allow_nan=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--mapper',type=Path,required=True);a=p.parse_args();run(a.source,a.manifest,a.output,a.mapper)
