const {chromium}=require('playwright');const fs=require('fs');
const R='/home/claude/tajalliyat/';const list=JSON.parse(fs.readFileSync(R+'og_list.json'));
const only=process.argv[2];
const css=`@font-face{font-family:Kufi;src:url(file://${R}assets/fonts/reem-kufi-arabic-700-normal.woff2);font-weight:700}
@font-face{font-family:Naskh;src:url(file://${R}assets/fonts/noto-naskh-arabic-arabic-600-normal.woff2);font-weight:600}
@font-face{font-family:Plex;src:url(file://${R}assets/fonts/ibm-plex-sans-arabic-arabic-500-normal.woff2);font-weight:500}
*{margin:0;box-sizing:border-box}body{width:1200px;height:630px;background:#0E1324;color:#E9E6DD;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;position:relative;direction:rtl}
.f{position:absolute;inset:24px;border:2px solid #E3B45C;opacity:.35;border-radius:8px}.f:after{content:"";position:absolute;inset:8px;border:1px solid #E3B45C;border-radius:5px}
.k{font:500 30px Plex;opacity:.75;letter-spacing:.04em;margin-bottom:18px}.n{font:700 170px/1.5 Kufi;color:#E3B45C;margin-top:0}.t{font:600 40px/1.6 Naskh;max-width:960px}.u{position:absolute;bottom:44px;font:500 24px Plex;opacity:.5}
svg{width:70px;height:70px;color:#E3B45C;margin-bottom:6px}`;
fs.writeFileSync('/dev/null','');const star='<svg viewBox="0 0 64 64"><g fill="none" stroke="currentColor" stroke-width="2.2"><rect x="14" y="14" width="36" height="36"/><rect x="14" y="14" width="36" height="36" transform="rotate(45 32 32)"/></g></svg>';
const page=(name,tag,kick)=>`<!doctype html><meta charset=utf-8><style>${css}</style><body><div class=f></div>${star}<div class=k>${kick}</div><div class=n>${name}</div><div class=t>${tag}</div><div class=u>oaelhag.github.io/tajalliyat</div>`;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:630}});
fs.mkdirSync(R+'og',{recursive:true});fs.mkdirSync(R+'pdf',{recursive:true});
if(!only||only==='og'){
 const all=[...list,{id:'default',name:'تجليات الأسماء',tagline:'عِش أسماء الله الحسنى في يومك: معنى وتأمل وتجلٍّ لكل اسم',kick:'أسماء الله الحسنى'}];
 for(const n of all){fs.writeFileSync(R+'og/_t.html',page(n.name,n.tagline,n.kick||'تجليات الأسماء · اسم من أسماء الله الحسنى'));await p.goto('file://'+R+'og/_t.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(80);
  await p.screenshot({path:R+`og/${n.id}.jpg`,type:'jpeg',quality:84});}
 fs.unlinkSync(R+'og/_t.html');console.log('og done');}
if(!only||only==='pdf'){
 const pp=await b.newPage();let bad=[];
 for(const n of list){for(const g of ['boy','girl','youngman','youngwoman','father','mother']){
  await pp.goto(`file://${R}print/${n.id}-${g}.html`);await pp.evaluate(()=>document.fonts.ready);
  const f=`${R}pdf/${n.id}-${g}.pdf`;await pp.pdf({path:f,format:'A4',printBackground:true,preferCSSPageSize:true});
  const txt=fs.readFileSync(f,'latin1');const pages=(txt.match(/\/Type\s*\/Page[^s]/g)||[]).length;if(pages!==4)bad.push(n.id+'-'+g+':'+pages);}}
 console.log('pdf done; not 4 pages:',bad.join(' ')||'none');}
await b.close();})();
