// استعمال: node source/tools/shoot_cards.js [id ...]  (الصور في images/<id>/)
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const R='/home/claude/tajalliyat/';const b=await chromium.launch();const errs=[];
const p=await b.newPage({viewport:{width:1080,height:1350}});p.on('pageerror',e=>errs.push(e.message));
const only=process.argv.slice(2);fs.writeFileSync(R+'source/tools/_products.js','window.PROD='+fs.readFileSync(R+'products/products.json','utf8')+';');const ids=only.length?only:Object.keys(JSON.parse(fs.readFileSync(R+'products/products.json','utf8')));
for(const id of ids){fs.mkdirSync(R+'images/'+id,{recursive:true});
 for(const s of ['0','1','2','3','4','w']){const h=s==='w'?1920:1350;await p.setViewportSize({width:1080,height:h});
  await p.goto(`file://${R}source/tools/card.html?n=${id}&s=${s}`);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(150);
  const of=await p.evaluate(()=>{const c=document.querySelector('.c');return c.scrollHeight>c.clientHeight+2});if(of)errs.push('overflow '+id+' '+s);
  await p.screenshot({path:R+`images/${id}/${s==='w'?'wallpaper':'slide-'+(+s+1)}.jpg`,type:'jpeg',quality:86});}}
console.log('errors',errs);await b.close();})();
