const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {createDemo,FOLDER,WARNING}=require('../../site/demo/demo.js');
const {zipStore}=require('../viewer.js');
const sample=()=>JSON.parse(fs.readFileSync(path.join(__dirname,'../../site/demo/sample.json'),'utf8'));
function harness(options={}){
  const queue=new Map();let serial=0;
  const demo=createDemo(sample(),{schedule:fn=>{queue.set(++serial,fn);return serial;},unschedule:id=>queue.delete(id),...options});
  return {demo,async finish(){while(queue.size){const [id,fn]=queue.entries().next().value;queue.delete(id);fn();}return demo.request('jobs/demo');}};
}
async function open(demo,auto_run=false){return demo.request('jobs',{input_dir:FOLDER,auto_run});}
test('demo starts empty and browses only a simulated folder tree',async()=>{
  const {demo}=harness();assert.equal((await demo.request('state')).result.captures.length,0);
  const folder=await demo.request('browse',{path:FOLDER});assert.equal(folder.image_count,16);assert.equal(folder.parent,'D:\\');
  assert.equal((await demo.request('browse',{path:'D:\\'})).folders[0].path,FOLDER);
  await assert.rejects(demo.request('browse',{path:'C:\\private'}),/simulated computer/);
  await assert.rejects(demo.request('jobs',{input_dir:'C:\\private'}),/downloaded app/);
});
test('automatic workflow publishes preview, five regions and all captures after simulated stages',async()=>{
  const h=harness();const running=await open(h.demo,true);assert.equal(running.status,'running');assert.equal(running.result.rois.length,0);
  const done=await h.finish();assert.equal(done.status,'complete');assert.equal(done.result.rois.length,5);assert.equal(done.result.captures.length,16);
  assert.equal(done.result.apertures.length,8);assert.ok(done.result.captures.every(c=>Object.keys(c.measurements).length===5));
  assert.match(done.progress.message,/simulated/);assert.ok(done.result.warnings.includes(WARNING));
});
test('manual import, detection and measurement require five regions',async()=>{
  const h=harness();await open(h.demo);await assert.rejects(h.demo.request('jobs/demo/analyze',{}),/five regions/);
  await h.demo.request('jobs/demo/detect',{});const detected=await h.finish();assert.equal(detected.status,'ready');assert.equal(detected.result.rois.length,5);
  assert.ok(detected.result.captures.every(c=>!Object.keys(c.measurements).length));
  await h.demo.request('jobs/demo/analyze',{});assert.equal((await h.finish()).status,'complete');
});
test('cancellation prevents queued stages from completing and allows rerun',async()=>{
  const h=harness();await open(h.demo,true);const cancelled=await h.demo.request('jobs/demo/cancel',{});
  assert.equal(cancelled.status,'cancelled');assert.equal((await h.finish()).status,'cancelled');
  await h.demo.request('jobs/demo/automatic',{});assert.equal((await h.finish()).status,'complete');
});
test('ROI corrections invalidate results, enforce bounds and remain editable through reruns',async()=>{
  const h=harness();await open(h.demo,true);let done=await h.finish();
  const rois=done.result.rois;rois[0].x+=1;
  const edited=await h.demo.request('jobs/demo/edit',{rois});assert.equal(edited.status,'ready');assert.equal(edited.result.rois[0].x,rois[0].x);
  assert.ok(edited.result.captures.every(c=>!Object.keys(c.measurements).length));
  await h.demo.request('jobs/demo/analyze',{});done=await h.finish();assert.deepEqual(done.result.rois,rois);
  const invalid=structuredClone(rois);invalid[0].x=-1;
  await assert.rejects(h.demo.request('jobs/demo/edit',{rois:invalid}),/within/);
  await assert.rejects(h.demo.request('jobs/demo/edit',{rois:rois.map(r=>({...r,id:'center'}))}),/five regions/);
  await assert.rejects(h.demo.request('jobs/demo/edit',{track:2}),/Search radius/);
});
test('aperture edits regroup captures and whole-capture overrides affect all regions',async()=>{
  const h=harness();await open(h.demo,true);const done=await h.finish();const first=done.result.captures[0],second=done.result.captures[1];
  const selected=await h.demo.request('jobs/demo/edit',{selected:{[first.aperture]:second.id}});
  assert.equal(selected.result.apertures[0].selectedCaptureId,second.id);
  assert.deepEqual(selected.result.captures[1].measurements,second.measurements);
  const newAperture=Math.max(...done.result.apertures.map(g=>g.value))+1;
  const edited=await h.demo.request('jobs/demo/edit',{apertures:{[first.id]:newAperture,[second.id]:null}});
  assert.equal(edited.result.apertures.find(g=>g.value===newAperture).selectedCaptureId,first.id);
  assert.equal(edited.result.captures[1].aperture,null);
  await assert.rejects(h.demo.request('jobs/demo/edit',{apertures:{[first.id]:-1}}),/Aperture/);
});
test('fresh import discards the prior simulation, edits and measurements',async()=>{
  const h=harness();await open(h.demo,true);const done=await h.finish();
  await h.demo.request('jobs/demo/edit',{apertures:{[done.result.captures[0].id]:22}});
  const fresh=await open(h.demo);assert.equal(fresh.result.captures[0].aperture,sample().captures[0].aperture);
  assert.equal(fresh.result.preview,null);assert.equal(fresh.result.rois.length,0);
  assert.ok(fresh.result.captures.every(c=>!Object.keys(c.measurements).length));
});
test('snapshot reads cannot mutate simulation state',async()=>{
  const h=harness();const state=await open(h.demo);state.result.captures[0].name='changed';
  assert.notEqual((await h.demo.request('state')).result.captures[0].name,'changed');
});
test('report export keeps synthetic labels, relative crops and viewer without demo transport',async()=>{
  const h=harness({load:async url=>new Response(url==='report.html'?fs.readFileSync(path.join(__dirname,'../report.html'),'utf8'):'example asset')});
  let files;h.demo.setZipWriter(input=>{files=input;return zipStore(input);});
  await open(h.demo,true);await h.finish();assert.equal((await h.demo.request('jobs/demo/export',{})).status,'running');
  for(let i=0;i<200&&!files;i++)await new Promise(resolve=>setImmediate(resolve));
  assert.ok(files);const done=await h.demo.request('state');assert.equal(done.status,'complete');assert.match(done.result.export_url,/^blob:/);
  const html=new TextDecoder().decode(files.find(f=>f.name==='index.html').data);
  assert.ok(html.includes(WARNING));assert.equal(html.includes('demo.js'),false);
  assert.equal(files.filter(f=>f.name.startsWith('assets/')).length,81);
  const report=JSON.parse(new TextDecoder().decode(files.find(f=>f.name==='manifest.json').data));
  assert.equal(report.export_url,undefined);assert.ok(report.captures.every(c=>Object.values(c.measurements).every(m=>m.crop.url.startsWith('assets/'))));
  await h.demo.request('jobs/demo/cancel',{});
});
test('missing report assets become a visible failure instead of a successful export',async()=>{
  const h=harness({load:async()=>new Response('',{status:404})});h.demo.setZipWriter(zipStore);await open(h.demo,true);await h.finish();
  await h.demo.request('jobs/demo/export',{});await new Promise(resolve=>setImmediate(resolve));
  const done=await h.demo.request('state');assert.equal(done.status,'failed');assert.match(done.progress.message,/report asset/);assert.equal(done.result.export_url,undefined);
});
test('editing selections invalidates a previously generated example report',async()=>{
  const h=harness({load:async url=>new Response(url==='report.html'?'>null</script>':'asset')});
  let exported=false;h.demo.setZipWriter(files=>{exported=true;return zipStore(files);});
  await open(h.demo,true);const done=await h.finish();await h.demo.request('jobs/demo/export',{});
  for(let i=0;i<200&&!exported;i++)await new Promise(resolve=>setImmediate(resolve));
  assert.ok((await h.demo.request('state')).result.export_url);
  const edited=await h.demo.request('jobs/demo/edit',{selected:{[done.result.captures[0].aperture]:done.result.captures[1].id}});
  assert.equal(edited.result.export_url,undefined);assert.equal(Object.keys(edited.result.captures[0].measurements).length,5);
});
test('cancelling an in-flight export cannot publish stale report contents',async()=>{
  let resume;
  const h=harness({load:()=>new Promise(resolve=>{resume=resolve;})});h.demo.setZipWriter(()=>{throw Error('Cancelled export must not create ZIP');});
  await open(h.demo,true);await h.finish();await h.demo.request('jobs/demo/export',{});await h.demo.request('jobs/demo/cancel',{});
  resume(new Response('asset'));await new Promise(resolve=>setImmediate(resolve));
  const done=await h.demo.request('state');assert.equal(done.status,'cancelled');assert.equal(done.result.export_url,undefined);
});
test('published sample contains only relative, existing example assets and simulation scores',()=>{
  const data=sample(),serialized=JSON.stringify(data);assert.equal(/(?:[A-Z]:\\|\/jobs\/|native\.log|input_dir)/i.test(serialized),false);
  const urls=[data.preview.url,...data.captures.flatMap(c=>Object.values(c.measurements).map(m=>m.crop.url))];
  assert.equal(new Set(urls).size,81);
  for(const url of urls){assert.match(url,/^assets\/[a-z0-9-]+\.webp$/);assert.ok(fs.statSync(path.join(__dirname,'../../site/demo',url)).size>0);}
  assert.ok(data.warnings.some(w=>w.includes('simulated')));
});
