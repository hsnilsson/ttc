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
