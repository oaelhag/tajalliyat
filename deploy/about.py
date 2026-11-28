#!/usr/bin/env python3
"""يضيف شرح معنى «تجليات» للصفحة الأولى من النسخة المبنية (يُشغَّل فقط عند ABOUT=1).

- النص العربي يُقرأ من deploy/content/site_texts.json (المفتاح about_tajalliyat) ويُشترط status = approved.
- لا يُكتب النص بيد في أي ملف HTML؛ والنص الإنجليزي لا يُعرض في أي صفحة (يُفحص ذلك في النهاية).
- يحدّث meta description (و og/twitter) للصفحة الرئيسية من النص نفسه. وصف manifest يتولاه pwa.py من المصدر نفسه.

الاستعمال: about.py <مجلد-الإخراج>
"""
import sys, re, html, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import texts

OUT = pathlib.Path(sys.argv[1])
KEY = 'about_tajalliyat'
AR = texts.ar(KEY)                                    # يفشل إن لم يكن معتمداً أو خالف القاعدة اللغوية
EN = texts.en(KEY)
esc = lambda s: html.escape(s, quote=True)


def die(m):
    sys.exit('about: ' + m)


p = OUT / 'index.html'
s = p.read_text(encoding='utf-8')


def sub(old, new, count=1):
    global s
    if s.count(old) != count:
        die(f'expected {count} match(es), got {s.count(old)} for: {old[:60]!r}')
    s = s.replace(old, new)


# ───────── 1) الشريط تحت العنوان (قبل أزرار الفئات) ─────────
STRIP = (f'<section class="about-strip" id="about-meaning" aria-label="معنى «تجليات»">'
         f'<p>{esc(AR)}</p>'
         f'<button type="button" class="about-q" aria-label="اقرأ معنى «تجليات» كاملاً" aria-haspopup="dialog">؟</button></section>\n  ')
sub('<div class="aud" id="aud"', STRIP + '<div class="aud" id="aud"')

CSS = """
/* ── معنى «تجليات» (الصفحة الأولى) ── */
.about-strip{display:flex;align-items:flex-start;justify-content:flex-start;gap:10px;margin:0 0 14px}
.about-strip p{flex:0 1 auto;min-width:0;margin:0;padding-top:8px;font-family:var(--f-ui);font-size:var(--fs-cap);line-height:1.85;color:var(--ink-soft);display:-webkit-box;-webkit-line-clamp:2;line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.about-q{flex:none;min-width:44px;min-height:44px;padding:0;border-radius:50%;border:1px solid var(--rule);background:var(--leaf);color:var(--gold-text);font:600 20px/1 var(--f-ui);cursor:pointer;display:inline-flex;align-items:center;justify-content:center;transition:border-color .2s,transform .2s}
.about-q:hover{border-color:var(--gold)}
.about-q:focus-visible{outline:2px solid var(--gold);outline-offset:3px}
.about-dlg p{margin:0;line-height:2;font-size:var(--fs-body,1.05rem)}
.about-dlg h2{margin:0;font-size:var(--fs-h3,1.2rem)}
"""
sub('</style>\n\n<div class="wrap top">', CSS + '</style>\n\n<div class="wrap top">')

JS = """<script>(function(){
var strip=document.getElementById('about-meaning');if(!strip)return;
var btn=strip.querySelector('.about-q'),txt=strip.querySelector('p').textContent,today=document.getElementById('v-today');
function sync(){strip.hidden=!!(today&&today.hidden);}                 /* يظهر في الصفحة الأولى فقط */
if(today&&window.MutationObserver)new MutationObserver(sync).observe(today,{attributes:true,attributeFilter:['hidden']});
sync();
var modal=null,prev='',reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
function onKey(e){
  if(!modal)return;
  if(e.key==='Escape'){e.preventDefault();e.stopPropagation();close();}
  else if(e.key==='Tab'){e.preventDefault();modal.querySelector('.btn').focus();}
}
function close(){
  if(!modal)return;var m=modal;modal=null;
  document.removeEventListener('keydown',onKey,true);document.body.style.overflow=prev;
  m.classList.add('out');setTimeout(function(){m.remove();btn.focus({preventScroll:true});},reduce?0:200);
}
function open(){
  if(modal)return;
  var box=document.createElement('div');box.className='box about-dlg';
  var h=document.createElement('h2');h.id='about-dlg-title';h.textContent='معنى «تجليات»';
  var p=document.createElement('p');p.textContent=txt;
  var row=document.createElement('div');row.className='row';
  var x=document.createElement('button');x.type='button';x.className='btn ghost';x.textContent='إغلاق';x.onclick=close;
  row.append(x);box.append(h,p,row);
  modal=document.createElement('div');modal.className='modal';modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');modal.setAttribute('aria-labelledby','about-dlg-title');
  modal.onclick=function(e){if(e.target===modal)close();};
  modal.append(box);
  prev=document.body.style.overflow;document.body.style.overflow='hidden';
  document.addEventListener('keydown',onKey,true);document.body.append(modal);x.focus();
}
btn.addEventListener('click',open);
})();</script>
"""
sub('\n</html>', '\n' + JS + '</html>')

# ───────── 2) الوصف في meta للصفحة الرئيسية من النص نفسه ─────────
for pat in (r'(<meta name="description" content=")[^"]*(")', r'(<meta property="og:description" content=")[^"]*(")',
            r'(<meta name="twitter:description" content=")[^"]*(")'):
    s, n = re.subn(pat, lambda m: m.group(1) + esc(AR) + m.group(2), s)
    if n != 1:
        die('description tag not found exactly once: ' + pat)
p.write_text(s, encoding='utf-8')

# ───────── 3) تحقق: النص العربي حرفياً، والإنجليزي لا يظهر في أي ملف منشور ─────────
check = p.read_text(encoding='utf-8')
if check.count(esc(AR)) < 4:
    die('Arabic text is missing from strip/meta')
probe = ['Tajalliyat (tah', 'tah-jal-lee', "Allah's Beautiful Names in our"]
for f in OUT.rglob('*'):
    if f.is_file() and f.suffix.lower() in {'.html', '.js', '.json', '.xml', '.txt', '.webmanifest', '.css'}:
        t = f.read_text(encoding='utf-8', errors='ignore')
        if any(x in t for x in probe):
            die(f'English text leaked into {f.relative_to(OUT)}')
print('about: strip + meta descriptions added; English text not published')
