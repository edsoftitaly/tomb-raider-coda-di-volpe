const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const pg=await b.newPage({viewport:{width:1280,height:720}});
const http=require('http'),fs=require('fs'),path=require('path');
const srv=http.createServer((q,s)=>{const f=path.join(__dirname,q.url.split('?')[0]);const t={'.js':'text/javascript','.html':'text/html','.png':'image/png','.json':'application/json'}[path.extname(f)]||'application/octet-stream';fs.readFile(f,(e,d)=>{if(e){s.writeHead(404);s.end();}else{s.writeHead(200,{'Content-Type':t});s.end(d);}});}).listen(8765);
pg.on('console',m=>console.log('page:',m.text()));pg.on('pageerror',e=>console.log('err:',e.message));
await pg.goto('http://localhost:8765/index.html');await pg.waitForFunction('window.ready===true',null,{timeout:120000});
const V=JSON.parse(process.argv[2]);
for(const [name,v] of Object.entries(V)){await pg.evaluate(v=>window.view(...v),v);await pg.screenshot({path:name+'.png'});console.log('saved',name);}
await b.close();srv.close();})();
