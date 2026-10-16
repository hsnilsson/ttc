const {test}=require('node:test');
const assert=require('node:assert/strict');
const {normalize,starRows}=require('../viewer.js');
test('star results preserve whole capture choice and expose missing repeats',()=>{
  const edge=(value)=>({id:'inset_tl',edges:[{direction:'horizontal detail',status:'accepted',mtf50:value}]});
  const data=normalize({frames:[{id:'a',aperture:4,star_mtf:[edge(.1)]},{id:'b',aperture:4,star_mtf:[edge(.2)]}],groups:[{aperture:4,selected_frame_id:'a'}]});
  const rows=starRows(data);
  assert.equal(rows[0].cells[0].value,.1);
  assert.equal(rows[0].cells[0].halfRange,.05);
  assert.match(rows[0].cells[0].flags.join(),/exceeds/);
  assert.equal(rows[1].cells[0].value,null);
  assert.match(rows[1].cells[0].flags.join(),/no valid/);
});
test('rejected star MTF is never displayed as valid or substituted by gradient',()=>{
  const data={captures:[{id:'a',aperture:4,measurements:{tl:{value:.9}},star_mtf:[{id:'outer_tl',edges:[{direction:'vertical detail',status:'rejected',mtf50:.3,reason:'Neighbour'}]}]}]};
  const rows=starRows(data);
  assert.equal(rows[1].cells[0].value,null);
  assert.equal(rows[1].cells[0].reason,'Neighbour');
});
const {starCurveSeries,starConfidence,starCurveSVG}=require('../viewer.js');
const measured=(id,aperture,value,extra={})=>({id,aperture,star_mtf:[{id:'inset_tl',edges:[{direction:'horizontal detail',status:'accepted',mtf50:value,crop_spread:.02,sfr:[1,.5,.01],frequencies:[0,value,.5],...extra}]}]});
test('curves overlay every accepted repeat while retaining whole capture selection',()=>{
  const data={captures:[measured('a',4,.1),measured('b',4,.102),measured('c',5.6,.12)],apertures:[{value:4,selectedCaptureId:'b'}]};
  const series=starCurveSeries(data,'inset_tl','horizontal detail');
  assert.equal(series.length,3);
  assert.equal(series[0].color,series[1].color);
  assert.notEqual(series[0].color,series[2].color);
  assert.equal(series[1].selected,true);
  const svg=starCurveSVG(series,'Top left <test>');
  assert.equal((svg.match(/<polyline/g)||[]).length,3);
  assert.equal((svg.match(/<circle/g)||[]).length,3);
  assert.match(svg,/stroke-dasharray="7 5"/);
  assert.match(svg,/50%/);
  assert.match(svg,/cycles per output pixel/);
  assert.match(svg,/&lt;test&gt;/);
});
test('invalid and rejected curves never become a displayed measurement',()=>{
  const data={captures:[measured('a',4,.1,{status:'rejected'}),measured('b',4,.1,{sfr:[1,NaN,0]}),measured('c',5,.1,{frequencies:[0,.5,.1]}),measured('d',5,.1,{frequencies:[0,.1]})]};
  assert.deepEqual(starCurveSeries(data,'inset_tl','horizontal detail'),[]);
  assert.match(starCurveSVG([],'missing'),/not zero sharpness/);
});
test('confidence distinguishes repeat agreement, missing repeats and unavailable crop checks',()=>{
  const captures=[measured('a',4,.1),measured('b',4,.102)];
  let evidence=starConfidence(captures,'inset_tl','horizontal detail');
  assert.equal(evidence.label,'Repeats agree within 10%');
  assert.ok(evidence.repeatSpread>.019&&evidence.repeatSpread<.020);
  assert.equal(evidence.cropSpread,.02);
  assert.equal(starConfidence(captures.slice(0,1),'inset_tl','horizontal detail').label,'Single capture only');
  evidence=starConfidence([...captures,{id:'missing'}],'inset_tl','horizontal detail');
  assert.equal(evidence.label,'Incomplete repeats');
  assert.equal(evidence.accepted,2);
  assert.equal(evidence.total,3);
  assert.equal(starConfidence([measured('a',4,.1),measured('b',4,.2)],'inset_tl','horizontal detail').label,'Repeats disagree');
  assert.equal(starConfidence([{id:'missing'}],'inset_tl','horizontal detail').cropSpread,null);
});
const {starSupport,starSupportHTML,starTrackingHTML}=require('../viewer.js');
test('supporting edges report agreement without replacing a failed primary',()=>{
  const edge={status:'accepted',mtf50:.1,supporting_edges:[{status:'accepted',mtf50:.13},{status:'rejected',mtf50:.11},{status:'accepted',mtf50:.102}]};
  const support=starSupport(edge);
  assert.equal(support.accepted,2);
  assert.equal(support.total,3);
  assert.ok(Math.abs(support.difference-.3)<1e-12);
  assert.equal(support.caution,true);
  assert.match(starSupportHTML(edge),/Caution: exceeds 20%/);
  assert.match(starSupportHTML(edge),/still use the primary edge/);
  edge.status='rejected';
  assert.equal(starSupport(edge).difference,null);
  assert.equal(starSupport(edge).caution,false);
  assert.match(starSupportHTML(edge),/do not replace a rejected primary/);
  assert.match(starSupportHTML({}),/unavailable/);
});
test('context tracking reports measured evidence and escapes untrusted status',()=>{
  const html=starTrackingHTML({status:'<rejected>',shift:[1.25,-2],inliers:42,coverage:.25,residual_p90:.8,anchor:true});
  assert.match(html,/&lt;rejected&gt;/);
  assert.match(html,/25%/);
  assert.match(html,/0.8 pixels/);
  assert.match(html,/alignment reference capture/);
  assert.match(html,/alignment, not sharpness/);
  assert.match(starTrackingHTML(),/unavailable/);
});
const {starLabel,starOverviewHTML}=require('../viewer.js');
test('overview uses first-capture coordinates and describes attempted center coverage honestly',()=>{
  const data={preview:{url:'reference.png',width:1000,height:800},captures:[{id:'first',star_mtf:[{id:'center_small',source_box:[400,300,100,150]}]},{id:'second',star_mtf:[{id:'center_small',source_box:[444,333,100,150]}]}]};
  assert.equal(starLabel('center_small'),'Center test block');
  const html=starOverviewHTML(data);
  assert.match(html,/x="400" y="300" width="100" height="150"/);
  assert.doesNotMatch(html,/x="444"/);
  assert.match(html,/marked area does not mean a measurement passed/);
  assert.match(html,/center coverage is not assumed/);
  assert.match(html,/four tiny stars and the larger pinwheel/);
  assert.equal(starOverviewHTML({...data,preview:null}),'');
});
const {starCoverage,PRIMARY_STAR_IDS}=require('../viewer.js');
test('primary coverage includes center, requires both directions and never substitutes inset results',()=>{
  assert.deepEqual(PRIMARY_STAR_IDS,['outer_tl','outer_tr','center_small','outer_bl','outer_br']);
  const star=id=>({id,edges:['horizontal detail','vertical detail'].map(direction=>({direction,status:'accepted',mtf50:.1}))});
  const capture={star_mtf:['outer_tl','outer_tr','outer_bl','outer_br','inset_tl'].map(star)};
  assert.equal(starCoverage(capture).accepted,4);
  assert.equal(starCoverage(capture).total,5);
  capture.star_mtf.push(star('center_small'));
  assert.equal(starCoverage(capture).accepted,5);
  capture.star_mtf[0].edges[1].status='rejected';
  assert.equal(starCoverage(capture).accepted,4);
  assert.equal(starCoverage(null).accepted,0);
});
const {starDirectionLabel}=require('../viewer.js');
test('pinwheel directions are explicitly oblique, never labelled horizontal or vertical',()=>{
  assert.equal(starDirectionLabel({method:'pinwheel-oblique-edge',detail_angle_degrees:30.12},'horizontal detail'),'Oblique detail · 30.1° from image horizontal');
  assert.equal(starDirectionLabel({method:'pinwheel-oblique-edge',detail_angle_degrees:119.9},'vertical detail'),'Oblique detail · 119.9° from image horizontal');
  assert.equal(starDirectionLabel({},'horizontal detail'),'horizontal detail');
});
const {starPlotLimit,starApertureSummary}=require('../viewer.js');
test('aperture summaries preserve selected captures and flag overlapping repeat ranges',()=>{
 const make=(id,aperture,value)=>({id,aperture,star_mtf:[{id:'outer_tl',edges:[{direction:'horizontal detail',status:'accepted',mtf50:value,crop_spread:.01}]}]});
 const data={captures:[make('a',4,.1),make('b',4,.102),make('c',5.6,.103),make('d',5.6,.101)],apertures:[{value:4,selectedCaptureId:'a'},{value:5.6,selectedCaptureId:'c'}]};
 let summary=starApertureSummary(data,'outer_tl','horizontal detail');
 assert.equal(summary.best,5.6);assert.deepEqual(summary.similar,[4,5.6]);assert.equal(summary.provisional,false);
 data.apertures[1].selectedCaptureId='missing';
 summary=starApertureSummary(data,'outer_tl','horizontal detail');assert.equal(summary.best,4);assert.equal(summary.provisional,true);
 data.captures=[];assert.match(starApertureSummary(data,'outer_tl','horizontal detail').text,/No accepted/);
});
test('useful plot range includes every region, repeat and high-frequency rebound',()=>{
 const data={captures:[{id:'a',aperture:4,star_mtf:[{id:'center_small',edges:[{direction:'horizontal detail',status:'accepted',mtf50:.08,frequencies:[0,.1,.2,.3,.4,.5],sfr:[1,.4,.09,.01,.02,0]}]}]}]};
 assert.equal(starPlotLimit(data),.2);
 data.captures[0].star_mtf[0].edges[0].sfr[4]=.15;assert.equal(starPlotLimit(data),.5);
 data.captures[0].star_mtf[0].edges[0].status='rejected';assert.equal(starPlotLimit(data),.1);
});
