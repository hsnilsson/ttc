// Verify a generated, extracted offline report without a browser or server.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const dir=path.resolve(process.argv[2]||'');
const page=fs.readFileSync(path.join(dir,'report.html'),'utf8');
const embedded=page.match(/<script id="ttc-manifest" type="application\/json">([\s\S]*?)<\/script>/);
assert.ok(embedded,'Report must embed its manifest, without a file:// fetch');
const manifest=JSON.parse(embedded[1]);
assert.deepEqual(manifest,JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'),'utf8')));
assert.ok(!/[A-Z]:[\\/]/i.test(JSON.stringify(manifest)),'No local absolute source paths');
assert.ok(!/https?:\/\//i.test(JSON.stringify(manifest)),'No remote assets');
for(const asset of ['viewer.js','viewer.css'])assert.ok(fs.existsSync(path.join(dir,asset)),asset);
let crops=0;
for(const frame of manifest.frames)for(const region of frame.regions){
 if(!region.crop_url)continue;
 assert.ok(region.crop_url.startsWith('assets/'),'Portable crop asset');
 const file=path.resolve(dir,region.crop_url);assert.ok(file.startsWith(dir+path.sep));
 const data=fs.readFileSync(file);
 assert.equal(data.subarray(1,4).toString(),'PNG');
 assert.equal(data.readUInt32BE(16),region.width,'Native crop width');
 assert.equal(data.readUInt32BE(20),region.height,'Native crop height');
 crops++;
}
console.log(JSON.stringify({frames:manifest.frames.length,apertures:manifest.groups.length,crops,portable:true}));
