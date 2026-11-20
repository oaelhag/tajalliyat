(()=>{'use strict';
const B=document.body,BOOK=B.dataset.book; if(!BOOK) return;
const KEY='tajalli_book_'+BOOK+'_v1',$=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
let S={notes:{},done:{},read:{},last:'',fs:1,theme:''};
try{Object.assign(S,JSON.parse(localStorage.getItem(KEY)||'{}'))}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}};
const root=document.documentElement;
function applyPrefs(){root.style.setProperty('--fs',S.fs||1);if(S.theme)root.setAttribute('data-theme',S.theme);else root.removeAttribute('data-theme');
 $$('#settings [data-theme]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.theme===S.theme)))}
applyPrefs();
const arts=$$('.art'),chapters=arts.filter(a=>/^c\d+$/.test(a.id)),order=arts.filter(a=>a.id!=='notes').map(a=>a.id).concat(['notes']);
const toc=$('#toc'),scrim=$('#scrim'),setp=$('#settings');
function openToc(o){toc.hidden=!o;scrim.hidden=!o;$('#tocBtn').setAttribute('aria-expanded',o);if(o){setp.hidden=true;const on=$('.tocrow.on');on&&on.scrollIntoView({block:'center'})}}
$('#tocBtn').onclick=()=>openToc(toc.hidden);$('#tocClose').onclick=()=>openToc(false);scrim.onclick=()=>{openToc(false);setp.hidden=true};
$('#setBtn').onclick=()=>{setp.hidden=!setp.hidden;$('#setBtn').setAttribute('aria-expanded',!setp.hidden);if(!setp.hidden)openToc(false)};
$('#fsUp').onclick=()=>{S.fs=Math.min(1.5,+((S.fs||1)+.1).toFixed(2));applyPrefs();save()};
$('#fsDown').onclick=()=>{S.fs=Math.max(.85,+((S.fs||1)-.1).toFixed(2));applyPrefs();save()};
$$('#settings [data-theme]').forEach(b=>b.onclick=()=>{S.theme=(S.theme===b.dataset.theme?'':b.dataset.theme);applyPrefs();save()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){openToc(false);setp.hidden=true}});
/* حالة التوثيق */
function mark(){$$('.tocrow[data-go]').forEach(a=>a.classList.toggle('read',!!S.read[a.dataset.go]));
 const n=chapters.filter(c=>S.read[c.id]).length;$('#progTxt').textContent=n?`أتممتَ ${n.toLocaleString('ar')} من ${chapters.length.toLocaleString('ar')} فصلاً`:'لم تُتمّ فصلاً بعد. يُحفظ تقدمك على هذا الجهاز فقط.';
 $('#progBar').style.width=(chapters.length?100*n/chapters.length:0)+'%'}
/* عرض صفحة */
let cur=null;
function show(id,anchor){let el=document.getElementById(id);if(!el){id='front';el=document.getElementById('front')}
 const art=el.classList.contains('art')?el:el.closest('.art');if(!art)return;
 if(cur!==art){arts.forEach(a=>a.hidden=a!==art);cur=art;if(art.id==='notes')renderNotes();pager(art);document.title=art.dataset.title+' | '+B.dataset.title+' | تجليات الأسماء';
  if(art.id!=='notes'){S.last=art.id;save()}
  $$('.tocrow.on').forEach(x=>x.classList.remove('on'));const r=$(`.tocrow[data-go="${art.id}"]`);r&&r.classList.add('on');
  $$('.tch').forEach(t=>t.classList.toggle('open',!!t.querySelector(`.tocrow[data-go="${art.id}"]`)))}
 if(el!==art){requestAnimationFrame(()=>el.scrollIntoView({block:'start'}))}else window.scrollTo(0,0);
 openToc(false);setp.hidden=true}
function pager(art){const i=order.indexOf(art.id),pn=$('#pn');pn.innerHTML='';
 if(/^c\d+$/.test(art.id)){const b=document.createElement('div');b.className='readbtn';b.style.width='100%';const btn=document.createElement('button');
  const set=()=>{btn.textContent=S.read[art.id]?'✓ أتممتُ هذا الفصل (اضغط للتراجع)':'أتممتُ هذا الفصل';btn.setAttribute('aria-pressed',!!S.read[art.id])};
  btn.className='btn';set();btn.onclick=()=>{S.read[art.id]=!S.read[art.id];save();set();mark()};b.appendChild(btn);pn.appendChild(b)}
 const mk=(id,pre)=>{const t=id==='notes'?'ملاحظاتي':(document.getElementById(id).dataset.title);const a=document.createElement('a');a.className='btn';a.href='#'+id;a.textContent=pre+t;return a};
 if(i<order.length-1)pn.appendChild(mk(order[i+1],'التالي: '));if(i>0)pn.appendChild(mk(order[i-1],'السابق: '))}
function route(){const h=decodeURIComponent(location.hash.slice(1));show(h||S.last||'front')}
window.addEventListener('hashchange',route);
/* الملاحظات والمهام */
$$('textarea[data-note]').forEach(t=>{t.value=S.notes[t.dataset.note]||'';let to;t.addEventListener('input',()=>{clearTimeout(to);to=setTimeout(()=>{if(t.value.trim())S.notes[t.dataset.note]=t.value;else delete S.notes[t.dataset.note];save()},300)})});
$$('input[data-task]').forEach(c=>{c.checked=!!S.done[c.dataset.task];c.onchange=()=>{if(c.checked)S.done[c.dataset.task]=1;else delete S.done[c.dataset.task];save()}});
function renderNotes(){const n=$('#notes'),keys=Object.keys(S.notes);const ql={};$$('textarea[data-note]').forEach(t=>ql[t.dataset.note]=[t.dataset.name,t.dataset.q]);
 let h='<header class="chead plain"><div><p class="kicker">على جهازك فقط</p><h1>ملاحظاتي</h1></div></header>';
 const dn=Object.keys(S.done).length;h+=`<p class="lead">مهام أنجزتَها: ${dn.toLocaleString('ar')}. ملاحظات مكتوبة: ${keys.length.toLocaleString('ar')}. لا يُرسل شيء إلى أي خادم؛ إن مسحت بيانات المتصفح أو غيّرت جهازك فلن تجدها، فنزّل نسخة منها.</p>`;
 if(keys.length){h+='<p class="row"><button class="btn main" id="exp">تنزيل ملاحظاتي (نص)</button><button class="btn quiet" id="clr">مسح كل ملاحظاتي</button></p>';
  const dom=$$('textarea[data-note]').map(t=>t.dataset.note);keys.sort((a,b)=>dom.indexOf(a)-dom.indexOf(b)).forEach(k=>{const [nm,q]=ql[k]||['',''];h+=`<div class="box note"><h3>${esc(nm)}</h3><p><b>${esc(q)}</b></p><p>${esc(S.notes[k]).replace(/\n/g,'<br>')}</p><p><a href="#n-${k.split('-')[0]}">اذهب إلى الاسم</a></p></div>`})}
 else h+='<p class="note">لا ملاحظات بعد. في آخر كل اسم قسم «دوّن أثرك» تكتب فيه.</p>';
 n.innerHTML=h;const e=$('#exp');if(e)e.onclick=()=>{const t=Object.keys(S.notes).map(k=>{const [nm,q]=ql[k]||['',''];return `${nm}\n${q}\n${S.notes[k]}\n`}).join('\n----\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([t],{type:'text/plain;charset=utf-8'}));a.download='ملاحظاتي-'+BOOK+'.txt';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000)};
 const c=$('#clr');if(c){c.onclick=()=>{if(c.dataset.sure){S.notes={};save();$$('textarea[data-note]').forEach(t=>t.value='');renderNotes()}else{c.dataset.sure=1;c.textContent='اضغط مرة أخرى للتأكيد'}}}}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
/* البحث */
const norm=s=>s.replace(/[ً-ٰٟۖ-ۭـ]/g,'').replace(/[أإآٱ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه').replace(/[ؤئ]/g,'ء').toLowerCase();
let idx=null;function build(){idx=[];arts.forEach(a=>{const sec=$$('.name',a);if(sec.length){sec.forEach(s=>idx.push({id:s.id,t:s.dataset.name+' — '+a.dataset.title,x:s.textContent.replace(/\s+/g,' ')}))}else idx.push({id:a.id,t:a.dataset.title,x:a.textContent.replace(/\s+/g,' ')})});idx.forEach(r=>{r.n=norm(r.x);r.nt=norm(r.t)})}
const q=$('#q'),res=$('#results'),body=$('#tocbody');
q.addEventListener('input',()=>{const v=norm(q.value.trim());if(v.length<2){res.innerHTML='';body.hidden=false;return}if(!idx)build();body.hidden=true;
 const hits=idx.filter(r=>r.n.includes(v)||r.nt.includes(v)).slice(0,25);
 res.innerHTML=hits.length?hits.map(r=>{const i=r.n.indexOf(v);const s=i>=0?r.x.slice(Math.max(0,i-30),i+70):'';return `<a href="#${r.id}" data-s="1"><b>${esc(r.t)}</b>${esc(s)}…</a>`}).join(''):'<p class="small">لا نتائج.</p>'});
res.addEventListener('click',e=>{if(e.target.closest('a')){q.value='';res.innerHTML='';body.hidden=false}});
$$('.tocrow,.tn').forEach(a=>a.addEventListener('click',()=>openToc(false)));
mark();route();
})();
