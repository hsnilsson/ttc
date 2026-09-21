// Serve only an extracted generated report directory for local browser QA.
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
if(!process.argv[2])throw Error('Usage: node web/tests/serve-report.cjs EXTRACTED_REPORT_DIR');
const base=fs.realpathSync(process.argv[2]);
http.createServer((req,res)=>{
 try{
  const name=decodeURIComponent(req.url.split('?')[0]);
  const file=fs.realpathSync(path.resolve(base,'.'+(name==='/'?'/report.html':name)));
  if(!file.startsWith(base+path.sep))throw Error('Outside report');
  const types={'.html':'text/html','.css':'text/css','.js':'text/javascript','.png':'image/png','.json':'application/json'};
  const type=types[path.extname(file)];if(!type)throw Error('Not a report asset');
  res.setHeader('Content-Type',type);fs.createReadStream(file).pipe(res);
 }catch{res.writeHead(404);res.end('Not found');}
}).listen(8767,'127.0.0.1',()=>console.log('Report QA http://127.0.0.1:8767'));
