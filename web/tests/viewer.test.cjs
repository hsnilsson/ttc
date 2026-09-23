const {test}=require('node:test');
const assert=require('node:assert/strict');
const {TABLE_REGIONS,sharpnessTotals,color,valid,groups,normalize,escape,apertureEdits,manualRois,roiLabelClass,RoiHistory}=require('../viewer.js');
test('loaded row range uses the full spectrum, including near ties',()=>{
 assert.notEqual(color(99,99,100),color(100,99,100));
 assert.equal(color(99,99,100),color(0,0,100));
 assert.equal(color(100,99,100),color(100,0,100));
 assert.equal(color(0,0,0),color(100,100,100));
 assert.equal(color(NaN,0,1),'#29343d');
 assert.notEqual(color(99.5,99,100),color(99,99,100));
});
test('ROI undo groups edits and reset itself can be undone without changing saved positions',()=>{
 const original=manualRois(1600,1200),history=new RoiHistory(original);
 const moved=history.current;moved[0].x+=30;history.push(moved);history.push(moved);
 assert.equal(history.steps.length,2);assert.deepEqual(history.undo(),original);
 history.push(moved);const resized=history.current;resized[1].width+=10;history.push(resized);
 assert.deepEqual(history.reset(),original);assert.deepEqual(history.undo(),resized);
 assert.deepEqual(history.undo(),moved);assert.deepEqual(history.undo(),original);
 assert.deepEqual(history.baseline,original);
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
test('every region label has a dedicated outside-overlay position class',()=>{
 assert.deepEqual(['center','tl','tr','bl','br'].map(roiLabelClass),[
  'roi-label roi-label-center','roi-label roi-label-tl','roi-label roi-label-tr','roi-label roi-label-bl','roi-label roi-label-br'
 ]);
 assert.equal(roiLabelClass('unexpected'),'roi-label roi-label-other');
});

test('total uses five valid regions of the selected whole capture and marks ties',()=>{
 const capture=(id,aperture,values)=>({id,aperture,measurements:Object.fromEntries(['center','tl','tr','bl','br'].map((r,i)=>[r,{value:values[i],status:'accepted'}]))});
 const m={captures:[capture('a',4,[1,2,3,4,5]),capture('unused',4,[9,9,9,9,9]),capture('b',5.6,[2,2,3,4,5]),capture('c',8,[2,2,3,4,5])],apertures:[{value:4,selectedCaptureId:'a'},{value:5.6,selectedCaptureId:'b'},{value:8,selectedCaptureId:'c'}]};
 assert.deepEqual(sharpnessTotals(m).map(t=>[t.value,t.best]),[[15,false],[16,true],[16,true]]);
 m.captures[2].measurements.tr.status='rejected';
 assert.equal(sharpnessTotals(m)[1].value,null);
 m.apertures[2].selectedCaptureId=null;
 assert.deepEqual(sharpnessTotals(m).map(t=>t.best),[true,false,false]);
 assert.deepEqual(TABLE_REGIONS,['tl','tr','center','bl','br']);
});
