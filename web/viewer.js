/* Shared local/offline viewer. No remote dependencies or telemetry. */
(function () {
  'use strict';
  const REGIONS = ['center', 'tl', 'tr', 'bl', 'br'];
  const TABLE_REGIONS = ['tl','tr','center','bl','br'];
  const LABELS = {center:'Center',tl:'Top left',tr:'Top right',bl:'Bottom left',br:'Bottom right'};
  const COMPOSITE_REGIONS = ['tl','tr','bl','br','center'];
  // Labels are deliberately outside their editable rectangle: the crosshair,
  // not a label, marks the pixel coordinate used as the measurement center.
  const roiLabelClass = id => `roi-label roi-label-${REGIONS.includes(id) ? id : 'other'}`;
  const escape = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const valid = m => Boolean(m && Number.isFinite(m.value) && m.value >= 0 && ['accepted','reference','fixed','tracked','clipping-warning'].includes(m.status));
  // Map values onto the supplied range; equal values remain equal.
  function color(value, minimum, maximum) {
    if (![value,minimum,maximum].every(Number.isFinite)) return '#29343d';
    const t=maximum>minimum?Math.max(0,Math.min(1,(value-minimum)/(maximum-minimum))):.5;
    const stops=[[61,54,139],[36,126,157],[66,179,137],[211,211,94],[250,225,90]];
    const position=t*(stops.length-1),i=Math.min(stops.length-2,Math.floor(position)),f=position-i;
    return `rgb(${stops[i].map((v,j)=>Math.round(v+(stops[i+1][j]-v)*f)).join(' ')})`;
  }
  const copyRois=rois=>rois.map(r=>({...r}));
  class RoiHistory {
    constructor(rois){this.baseline=copyRois(rois);this.steps=[copyRois(rois)];}
    get current(){return copyRois(this.steps[this.steps.length-1]);}
    push(rois){if(JSON.stringify(rois)!==JSON.stringify(this.current))this.steps.push(copyRois(rois));}
    undo(){if(this.steps.length>1)this.steps.pop();return this.current;}
    reset(){this.push(this.baseline);return this.current;}
  }
  function groups(manifest) {
    const values = [...new Set(manifest.captures.map(c=>Number(c.aperture)).filter(a=>a>0))].sort((a,b)=>a-b);
    return values.map(value=>{
      const captures=manifest.captures.filter(c=>Number(c.aperture)===value);
      const selection=(manifest.apertures||[]).find(a=>Number(a.value)===value);
      return {value,captures,flags:selection?.flags||[],selectedCaptureId:selection?selection.selectedCaptureId:(captures.find(c=>c.selected)?.id || captures[0].id)};
    });
  }
  function normalize(raw) {
    if (!raw.frames) return raw;
    return {...raw,captures:raw.frames.map(f=>({...f,name:f.label,apertureSource:f.aperture_source,measurements:Object.fromEntries((f.regions||[]).map(r=>[r.id,{...r,value:r.sharpness,crop:r.crop_url?{url:r.crop_url,width:r.width,height:r.height}:null}]))})),apertures:(raw.groups||[]).map(g=>({value:g.aperture,selectedCaptureId:g.selected_frame_id,flags:g.flags})),preview:raw.preview_url?{url:raw.preview_url,width:raw.width,height:raw.height}:null};
  }
  const apertureEdits=(captures,original)=>Object.fromEntries(captures.filter(c=>c.aperture!==original.find(o=>o.id===c.id)?.aperture).map(c=>[c.id,c.aperture]));
  function manualRois(width,height){if(!(width>=16&&height>=16))return [];const size=Math.max(8,Math.round(Math.min(width,height)*.05));return REGIONS.map((id,i)=>{const [cx,cy]=[[.5,.5],[.15,.15],[.85,.15],[.15,.85],[.85,.85]][i];return {id,x:Math.round(cx*width-size/2),y:Math.round(cy*height-size/2),width:size,height:size};});}
  function progressValue(progress){return progress&&Number.isFinite(progress.completed)&&Number.isFinite(progress.total)&&progress.total>0?Math.max(0,Math.min(1,progress.completed/progress.total)):null;}
  function compositeLayout(sizes){
    const left=Math.max(sizes.tl?.width||0,sizes.bl?.width||0),right=Math.max(sizes.tr?.width||0,sizes.br?.width||0);
    const top=Math.max(sizes.tl?.height||0,sizes.tr?.height||0),bottom=Math.max(sizes.bl?.height||0,sizes.br?.height||0);
    const width=left+right,height=top+bottom,center=sizes.center||{width:0,height:0};
    return {width,height,placements:{tl:{x:left-(sizes.tl?.width||0),y:top-(sizes.tl?.height||0)},tr:{x:left,y:top-(sizes.tr?.height||0)},bl:{x:left-(sizes.bl?.width||0),y:top},br:{x:left,y:top},center:{x:Math.round((width-center.width)/2),y:Math.round((height-center.height)/2)}}};
  }
  function crc32(bytes){let c=-1;for(const b of bytes){c^=b;for(let k=0;k<8;k++)c=(c>>>1)^(0xedb88320&-(c&1));}return (c^-1)>>>0;}
  function zipStore(files){
    const encoder=new TextEncoder(),chunks=[],central=[];let offset=0;
    const u16=n=>Uint8Array.of(n&255,n>>>8&255),u32=n=>Uint8Array.of(n&255,n>>>8&255,n>>>16&255,n>>>24&255);
    for(const file of files){
      const name=encoder.encode(file.name),data=file.data,crc=crc32(data);
      const local=[u32(0x04034b50),u16(20),u16(0),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0),name,data];
      chunks.push(...local);central.push({name,crc,size:data.length,offset});offset+=local.reduce((sum,part)=>sum+part.length,0);
    }
    const centralStart=offset;
    for(const file of central){
      const record=[u32(0x02014b50),u16(20),u16(20),u16(0),u16(0),u16(0),u16(0),u32(file.crc),u32(file.size),u32(file.size),u16(file.name.length),u16(0),u16(0),u16(0),u16(0),u32(0),u32(file.offset),file.name];
      chunks.push(...record);offset+=record.reduce((sum,part)=>sum+part.length,0);
    }
    chunks.push(u32(0x06054b50),u16(0),u16(0),u16(central.length),u16(central.length),u32(offset-centralStart),u32(centralStart),u16(0));
    return new Blob(chunks,{type:'application/zip'});
  }
  function sharpnessRange(manifest){
    const values=groups(manifest).flatMap(g=>{
      const capture=g.captures.find(c=>c.id===g.selectedCaptureId);
      return REGIONS.map(r=>capture?.measurements?.[r]).filter(valid).map(m=>m.value);
    });
    return {min:values.length?Math.min(...values):null,max:values.length?Math.max(...values):null};
  }
  function sharpnessTotals(manifest){
    const totals=groups(manifest).map(g=>{
      const capture=g.captures.find(c=>c.id===g.selectedCaptureId);
      const measurements=REGIONS.map(r=>capture?.measurements?.[r]);
      return {aperture:g.value,value:measurements.every(valid)?measurements.reduce((sum,m)=>sum+m.value,0):null};
    });
    const best=Math.max(...totals.filter(t=>Number.isFinite(t.value)).map(t=>t.value));
    return totals.map(t=>({...t,best:Number.isFinite(t.value)&&Math.abs(t.value-best)<=Number.EPSILON*Math.max(1,Math.abs(best))*8}));
  }
  const api = {TABLE_REGIONS, sharpnessRange, sharpnessTotals, REGIONS, valid, color, groups, escape, normalize, apertureEdits, manualRois, roiLabelClass, RoiHistory, compositeLayout, crc32, progressValue};
  if (typeof module !== 'undefined') module.exports=api;
  if (typeof document === 'undefined') return;
  let manifest={captures:[],apertures:[],rois:[]}, offline=false, apertureIndex=0, region='center', repeatId=null, zoom=1, pan={x:0,y:0}, focused=false, polling=null, token=null, jobId=null, pendingExport=false, setupOpen=true, manualDraft=false, folderPath="", requestPending=false, configDirty=false;
  let roiHistory=null, roiZoom=1, compositeRenderToken=0, compositePrewarmRunning=false;
  const compositeCache=new Map(),compositePending=new Map();
  const root=document.getElementById('app');
  const embedded=window.TTC_MANIFEST || JSON.parse(document.getElementById('ttc-manifest').textContent);
  const fmt=n=>Number.isFinite(n)?Number(n).toLocaleString(undefined,{maximumSignificantDigits:4}):'—';
  const measurement=(capture,r)=>capture?.measurements?.[r];
  const selected=()=>{const g=groups(manifest)[apertureIndex];return g?.captures.find(c=>c.id===(repeatId||g.selectedCaptureId))||g?.captures[0];};
  function error(e){document.getElementById('message').textContent=e.message||String(e);}
  async function request(path,body){const response=await fetch('/api/'+path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json','X-TTC-Token':token},body:body===undefined?undefined:JSON.stringify(body)});if(!response.ok){const message=await response.text();let detail;try{detail=JSON.parse(message).error;}catch{}throw Error(detail||message);}return response.json();}
  async function browseFolders(){
    const input=document.getElementById('folder');
    const dialog=document.createElement('dialog');
    dialog.className='folder-dialog';
    dialog.setAttribute('aria-labelledby','folder-title');
    dialog.innerHTML='<h2 id="folder-title">Choose an image folder</h2><p>Browse this computer. Images stay local.</p><div class="bar"><label class="folder-location">Location <input id="folder-location" autocomplete="off"></label><button id="folder-go">Go</button></div><div id="folder-roots" class="bar"></div><p id="folder-status" role="status"></p><div id="folder-list" class="folder-list"></div><div class="bar"><button id="folder-use" class="primary" disabled>Use this folder</button><button id="folder-close">Cancel</button></div>';
    document.body.append(dialog);
    const location=dialog.querySelector('#folder-location'),status=dialog.querySelector('#folder-status'),list=dialog.querySelector('#folder-list'),use=dialog.querySelector('#folder-use'),go=dialog.querySelector('#folder-go');
    let current=null,sequence=0;
    dialog.addEventListener('close',()=>{sequence++;dialog.remove();document.getElementById('browse')?.focus();});
    dialog.querySelector('#folder-close').onclick=()=>dialog.close();
    use.onclick=()=>{if(current){input.value=current;input.dispatchEvent(new Event('input'));dialog.close();}};
    async function load(path){
      const ticket=++sequence;
      current=null;use.disabled=true;go.disabled=true;list.replaceChildren();status.textContent='Loading folders…';
      try{
        if(!token)token=(await request('session')).token;
        const result=await request('browse',{path});
        if(ticket!==sequence||!dialog.open)return;
        current=result.path;location.value=current;
        status.textContent=`${result.image_count} supported image${result.image_count===1?'':'s'} in this folder${result.skipped?`; ${result.skipped} unavailable entries skipped`:''}.`;
        const roots=dialog.querySelector('#folder-roots');roots.replaceChildren();
        function addButton(container,label,path){const button=document.createElement('button');button.textContent=label;button.onclick=()=>load(path);container.append(button);}
        for(const root of result.roots)addButton(roots,root.name,root.path);
        if(result.parent)addButton(list,'↑ Parent folder',result.parent);
        for(const folder of result.folders)addButton(list,folder.name,folder.path);
        if(!result.folders.length){const p=document.createElement('p');p.textContent='No subfolders.';list.append(p);}
        use.disabled=false;
      }catch(e){if(ticket===sequence&&dialog.open)status.textContent='Cannot browse this folder: '+(e.message||String(e));}
      finally{if(ticket===sequence&&dialog.open)go.disabled=false;}
    }
    go.onclick=()=>load(location.value);
    location.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();load(location.value);}};
    location.value=input.value;dialog.showModal();await load(input.value);
  }
  function accept(snapshot){jobId=snapshot.id||jobId;if(jobId)sessionStorage.setItem('ttc-job',jobId);manifest=normalize(snapshot.result||snapshot.manifest||snapshot);if(snapshot.result)manifest.job={status:snapshot.status,message:snapshot.error||snapshot.progress?.message,progress:progressValue(snapshot.progress)};render();if(pendingExport&&snapshot.status!=='running'){pendingExport=false;if(manifest.export_url){const link=document.createElement('a');link.href=manifest.export_url;link.download='';link.click();}}}
  async function action(path,body){
    if(requestPending)return;
    requestPending=true;
    const controls=[...root.querySelectorAll('button,input,select')].map(el=>[el,el.disabled]);
    controls.forEach(([el])=>el.disabled=true);
    const message=document.getElementById('message');
    message.textContent=path==='import'?'Opening folder and reading image metadata…':'Applying request…';
    try{if(!token)token=(await request('session')).token;let endpoint='jobs/'+encodeURIComponent(jobId)+'/';if(path==='import'){endpoint='jobs';body={input_dir:body.directory,auto_run:body.autoRun===true};}else if(path==='config'){endpoint+='edit';body={apertures:apertureEdits(body.captures,manifest.captures),rois:body.rois,...(body.track==null?{}:{track:body.track})};}else if(path==='select'){endpoint+='edit';body={selected:{[body.aperture]:body.captureId}};}else endpoint+=path==='run'?'analyze':path;if(path==='export')pendingExport=true;const snapshot=await request(endpoint,body);if(['config','import','detect','automatic'].includes(path)){manualDraft=false;configDirty=false;roiHistory=null;if(path==='import')roiZoom=1;}accept(snapshot);}catch(e){pendingExport=false;error(e);}
    finally{requestPending=false;controls.forEach(([el,disabled])=>{if(el.isConnected)el.disabled=disabled;});}
  }
  function markConfigDirty(){
    configDirty=true;
    root.querySelectorAll('#run,#detect,#automatic,#export,#download-composite,#choose-capture').forEach(el=>el.disabled=true);
    error('Unsaved corrections. Save corrections before running or exporting.');
  }
  function render(){
    const draft=configDirty?[...root.querySelectorAll('[data-aperture],[data-roi-id],#tracking-radius')].map(el=>({id:el.id,aperture:el.dataset.aperture,roi:el.dataset.roiId,field:el.dataset.field,value:el.value})):[];
    const roiScroll=root.querySelector('.roi-scroller');
    const roiPosition=roiScroll?{x:roiScroll.scrollLeft,y:roiScroll.scrollTop}:null;
    if(!roiHistory||(!configDirty&&JSON.stringify(roiHistory.current)!==JSON.stringify(manifest.rois||[])))roiHistory=new RoiHistory(manifest.rois||[]);
    const activeId=document.activeElement?.id;
    folderPath=document.getElementById("folder")?.value??folderPath;
    const gs=groups(manifest);apertureIndex=Math.min(apertureIndex,Math.max(0,gs.length-1));
    root.innerHTML=`<div class="bar spread"><div><h1>Aperture comparison</h1><p class="muted">Compare apertures from one complete capture at a time.</p></div><span class="pill">${manifest.captures.length} captures · ${gs.length} apertures</span></div><p id="message" role="status" class="warning"></p><p class="warning">${escape((manifest.warnings||[]).join(" · "))}</p>${offline?'':setupHTML()}${gs.length?resultsHTML(gs):'<section class="panel"><h2>Your comparison starts here</h2><p class="muted">Open a local capture folder, review aperture assignments and target regions, then run the comparison.</p></section>'}<p class="footnote">Relative rendered-image detail, not calibrated MTF or universal sharpness. Colors share one scale across all five regions and apertures; target patterns differ by region. Source images remain unchanged.</p>`;
    const unknown=manifest.captures.filter(c=>!(Number(c.aperture)>0));
    if(unknown.length)root.insertAdjacentHTML('beforeend',`<section class="panel"><h2>Unassigned aperture · ${unknown.length} captures</h2><p class="muted">These captures are retained but excluded from the aperture summary. Correct their aperture in the local app.</p>${unknown.map(c=>`<p><strong>${escape(c.name||c.id)}</strong> ${escape((c.flags||[]).join(' · '))}</p><div class="bar">${REGIONS.map(r=>measurement(c,r)?.crop?`<a href="${escape(measurement(c,r).crop.url)}" download>${LABELS[r]} crop</a>`:'').join('')}</div>`).join('')}</section>`);
    if(!offline)root.insertAdjacentHTML("beforeend",'<button id="quit">Stop local service</button>');
    bind();renderCrops();
    if(configDirty){
      root.querySelectorAll('[data-aperture],[data-roi-id],#tracking-radius').forEach(el=>{const value=draft.find(d=>d.id===el.id&&d.aperture===el.dataset.aperture&&d.roi===el.dataset.roiId&&d.field===el.dataset.field);if(value)el.value=value.value;});
      markConfigDirty();
    }
    syncRoiOverlay();
    const newScroll=root.querySelector('.roi-scroller');if(newScroll&&roiPosition){newScroll.scrollLeft=roiPosition.x;newScroll.scrollTop=roiPosition.y;}
    if(manifest.job?.status === "running")root.querySelectorAll("#import,#import-auto,#browse,#quit,#save-config,#detect,#automatic,#export,#download-composite,#choose-capture,#tracking-radius,#manual-rois,#roi-undo,#roi-reset,[data-aperture],[data-roi-id]").forEach(el=>el.disabled=true);
    if(manualDraft){document.getElementById('run').disabled=true;error('Manual region draft: reposition and resize all five boxes, then Save corrections before running. These boxes are not detected targets.');}
    if(manifest.job?.status==='failed')error(manifest.job.message||'Processing failed. Review the setup and try again.');
    if(activeId)document.getElementById(activeId)?.focus({preventScroll:true});
  }
  function setupHTML(){
    return `<section class="panel"><details ${setupOpen?'open':''}><summary>1 · Images, aperture assignments & target regions</summary><p class="muted">Use a local folder path. Processing runs on this computer.</p><div class="bar"><label style="flex:1">Folder <input id="folder" value="${escape(folderPath)}" style="width:100%" placeholder="D:\\camera scanning\\vlads4"></label><button id="browse">Browse folders</button><button id="import">Open folder</button><button id="import-auto" class="primary">Open &amp; compare automatically</button></div><p class="muted">Open &amp; compare automatically reads the series, finds all five target regions, then generates the sharpness table without further clicks. It stops if detection is uncertain.</p>${manifest.captures.length?`<div class="scroll"><table><caption class="muted">Aperture: metadata first, filename second, manual correction always available.</caption><thead><tr><th>Capture</th><th>Aperture</th><th>Source</th><th>Review</th></tr></thead><tbody>${manifest.captures.map(c=>`<tr><td>${escape(c.name||c.id)}</td><td><label>f/<input data-aperture="${escape(c.id)}" type="number" min="0.1" step="0.1" value="${escape(c.aperture||'')}" aria-label="Aperture for ${escape(c.name||c.id)}"></label></td><td>${escape(c.apertureSource||'manual needed')}</td><td class="warning">${escape((c.flags||[]).join(' · '))}</td></tr>`).join('')}</tbody></table></div>${roiHTML()}<div class="bar"><button id="save-config">Save corrections</button><button id="detect">Detect target & preview</button><button id="automatic" class="primary">Detect &amp; run comparison</button></div>`:''}</details></section><section class="panel"><div class="bar spread"><div><h2>2 · Measure & align</h2><span id="job-status" role="status">${escape(manifest.job?.message||'Ready when your capture setup is confirmed.')}</span></div><div class="bar"><button id="run" class="primary" ${!manifest.captures.length||manifest.rois?.length!==5||manifest.job?.status==='running'?'disabled':''}>Run comparison</button><button id="cancel" ${manifest.job?.status==='running'?'':'disabled'}>Cancel</button></div></div>${manifest.job?.status==='running'?`<progress max="1" ${manifest.job.progress===null?'':`value="${manifest.job.progress}"`} aria-label="Processing progress"></progress>`:''}</section>`;
  }
  function roiHTML(){const p=manifest.preview;return `<div class="bar"><label>Alignment search radius <input id="tracking-radius" type="number" min="0" max="32" step="1" placeholder="Default" value="${manifest.tracking_radius??''}"> px</label><small>3–32 pixels; 0 disables tracking. Save corrections to apply.</small></div><h2>Five lp/mm / USAF measurement centers</h2>${!manifest.rois?.length&&manifest.width&&manifest.height?'<button id="manual-rois">Define regions manually</button>':''}<p class="muted">Each crosshair marks the center of one small lp/mm / USAF measurement square: center plus four corners. Labels sit outside the measured area. Corner names refer to the target’s upright chart layout, not the displayed scan orientation. Drag a rectangle to move it, or edit its pixel coordinates and size below; changes remain a draft until you Save corrections.</p>${p?`<div class="bar roi-tools"><button id="roi-undo">Undo ROI move</button><button id="roi-reset">Reset ROIs to saved</button><button id="roi-zoom-out" aria-label="Zoom target out">−</button><output id="roi-zoom-value">${Math.round(roiZoom*100)}%</output><button id="roi-zoom-in" aria-label="Zoom target in">+</button><button id="roi-fit">Fit target</button><small>Zoom to place centers precisely; scroll to reach other regions. Reset restores the last saved or detected positions.</small></div><div class="roi-scroller"><div class="roi-preview" style="width:${roiZoom*100}%"><img src="${escape(p.url)}" alt="Reference capture with five editable lp per mm and USAF measurement regions">${(manifest.rois||[]).map(r=>`<div class="roi-box" data-roi="${escape(r.id)}" style="left:${100*r.x/p.width}%;top:${100*r.y/p.height}%;width:${100*r.width/p.width}%;height:${100*r.height/p.height}%" aria-label="${escape(LABELS[r.id]||r.id)} measurement region"><i class="roi-crosshair" aria-hidden="true"></i><span class="${roiLabelClass(r.id)}">${escape(LABELS[r.id]||r.id)}</span></div>`).join('')}</div></div>`:'<p class="warning">Preview unavailable. Verify the region coordinates before processing.</p>'}${(manifest.rois||[]).map(r=>`<div class="roi-fields"><strong>${escape(LABELS[r.id]||r.id)}</strong>${['x','y','width','height'].map(k=>`<label>${k}<input data-roi-id="${escape(r.id)}" data-field="${k}" aria-label="${escape(r.id)} ${k}" type="number" min="${k==='x'||k==='y'?0:1}" step="1" value="${Number(r[k])}"></label>`).join('')}</div>`).join('')}`;}
  function totalsHTML(){
    const totals=sharpnessTotals(manifest),values=totals.filter(t=>Number.isFinite(t.value)).map(t=>t.value),min=Math.min(...values),max=Math.max(...values);
    return `<tfoot><tr class="total-gap" aria-hidden="true"><td colspan="${totals.length+1}"></td></tr><tr class="sharpness-total"><th scope="row">Total sharpness<small>Sum of 5 regions</small></th>${totals.map((t,i)=>`<td class="heatmap-value ${i===apertureIndex?'selected-column':''}" data-column="${i}" style="--cell:${t.value===null?'#29343d':color(t.value,min,max)};--ink:${t.value!==null&&t.value>=(min+max)/2?'#10171c':'#fff'}"><div class="cell"><strong>${fmt(t.value)}</strong><small>${t.best?'★ Highest total':t.value===null?'Needs all 5 regions':'Sum of 5 regions'}</small></div></td>`).join('')}</tr></tfoot>`;
  }
  function resultsHTML(gs){const {min,max}=sharpnessRange(manifest);return `<section class="panel"><div class="bar spread"><h2>3 · Compare apertures</h2>${offline?'':`<div class="bar"><button id="export">Download offline report ZIP</button>${manifest.export_url?`<a class="button" href="${escape(manifest.export_url)}" download>Save latest ZIP</a>`:''}<label><input id="full-export" type="checkbox"> Include full aligned images</label><small>Full-image export requires consistent alignment across all five regions.</small></div>`}</div><p class="muted">Five regions, one selected capture per aperture. Select an aperture column to compare all five aligned regions.</p><div class="scroll"><table id="heatmap"><caption class="footnote">All five regions and apertures share the lowest-to-highest valid score range: purple = lowest, teal = middle, yellow = highest. Equal scores share the same color everywhere. The total row uses its own range. Colors show relative position, not significance. Values use the engine’s detail metric. ± is the repeat half-range, not a confidence interval.</caption><thead><tr><th scope="col">Region</th>${gs.map((g,i)=>`<th scope="col"><button class="aperture-column" data-column="${i}" aria-pressed="${i===apertureIndex}" aria-label="Select aperture f/${fmt(g.value)}">f/${fmt(g.value)}${g.flags.length?" ⚠":""}<small style="display:block">${escape(g.selectedCaptureId?g.captures.find(c=>c.id===g.selectedCaptureId)?.name||g.selectedCaptureId:"No valid capture")}</small><span class="column-selection">${i===apertureIndex?"Selected":"Select column"}</span></button></th>`).join('')}</tr></thead><tbody>${TABLE_REGIONS.map(r=>{const ms=gs.map(g=>measurement(g.captures.find(c=>c.id===g.selectedCaptureId),r)||(g.captures.some(c=>Object.keys(c.measurements||{}).length)?{status:"No valid capture",flags:[...g.flags,...new Set(g.captures.flatMap(c=>Object.values(c.measurements||{}).filter(m=>!valid(m)).map(m=>m.status)))]}:null));return `<tr><th scope="row">${LABELS[r]}</th>${ms.map((m,i)=>`<td class="heatmap-value ${i===apertureIndex?'selected-column':''}" data-column="${i}" style="--cell:${valid(m)?color(m.value,min,max):'#29343d'};--ink:${valid(m)&&m.value>=(min+max)/2?'#10171c':'#fff'}"><div class="cell" title="${escape([m?.status||'Not measured',...(m?.flags||[])].join(' · '))}"><strong>${valid(m)?fmt(m.value):'—'}</strong><small>${valid(m)?(Number.isFinite(m.uncertainty)?'± '+fmt(m.uncertainty):'repeat spread unavailable'):(m?.status||'Not measured')}</small>${m?.flags?.length?'<br><small>⚠ Review flags</small>':''}</div></td>`).join('')}</tr>`;}).join('')}</tbody>${totalsHTML()}</table></div><p class="footnote">Total = sum of all five valid region scores from the selected capture. Use as an overall guide; the individual regions use different target patterns.</p></section><section class="panel" id="comparison"><div class="bar spread"><h2>Aligned detail</h2><button id="download-composite" class="primary">Download 5-ROI ZIP</button></div><div class="bar"><button id="previous" aria-label="Previous aperture">←</button><select id="aperture-choice" aria-label="Aperture">${gs.map((g,i)=>`<option value="${i}" ${i===apertureIndex?'selected':''}>f/${fmt(g.value)}</option>`).join('')}</select><button id="next" aria-label="Next aperture">→</button><select id="repeat-choice" aria-label="Capture repeat">${gs[apertureIndex].captures.map(c=>`<option value="${escape(c.id)}" ${c.id===selected()?.id?'selected':''}>${escape(c.name||c.id)}${c.id===gs[apertureIndex].selectedCaptureId?' · selected whole capture':''}</option>`).join('')}</select><button id="choose-capture">Use this whole capture</button></div><p id="capture-flags" class="warning"></p><div class="bar"><button id="zoom-out" aria-label="Zoom out">−</button><output id="zoom-value">100%</output><button id="zoom-in" aria-label="Zoom in">+</button><button id="reset">1:1 · center</button><span class="muted">Drag to pan · wheel to zoom · ← → apertures · [ ] repeats · cached 5-ROI merge</span></div><p id="composite-status" class="footnote">Each aperture shows one merged image: four corner ROIs under the centered ROI.</p><p class="footnote">Alignment uses whole-pixel translation; small residual motion may remain.</p><div id="crops" class="crop-grid composite-grid"></div></section>`;}
  function compositeReady(capture){return COMPOSITE_REGIONS.every(r=>measurement(capture,r)?.crop?.url);}
  function compositeKey(capture){return compositeReady(capture)?COMPOSITE_REGIONS.map(r=>measurement(capture,r).crop.url).join('|'):'';}
  function compositeFileBase(capture,aperture){return `f-${String(aperture??'unknown').replace(/[^a-z0-9._-]+/gi,'-')}-${String(capture?.name||capture?.id||'capture').replace(/[^a-z0-9._-]+/gi,'-')}-5-roi-merge.png`;}
  async function loadImage(url){
    const image=new Image();
    image.decoding='async';
    image.src=url;
    if(image.decode)await image.decode();else await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;});
    return image;
  }
  const pngBlob=source=>new Promise((resolve,reject)=>source.toBlob(blob=>blob?resolve(blob):reject(Error('PNG export failed')),'image/png'));
  async function compositeBlob(capture){
    const images=Object.fromEntries(await Promise.all(COMPOSITE_REGIONS.map(async r=>[r,await loadImage(measurement(capture,r).crop.url)])));
    const sizes=Object.fromEntries(COMPOSITE_REGIONS.map(r=>[r,{width:images[r].naturalWidth||images[r].width,height:images[r].naturalHeight||images[r].height}]));
    const layout=compositeLayout(sizes),canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');
    canvas.width=layout.width;canvas.height=layout.height;ctx.fillStyle='#000';ctx.fillRect(0,0,canvas.width,canvas.height);
    for(const r of COMPOSITE_REGIONS){const p=layout.placements[r];ctx.drawImage(images[r],p.x,p.y);}
    const blob=await pngBlob(canvas);
    return {blob,width:canvas.width,height:canvas.height};
  }
  async function cachedComposite(capture){
    const key=compositeKey(capture);
    if(!key)throw Error('All five aligned crops are required before the merged image can be created.');
    if(compositeCache.has(key))return compositeCache.get(key);
    if(compositePending.has(key))return compositePending.get(key);
    const pending=compositeBlob(capture).then(result=>{
      const entry={...result,url:URL.createObjectURL(result.blob)};
      compositeCache.set(key,entry);
      return entry;
    }).finally(()=>compositePending.delete(key));
    compositePending.set(key,pending);
    return pending;
  }
  function prewarmComposites(){
    if(compositePrewarmRunning)return;
    compositePrewarmRunning=true;
    const gs=groups(manifest),ordered=[...gs.keys()].sort((a,b)=>Math.abs(a-apertureIndex)-Math.abs(b-apertureIndex));
    const run=async()=>{
      try{
        for(const i of ordered){
          const g=gs[i],capture=g?.captures.find(c=>c.id===g.selectedCaptureId)||g?.captures[0];
          if(compositeReady(capture)&&!compositeCache.has(compositeKey(capture)))await cachedComposite(capture);
        }
      }catch{}
      finally{compositePrewarmRunning=false;}
    };
    if(window.requestIdleCallback)window.requestIdleCallback(run);else window.setTimeout(run,0);
  }
  async function downloadCompositeZip(){
    const button=document.getElementById('download-composite'),status=document.getElementById('composite-status'),gs=groups(manifest);
    const entries=gs.map(g=>({group:g,capture:g.captures.find(c=>c.id===g.selectedCaptureId)||g.captures[0]})).filter(entry=>compositeReady(entry.capture));
    if(!entries.length){if(status)status.textContent='No apertures have all five aligned crops yet.';return;}
    if(button)button.disabled=true;if(status)status.textContent='Preparing cached merged images...';
    try{
      const files=await Promise.all(entries.map(async entry=>{
        const image=await cachedComposite(entry.capture);
        return {name:compositeFileBase(entry.capture,entry.group.value),data:new Uint8Array(await image.blob.arrayBuffer())};
      }));
      files.push({name:'README.txt',data:new TextEncoder().encode('TTC five-ROI merged aperture set\n\nEach PNG is one aperture/capture composite. The four corner ROIs form the base image; the center ROI is drawn last and centered over them.\n')});
      const link=document.createElement('a');link.href=URL.createObjectURL(zipStore(files));link.download='ttc-five-roi-merges.zip';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),30000);
      if(status)status.textContent=`ZIP is ready with ${entries.length} merged image${entries.length===1?'':'s'}.`;
    }catch(e){if(status)status.textContent='Could not create merged-image ZIP: '+(e.message||String(e));}
    finally{if(button)button.disabled=false;}
  }
  function attachViewportGestures(container){container.querySelectorAll('.viewport').forEach(el=>{el.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.125,Math.min(8,zoom*(e.deltaY<0?1.25:.8)));transform();},{passive:false});el.addEventListener('pointerdown',e=>{el.setPointerCapture(e.pointerId);let x=e.clientX,y=e.clientY;const move=e=>{pan.x+=(e.clientX-x)/zoom;pan.y+=(e.clientY-y)/zoom;x=e.clientX;y=e.clientY;transform();};el.addEventListener('pointermove',move);el.addEventListener('pointerup',()=>el.removeEventListener('pointermove',move),{once:true});el.addEventListener('pointercancel',()=>el.removeEventListener('pointermove',move),{once:true});});});}
  function renderCrops(){
    const container=document.getElementById('crops');if(!container)return;
    const c=selected(),flags=document.getElementById('capture-flags'),status=document.getElementById('composite-status'),button=document.getElementById('download-composite');
    if(flags)flags.textContent=[...(groups(manifest)[apertureIndex]?.flags||[]),...(c?.flags||[])].join(' · ');
    if(button)button.disabled=!groups(manifest).some(g=>compositeReady(g.captures.find(c=>c.id===g.selectedCaptureId)||g.captures[0]));
    const key=compositeKey(c),cached=key&&compositeCache.get(key),ticket=String(++compositeRenderToken);container.dataset.ticket=ticket;
    const imageHTML=entry=>`<article class="crop-card composite-card"><div class="crop-title"><strong>5-ROI merge</strong><a href="${escape(entry.url)}" download="${escape(compositeFileBase(c,groups(manifest)[apertureIndex]?.value))}">Save image</a></div><div class="viewport composite-view" tabindex="0" aria-label="Five ROI merged crop, shared zoom and pan"><img src="${escape(entry.url)}" alt="Five ROI merge for ${escape(c?.name||c?.id)}" width="${Number(entry.width)}" height="${Number(entry.height)}"></div><small>${escape(c?.name||c?.id||'Selected capture')}</small></article>`;
    if(cached){container.innerHTML=imageHTML(cached);if(status)status.textContent='Cached merged image.';attachViewportGestures(container);transform();prewarmComposites();return;}
    container.innerHTML=`<article class="crop-card composite-card"><div class="viewport composite-view"><div class="empty">${compositeReady(c)?'Building merged image once...':'No complete 5-ROI merge available for this capture'}</div></div></article>`;
    attachViewportGestures(container);transform();
    if(!compositeReady(c)){if(status)status.textContent='Select a measured capture with all five aligned crops first.';return;}
    if(status)status.textContent=compositePending.has(key)?'Finishing cached merged image...':'Building merged image once; flips are cached after this.';
    cachedComposite(c).then(entry=>{if(container.dataset.ticket!==ticket)return;container.innerHTML=imageHTML(entry);attachViewportGestures(container);transform();if(status)status.textContent='Cached merged image.';prewarmComposites();}).catch(e=>{if(status)status.textContent='Could not build merged image: '+(e.message||String(e));});
  }
  function transform(){document.querySelectorAll('.viewport img').forEach(el=>el.style.transform=`translate(-50%,-50%) scale(${zoom}) translate(${pan.x}px,${pan.y}px)`);const out=document.getElementById('zoom-value');if(out)out.textContent=Math.round(zoom*100)+'%';}
  function changeAperture(delta){apertureIndex=(apertureIndex+delta+groups(manifest).length)%groups(manifest).length;repeatId=null;render();}
  function bind(){root.querySelectorAll('[data-aperture],[data-roi-id],#tracking-radius').forEach(el=>el.addEventListener('input',markConfigDirty));const on=(id,event,fn)=>document.getElementById(id)?.addEventListener(event,fn);root.querySelector('details')?.addEventListener('toggle',e=>{setupOpen=e.target.open;});on('manual-rois','click',()=>{manifest.rois=manualRois(manifest.width,manifest.height);manualDraft=true;setupOpen=true;render();});on('quit','click',async()=>{try{await request('shutdown',{});clearInterval(polling);document.getElementById('message').textContent='Local service stopped. You can close this tab.';}catch(e){error(e);}});on('browse','click',browseFolders);on('import','click',()=>action('import',{directory:document.getElementById('folder').value}));on('import-auto','click',()=>action('import',{directory:document.getElementById('folder').value,autoRun:true}));on('automatic','click',()=>action('automatic',{}));on('run','click',()=>action('run',{}));on('cancel','click',()=>action('cancel',{}));on('save-config','click',()=>{const captures=manifest.captures.map(c=>({id:c.id,aperture:(v=>v===''?null:Number(v))([...document.querySelectorAll('[data-aperture]')].find(e=>e.dataset.aperture===c.id).value)}));const rois=readRois();const trackValue=document.getElementById('tracking-radius')?.value;action('config',{captures,rois,track:trackValue?Number(trackValue):null});});on('detect','click',()=>action('detect',{}));on('export','click',()=>action('export',{full_resolution:document.getElementById('full-export').checked}));document.querySelectorAll('[data-column]').forEach(el=>el.onclick=()=>{apertureIndex=Number(el.dataset.column);repeatId=null;render();});on('region-choice','change',e=>{region=e.target.value;renderCrops();});on('previous','click',()=>changeAperture(-1));on('next','click',()=>changeAperture(1));on('aperture-choice','change',e=>{apertureIndex=Number(e.target.value);repeatId=null;render();});on('repeat-choice','change',e=>{repeatId=e.target.value;render();});on('choose-capture','click',()=>{const g=groups(manifest)[apertureIndex],id=selected().id;if(offline){manifest.apertures=groups(manifest).map(a=>({value:a.value,selectedCaptureId:a.value===g.value?id:a.selectedCaptureId,flags:a.flags}));render();document.getElementById('message').textContent='Whole-capture override applies to this viewing session.';}else action('select',{aperture:g.value,captureId:id});});on('focus','change',e=>{focused=e.target.checked;render();});on('zoom-in','click',()=>{zoom=Math.min(8,zoom*1.25);transform();});on('zoom-out','click',()=>{zoom=Math.max(.125,zoom*.8);transform();});on('reset','click',()=>{zoom=1;pan={x:0,y:0};transform();});bindRois();}
  function readRois(){return (manifest.rois||[]).map(r=>{const copy={...r};document.querySelectorAll('[data-roi-id]').forEach(el=>{if(el.dataset.roiId===r.id)copy[el.dataset.field]=Number(el.value);});return copy;});}
  function syncRoiOverlay(){
    const p=manifest.preview;
    if(p)for(const r of readRois()){
      const box=[...root.querySelectorAll('[data-roi]')].find(el=>el.dataset.roi===r.id);
      if(box)for(const field of ['x','y','width','height'])box.style[{x:'left',y:'top',width:'width',height:'height'}[field]]=100*r[field]/(['x','width'].includes(field)?p.width:p.height)+'%';
    }
    const undo=document.getElementById('roi-undo');if(undo)undo.disabled=!roiHistory||roiHistory.steps.length<2||manifest.job?.status==='running';
    const reset=document.getElementById('roi-reset');if(reset)reset.disabled=!roiHistory||JSON.stringify(readRois())===JSON.stringify(roiHistory.baseline)||manifest.job?.status==='running';
  }
  function applyRois(rois){
    for(const input of root.querySelectorAll('[data-roi-id]')){const r=rois.find(r=>r.id===input.dataset.roiId);if(r)input.value=r[input.dataset.field];}
    markConfigDirty();syncRoiOverlay();
  }
  function zoomRois(value){
    const scroller=root.querySelector('.roi-scroller'),preview=root.querySelector('.roi-preview');if(!scroller||!preview)return;
    const x=(scroller.scrollLeft+scroller.clientWidth/2)/preview.clientWidth,y=(scroller.scrollTop+scroller.clientHeight/2)/preview.clientHeight;
    roiZoom=Math.max(1,Math.min(8,value));preview.style.width=roiZoom*100+'%';
    scroller.scrollLeft=x*preview.clientWidth-scroller.clientWidth/2;scroller.scrollTop=y*preview.clientHeight-scroller.clientHeight/2;
    document.getElementById('roi-zoom-value').textContent=Math.round(roiZoom*100)+'%';
  }
  function bindRois(){
    const on=(id,fn)=>document.getElementById(id)?.addEventListener('click',fn);
    on('roi-undo',()=>applyRois(roiHistory.undo()));on('roi-reset',()=>applyRois(roiHistory.reset()));
    on('roi-zoom-in',()=>zoomRois(roiZoom*1.5));on('roi-zoom-out',()=>zoomRois(roiZoom/1.5));on('roi-fit',()=>zoomRois(1));
    root.querySelectorAll('[data-roi-id]').forEach(input=>{
      input.addEventListener('input',()=>{roiHistory.push(readRois());syncRoiOverlay();});
    });
    document.querySelectorAll('.roi-box').forEach(el=>el.onpointerdown=e=>{
      if(requestPending||manifest.job?.status==='running')return;
      e.preventDefault();el.setPointerCapture(e.pointerId);
      const r=readRois().find(r=>r.id===el.dataset.roi),bounds=el.parentElement.getBoundingClientRect(),p=manifest.preview,x=e.clientX,y=e.clientY;
      const move=e=>{
        const nx=Math.round(Math.max(0,Math.min(p.width-r.width,r.x+(e.clientX-x)*p.width/bounds.width))),ny=Math.round(Math.max(0,Math.min(p.height-r.height,r.y+(e.clientY-y)*p.height/bounds.height)));
        document.querySelectorAll('[data-roi-id]').forEach(input=>{if(input.dataset.roiId===r.id&&['x','y'].includes(input.dataset.field))input.value=input.dataset.field==='x'?nx:ny;});
        markConfigDirty();syncRoiOverlay();
      };
      const end=()=>{el.removeEventListener('pointermove',move);el.removeEventListener('pointerup',end);el.removeEventListener('pointercancel',end);roiHistory.push(readRois());syncRoiOverlay();};
      el.addEventListener('pointermove',move);el.addEventListener('pointerup',end);el.addEventListener('pointercancel',end);
    });
  }
  document.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]')||/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)||e.ctrlKey||e.metaKey||e.altKey||!groups(manifest).length)return;if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();changeAperture(e.key==='ArrowLeft'?-1:1);}if(['[',']'].includes(e.key)){const cs=groups(manifest)[apertureIndex].captures;const i=cs.findIndex(c=>c.id===selected().id);repeatId=cs[(i+(e.key==='['?-1:1)+cs.length)%cs.length].id;render();}});
  if(embedded){offline=true;manifest=normalize(embedded);document.getElementById('mode').textContent='Offline report';render();}
  else{render();request('session').then(async session=>{token=session.token;jobId=new URLSearchParams(window.location.search).get('job')||sessionStorage.getItem('ttc-job');let snapshot;try{snapshot=await request(jobId?'jobs/'+encodeURIComponent(jobId):'state');}catch{sessionStorage.removeItem('ttc-job');snapshot=await request('state');}if(snapshot)accept(snapshot);}).catch(()=>error('Local engine unavailable. Start the TTC local app to open images.'));polling=setInterval(async()=>{if(manifest.job?.status!=='running'||!jobId)return;try{accept(await request('jobs/'+encodeURIComponent(jobId)));}catch(e){error(e);}},1500);}
})();
