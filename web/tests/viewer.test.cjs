const {test}=require('node:test');
const assert=require('node:assert/strict');
const {color,valid,groups,normalize,escape,apertureEdits,manualRois}=require('../viewer.js');
test('near ties retain near-identical colors, not min-max exaggeration',()=>{
 const a=color(100,100).match(/\d+/g).map(Number),b=color(99,100).match(/\d+/g).map(Number);
 assert.ok(a.every((n,i)=>Math.abs(n-b[i])<=1));assert.equal(color(0,0),'#29343d');
});
test('invalid and rejected measurements never get ranked',()=>{
 for(const value of [null,NaN,Infinity,-1])assert.equal(valid({value}),false);
 assert.equal(valid({value:42,status:'rejected'}),false);assert.equal(valid({value:0,status:'accepted'}),true);
 assert.equal(valid({value:42,status:'tracking-ambiguous'}),false);assert.equal(valid({value:42,status:'too-dark'}),false);
});
test('f-stops sort numerically and whole capture selection applies across regions',()=>{
 const m=normalize({frames:[{id:'b',aperture:11,regions:[]},{id:'a',aperture:2.8,regions:[]},{id:'c',aperture:2.8,regions:[]}],groups:[{aperture:2.8,selected_frame_id:'c'}]});
 assert.deepEqual(groups(m).map(g=>[g.value,g.selectedCaptureId]),[[2.8,'c'],[11,'b']]);
});
test('unknown apertures retained outside heatmap and native crop dimensions preserved',()=>{
 const m=normalize({frames:[{id:'a',aperture:null,regions:[{id:'center',sharpness:4,status:'accepted',width:1024,height:768,crop_url:'assets/c.png'}]}]});
 assert.equal(m.captures.length,1);assert.equal(groups(m).length,0);assert.equal(m.captures[0].measurements.center.crop.width,1024);
});
test('source labels cannot inject markup',()=>assert.equal(escape('<img src=x onerror="x">'),'&lt;img src=x onerror=&quot;x&quot;&gt;'));
test('an aperture without a trustworthy whole capture never silently selects a repeat',()=>{
 const m=normalize({frames:[{id:'bad',aperture:4,regions:[]}],groups:[{aperture:4,selected_frame_id:null,flags:['No valid capture']}]});
 assert.equal(groups(m)[0].selectedCaptureId,null);assert.deepEqual(groups(m)[0].flags,['No valid capture']);
});
test('saving ROI corrections preserves untouched metadata aperture provenance',()=>{
 const original=[{id:'a',aperture:3.5},{id:'b',aperture:null}];
 assert.deepEqual(apertureEdits([{id:'a',aperture:3.5},{id:'b',aperture:4}],original),{b:4});
});
test('explicit manual fallback creates five bounded editable starting boxes',()=>{
 const rois=manualRois(19136,12752);assert.deepEqual(rois.map(r=>r.id),['center','tl','tr','bl','br']);
 for(const r of rois){assert.ok(r.x>=0&&r.y>=0&&r.x+r.width<=19136&&r.y+r.height<=12752);assert.ok(Number.isInteger(r.x));}
 assert.deepEqual(manualRois(0,0),[]);
});
