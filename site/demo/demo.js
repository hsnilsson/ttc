/* Explicit public-demo transport. No native service or filesystem access. */
(function () {
  'use strict';
  const FOLDER='D:\\Demo captures', ROOT='D:\\';
  const clone=value=>JSON.parse(JSON.stringify(value));
  const WARNING='DEMO — timings, detection and sharpness scores are simulated. Images are example captures, not measurements of your setup.';
  function createDemo(sample,options={}) {
    const schedule=options.schedule||setTimeout,unschedule=options.unschedule||clearTimeout;
    const load=options.load||((url)=>fetch(url));
    let result={captures:[],apertures:[],rois:[],warnings:[WARNING]},status='ready',progress=null,timer=null,generation=0,writeZip=null,exportUrl=null;
    const snapshot=()=>clone({id:'demo',status,progress,result});
    function regroup(overrides={}) {
      const prior=new Map((result.apertures||[]).map(g=>[g.value,g.selectedCaptureId]));
      result.apertures=[...new Set(result.captures.map(c=>c.aperture).filter(a=>a>0))].sort((a,b)=>a-b).map(value=>{
        const candidates=result.captures.filter(c=>c.aperture===value);
        const preferred=overrides[value]||prior.get(value);
        return {value,selectedCaptureId:candidates.some(c=>c.id===preferred)?preferred:candidates[0].id,flags:[]};
      });
    }
    function invalidate() {
      for(const c of result.captures)c.measurements={};
      invalidateExport();
    }
    function invalidateExport() {
      delete result.export_url;
      if(exportUrl){URL.revokeObjectURL(exportUrl);exportUrl=null;}
    }
    function detect() {
      result.preview=clone(sample.preview);result.rois=clone(sample.rois);
    }
    function measure() {
      for(const c of result.captures)c.measurements=clone(sample.captures.find(s=>s.id===c.id).measurements);
      regroup();
    }
    function stop() {
      generation++;if(timer!==null)unschedule(timer);timer=null;
    }
    function launch(kind) {
      stop();invalidate();status='running';
      const ticket=generation;
      const stages=kind==='detect'?['Rendering example target preview…','Locating five example target regions…']:kind==='automatic'?['Rendering example target preview…','Locating five example target regions…',...result.captures.map((c,i)=>`Measuring and aligning capture ${i+1} of ${result.captures.length}…`)]:result.captures.map((c,i)=>`Measuring and aligning capture ${i+1} of ${result.captures.length}…`);
      let i=0;
      function tick(){
        if(ticket!==generation)return;
        if(i===stages.length){if(kind!=='analyze')detect();if(kind!=='detect')measure();status=kind==='detect'?'ready':'complete';progress={completed:i,total:i,message:'Demo '+(kind==='detect'?'target regions ready to review.':'comparison complete. Timings and scores were simulated.')};timer=null;return;}
        if(kind==='automatic'&&i===2)detect();
        progress={completed:i,total:stages.length,message:'Simulated · '+stages[i++]};
        timer=schedule(tick,kind==='detect'?650:300);
      }
      tick();return snapshot();
    }
    function validateRois(rois) {
      if(!Array.isArray(rois)||rois.length!==5||new Set(rois.map(r=>r.id)).size!==5||rois.some(r=>!sample.rois.some(s=>s.id===r.id)||!['x','y','width','height'].every(k=>Number.isInteger(r[k]))||r.x<0||r.y<0||r.width<1||r.height<1||r.x+r.width>sample.width||r.y+r.height>sample.height))throw Error('Keep all five regions within the example target.');
    }
    async function buildReport(ticket) {
      try{
        const exported=clone(result),urls=new Set([exported.preview?.url,...exported.captures.flatMap(c=>Object.values(c.measurements).map(m=>m.crop?.url))].filter(Boolean));
        const files=[],encoder=new TextEncoder();
        // Process sequentially to keep report memory and network requests bounded.
        for(const url of [...urls,'viewer.css','viewer.js']){
          const response=await load(url);if(!response.ok)throw Error('Could not load example report asset: '+url);
          files.push({name:url,data:new Uint8Array(await response.arrayBuffer())});
          if(ticket!==generation)return;
          progress={completed:files.length,total:urls.size+3,message:'Simulated export · Packaging example report assets…'};
        }
        const response=await load('report.html');if(!response.ok)throw Error('Could not load report template.');
        const html=(await response.text()).replace('>null</script>','>'+JSON.stringify(exported).replace(/</g,'\\u003c')+'</script>');
        files.push({name:'index.html',data:encoder.encode(html)},{name:'manifest.json',data:encoder.encode(JSON.stringify(exported,null,2))});
        if(ticket!==generation)return;
        exportUrl=URL.createObjectURL(writeZip(files));result.export_url=exportUrl;status='complete';progress={completed:1,total:1,message:'Example offline report ready. Contains simulated scores.'};
      }catch(e){if(ticket===generation){status='failed';progress={message:e.message};}}
    }
    async function request(path,body) {
      if(path==='session')return {token:'demo-only'};
      if(path==='state')return snapshot();
      if(path==='browse'){
        const value=(body?.path||FOLDER).trim().replace(/\//g,'\\').replace(/\\+$/,'').toLowerCase();
        if(![FOLDER.replace(/\\+$/,'').toLowerCase(),'d:'].includes(value))throw Error('This simulated computer contains only D:\\Demo captures. Choose the Demo captures shortcut.');
        const atRoot=value==='d:';
        return {path:atRoot?ROOT:FOLDER,parent:atRoot?null:ROOT,image_count:atRoot?0:sample.captures.length,roots:[{name:'Demo captures',path:FOLDER},{name:'D:',path:ROOT}],folders:atRoot?[{name:'Demo captures',path:FOLDER}]:[]};
      }
      if(path==='shutdown'){if(typeof window!=='undefined')window.location.reload();return {};}
      if(path==='jobs'){
        if((body?.input_dir||'').trim().replace(/\\+$/,'').toLowerCase()!==FOLDER.toLowerCase())throw Error('Use D:\\Demo captures to import the example series. Your own folders are available in the downloaded app.');
        if(status==='running')throw Error('Wait for the simulation or cancel it first.');
        stop();invalidate();result=clone(sample);invalidate();result.preview=null;result.rois=[];status='ready';progress={message:'Example series opened. Detect target regions or run the automatic comparison.'};regroup();
        return body.auto_run?launch('automatic'):snapshot();
      }
      if(path==='jobs/demo')return snapshot();
      const action=path.replace(/^jobs\/demo\//,'');
      if(action==='cancel'){stop();status='cancelled';progress={message:'Simulation cancelled. Run again when ready.'};return snapshot();}
      if(status==='running')throw Error('Wait for the simulation or cancel it first.');
      if(action==='edit'){
        const apertures=body.apertures||{},rois=body.rois;
        if(rois)validateRois(rois);
        for(const value of Object.values(apertures))if(value!==null&&(!Number.isFinite(value)||value<.1||value>256))throw Error('Aperture must be between 0.1 and 256.');
        if(body.track!=null&&(!Number.isInteger(body.track)||!(body.track===0||body.track>=3&&body.track<=32)))throw Error('Search radius must be 0 or 3–32 pixels.');
        for(const [aperture,id] of Object.entries(body.selected||{}))if(!result.captures.some(c=>c.id===id&&c.aperture===Number(aperture)))throw Error('Choose a capture belonging to this aperture.');
        const changed=rois&&JSON.stringify(rois)!==JSON.stringify(result.rois)||body.track!=null&&body.track!==result.tracking_radius;
        for(const c of result.captures)if(Object.hasOwn(apertures,c.id)){c.aperture=apertures[c.id];c.apertureSource='manual (demo)';}
        if(rois)result.rois=clone(rois);if(body.track!=null)result.tracking_radius=body.track;
        invalidateExport();
        if(changed){invalidate();status='ready';}
        regroup(body.selected);progress={message:changed?'Corrections saved. Re-run the simulation; example crops and scores remain illustrative.':'Demo selections saved.'};return snapshot();
      }
      if(['detect','automatic','analyze'].includes(action)){
        if(!result.captures.length)throw Error('Open the example folder first.');
        if(action==='analyze'&&result.rois.length!==5)throw Error('Detect or define five regions before running.');
        return launch(action);
      }
      if(action==='export'){
        if(!result.captures.some(c=>Object.keys(c.measurements).length))throw Error('Run the example comparison before exporting.');
        stop();delete result.export_url;if(exportUrl)URL.revokeObjectURL(exportUrl);exportUrl=null;
        status='running';progress={message:'Packaging example offline report…'};void buildReport(generation);return snapshot();
      }
      throw Error('Unsupported demo action.');
    }
    return {folder:FOLDER,request,setZipWriter:writer=>{writeZip=writer;}};
  }
  if(typeof module!=='undefined')module.exports={createDemo,FOLDER,WARNING};
  if(typeof document==='undefined')return;
  const sample=fetch('sample.json').then(r=>{if(!r.ok)throw Error('Example series unavailable.');return r.json();});
  let writeZip;
  const instance=sample.then(data=>{const demo=createDemo(data);demo.setZipWriter(writeZip);return demo;});
  window.TTC_DEMO={folder:FOLDER,setZipWriter:writer=>{writeZip=writer;},request:async(path,body)=>{const demo=await instance;demo.setZipWriter(writeZip);return demo.request(path,body);}};
})();
