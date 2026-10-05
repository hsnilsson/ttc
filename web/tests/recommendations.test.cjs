const {test}=require('node:test');
const assert=require('node:assert/strict');
const {apertureRecommendations:recommend,normalize,REGIONS}=require('../viewer.js');
const capture=(id,aperture,values)=>({id,aperture,measurements:Object.fromEntries(REGIONS.map((r,i)=>[r,{value:values[i],status:'tracked'}]))});
function manifest(...captures){return {captures,apertures:[...new Set(captures.map(c=>c.aperture))].map(value=>({value,selectedCaptureId:captures.find(c=>c.aperture===value).id,flags:[]}))};}
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-12,`${a} != ${b}`);

test('center, corners and balanced favor distinct apertures with explicit weighting',()=>{
 const m=manifest(capture('center',4,[100,5,50,500,5000]),capture('balanced',5.6,[95,9,90,900,9000]),capture('corners',8,[50,10,100,1000,10000]));
 const r=recommend(m);
 assert.deepEqual(r.center.apertures,[4]);assert.deepEqual(r.corners.apertures,[8]);assert.deepEqual(r.balanced.apertures,[5.6]);
 close(r.balanced.rows[1].value,.925);assert.equal(r.method,'selected-region-max-v1');
 // Independently rescaling any pattern cannot change the decision.
 for(const c of m.captures)for(const [i,id] of REGIONS.entries())c.measurements[id].value*=[.1,1000,.01,17,3][i];
 const scaled=recommend(m);
 for(const kind of ['center','corners','balanced']){
  assert.deepEqual(scaled[kind].apertures,r[kind].apertures);
  scaled[kind].rows.forEach((row,i)=>close(row.value,r[kind].rows[i].value));
 }
});

test('unselected and unknown-aperture captures cannot set normalization references',()=>{
 const m=manifest(capture('a',4,[1,1,1,1,1]),capture('b',8,[2,2,2,2,2]));
 m.captures.push(capture('unused',4,[1e8,1e8,1e8,1e8,1e8]),capture('unknown',null,[1e9,1e9,1e9,1e9,1e9]));
 const r=recommend(m);assert.deepEqual(Object.values(r.references),[2,2,2,2,2]);assert.equal(r.balanced.rows[0].value,.5);
 // An explicit whole-capture choice updates all region denominators together.
 m.apertures[0].selectedCaptureId='unused';m.apertures[0].flags=['manual-selection'];
 const changed=recommend(m);assert.deepEqual(changed.balanced.apertures,[4]);assert.ok(changed.balanced.rows[0].flags.includes('manual-selection'));
});

test('missing or rejected corners exclude only dependent summaries, without averaging survivors',()=>{
 const m=manifest(capture('a',4,[1,1,1,1,1]),capture('b',5.6,[2,2,2,2,2]),capture('c',8,[3,3,3,3,3]));
 m.captures[1].measurements.tl.status='rejected';delete m.captures[2].measurements.br;
 const r=recommend(m);assert.deepEqual(r.center.apertures,[8]);
 assert.equal(r.corners.rows[1].value,null);assert.equal(r.balanced.rows[2].value,null);
 assert.deepEqual(r.corners.rows[1].missing,['tl']);assert.equal(r.corners.state,'insufficient');assert.deepEqual(r.corners.apertures,[]);
 m.apertures[0].selectedCaptureId=null;
 assert.equal(recommend(m).center.rows[0].value,null);
});

test('zero references and invalid values never produce a fabricated recommendation',()=>{
 const zeros=manifest(capture('a',4,[0,0,0,0,0]),capture('b',8,[0,0,0,0,0]));
 const r=recommend(zeros);assert.equal(r.center.state,'insufficient');assert.equal(r.balanced.rows[0].value,null);assert.deepEqual(r.center.rows[0].noSignal,['center']);
 for(const value of [null,NaN,Infinity,-1,true,'1']){
  const m=manifest(capture('a',4,[1,1,1,1,1]),capture('bad',8,[value,1,1,1,1]));
  assert.equal(recommend(m).center.rows[1].value,null);assert.equal(recommend(m).balanced.state,'insufficient');
 }
 assert.equal(recommend({captures:[]}).balanced.state,'insufficient');
 assert.equal(recommend(manifest(capture('single',4,[1,1,1,1,1]))).center.rows[0].best,false);
});

test('ties and near ties retain all close choices without claiming confidence',()=>{
 const m=manifest(capture('a',4,[100,100,100,100,100]),capture('tie',5.6,[100,100,100,100,100]),capture('close',8,[98,98,98,98,98]),capture('far',11,[97.9,97.9,97.9,97.9,97.9]));
 let r=recommend(m);assert.equal(r.balanced.state,'near-tie');assert.deepEqual(r.balanced.apertures,[4,5.6,8]);
 assert.deepEqual(r.balanced.rows.map(x=>x.best),[true,true,false,false]);
 m.captures[2].measurements.center.value=90;
 r=recommend(m);assert.equal(r.balanced.state,'tie');assert.deepEqual(r.balanced.apertures,[4,5.6]);
});

test('repeat scoring preserves whole captures and flags disagreement and order overlap',()=>{
 const m=manifest(capture('a',4,[100,80,80,80,80]),capture('a2',4,[80,100,100,100,100]),capture('b',8,[90,90,90,90,90]),capture('b2',8,[85,85,85,85,85]));
 const r=recommend(m);const a=r.balanced.rows[0];
 close(a.value,.5+.5*80/90);
 close(a.repeatRange[1],.4+.5*100/90); // No imaginary [100,100,100,100,100] capture.
 assert.ok(a.flags.includes('repeat-disagreement'));assert.ok(a.flags.includes('repeat-ranking-overlap'));
 assert.ok(!r.center.rows[1].flags.includes('repeat-disagreement'));
 m.captures[1].measurements.tl.status='tracking-ambiguous';
 const incomplete=recommend(m).balanced.rows[0];assert.equal(incomplete.repeatRange,null);
 assert.ok(incomplete.flags.includes('some-repeats-unusable'));assert.ok(incomplete.flags.includes('repeat-spread-unavailable'));
});

test('clipping stays eligible with visible caveats limited to the affected summary',()=>{
 const m=manifest(capture('a',4,[1,1,1,1,1]),capture('b',8,[2,2,2,2,2]));
 m.captures[1].measurements.tl.status='clipping-warning';
 const r=recommend(m);assert.deepEqual(r.corners.apertures,[8]);assert.ok(r.corners.rows[1].flags.includes('clipping-warning'));
 assert.ok(!r.center.rows[1].flags.includes('clipping-warning'));
});

test('legacy backend manifests derive the same recommendations as demo-style manifests',()=>{
 const raw={frames:[{id:'a',aperture:4,label:'a',regions:REGIONS.map(id=>({id,sharpness:1,status:'fixed'}))},{id:'b',aperture:8,label:'b',regions:REGIONS.map(id=>({id,sharpness:2,status:'fixed'}))}],groups:[{aperture:4,selected_frame_id:'a',flags:[]},{aperture:8,selected_frame_id:'b',flags:[]}]};
 const result=recommend(normalize(raw));assert.deepEqual(result.balanced.apertures,[8]);assert.equal(result.balanced.rows[0].value,.5);
});
