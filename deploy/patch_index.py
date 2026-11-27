#!/usr/bin/env python3
"""يطبّق تعديلات Hostinger على index.html المبني (main لا يُلمس).
كل استبدال يتحقق أنه وجد النص بالضبط ويفشل البناء إن لم يجده."""
import sys, pathlib

out = pathlib.Path(sys.argv[1]); snippet = pathlib.Path(sys.argv[2]).read_text(encoding='utf-8')
p = out / 'index.html'; s = p.read_text(encoding='utf-8')

def sub(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f'patch_index: expected exactly 1 match, got {s.count(old)} for: {old[:70]!r}')
    s = s.replace(old, new)

# 1) زر مشاركة واحد بقائمة صغيرة: نعيد استعمال shareRow نفسه (نسخ/واتساب/بطاقة) دون تغيير منطقها
OLD_SHARE_ITEM = "function shareItem(t,n,kind){return h('div',{class:'shi'},h('span',{},t),shareRow(t+(kind==='q'?'':'.'),'',kind,nmeta(n,kind==='q'?'سؤال للتأمل':'تجلٍّ للتأمل'),true));}"
NEW_SHARE_ITEM = r"""const SHICON='<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 10.5l6.8-4M8.6 13.5l6.8 4"/></svg>';
let openShare=null;
function closeShare(){if(openShare){openShare.wrap.classList.remove('open');openShare.btn.setAttribute('aria-expanded','false');openShare=null;}}
document.addEventListener('click',e=>{if(openShare&&!openShare.wrap.contains(e.target))closeShare();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&openShare){const b=openShare.btn;closeShare();b.focus();}});
function shareItem(t,n,kind){
  const menu=shareRow(t+(kind==='q'?'':'.'),'',kind,nmeta(n,kind==='q'?'سؤال للتأمل':'تجلٍّ للتأمل'),true);
  menu.classList.add('shmenu');menu.setAttribute('aria-label','خيارات المشاركة');
  const btn=h('button',{type:'button',class:'shbtn','aria-label':'مشاركة','aria-haspopup':'true','aria-expanded':'false'});btn.innerHTML=SHICON;
  const wrap=h('div',{class:'shwrap'},btn,menu);
  btn.addEventListener('click',e=>{e.stopPropagation();const was=openShare&&openShare.wrap===wrap;closeShare();if(!was){wrap.classList.add('open');btn.setAttribute('aria-expanded','true');openShare={wrap,btn};}});
  menu.addEventListener('click',e=>{if(e.target.closest('button,a'))setTimeout(closeShare,e.target.closest('a')?0:900);});
  return h('div',{class:'shi'},h('span',{},t),wrap);}"""
sub(OLD_SHARE_ITEM, NEW_SHARE_ITEM)

CSS = """
/* ── Hostinger: زر مشاركة واحد + قائمة، ومساحة للشريط السفلي ── */
.shi{display:flex;align-items:flex-start;gap:8px}
.shi>span{flex:1;min-width:0}
.shwrap{position:relative;flex:none}
.shbtn{display:inline-flex;align-items:center;justify-content:center;min-width:40px;min-height:40px;padding:0;border:1px solid var(--rule);background:var(--leaf);color:var(--ink-soft);border-radius:999px;cursor:pointer;box-sizing:border-box}
.shbtn:hover,.shbtn[aria-expanded="true"]{border-color:var(--gold);color:var(--ink)}
.shwrap .shmenu{display:none;position:absolute;inset-inline-end:0;top:calc(100% + 4px);z-index:4;flex-direction:column;flex-wrap:nowrap;gap:2px;margin:0;padding:6px;min-width:150px;background:var(--paper);border:1px solid var(--rule);border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,.18)}
.shwrap.open .shmenu{display:flex}
.shwrap .shmenu button,.shwrap .shmenu a{width:100%;justify-content:flex-start;border:0;background:none;border-radius:8px;min-height:40px;padding:6px 12px;font-size:var(--fs-ui);text-align:start;box-sizing:border-box}
.shwrap .shmenu button:hover,.shwrap .shmenu a:hover{background:var(--lapis-soft);transform:none}
@media (max-width:640px){body{padding-bottom:calc(var(--navh,64px) + 24px + env(safe-area-inset-bottom,0px))}}
"""
sub("</style>\n\n<div class=\"wrap top\">", CSS + "</style>\n\n<div class=\"wrap top\">")

# 2) ارتفاع الشريط السفلي الفعلي → padding سفلي بقدره
NAVJS = """<script>(function(){function f(){var n=document.querySelector('nav');if(n&&getComputedStyle(n).position==='fixed')document.documentElement.style.setProperty('--navh',n.offsetHeight+'px');}f();addEventListener('resize',f);addEventListener('load',f);})();</script>
"""

# 3) قسم «تواصل معنا» قبل التذييل
# honeypot: left:-9999px يمدّ الصفحة أفقياً في الاتجاه RTL، فنخفيه بالقص بدل الإزاحة (الوظيفة نفسها)
HP_OLD = 'style="position:absolute;left:-9999px"'
HP_NEW = 'style="position:absolute;width:1px;height:1px;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap"'
if snippet.count(HP_OLD) != 1: sys.exit('patch_index: honeypot style not found in snippet')
snippet = snippet.replace(HP_OLD, HP_NEW)
CONTACT = '<section id="contact" aria-labelledby="contactTitle">\n' + snippet.replace('<h3>تواصل معنا</h3>', '<h2 id="contactTitle" style="font-size:var(--fs-h3,1.25rem)">تواصل معنا</h2>') + '\n</section>\n\n  '
sub("<footer>محتوى تربوي", CONTACT + "<footer>محتوى تربوي")
sub("</script>\n\n</html>", "</script>\n" + NAVJS + "\n</html>")
p.write_text(s, encoding='utf-8')
print('patch_index: ok')
