"""Generate static GitHub Pages files: name pages (SEO + OG), print pages, sitemap, robots.
usage: python3 gen_static.py <data.js> <outdir>"""
import json,sys,html,pathlib,datetime
BASE='https://oaelhag.github.io/tajalliyat/'
SITE='تجليات الأسماء'
src=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8');OUT=pathlib.Path(sys.argv[2])
i=src.index('window.ASMA=')+12
A,_=json.JSONDecoder().raw_decode(src[i:])
GL={'boy':'طفل','girl':'طفلة','youngman':'شاب','youngwoman':'شابة','father':'أب','mother':'أم'}
KL=[('tajriba','تجربة'),('taammul','تأمل'),('fahm','فهم'),('tatbiq','تطبيق')]
e=html.escape
def cut(s,n):
    s=' '.join(s.split())
    return s if len(s)<=n else s[:n].rsplit(' ',1)[0]+'…'
FONTS='''@font-face{font-family:Kufi;src:url(%(r)sassets/fonts/reem-kufi-arabic-700-normal.woff2);font-weight:700}
@font-face{font-family:Kufi;src:url(%(r)sassets/fonts/reem-kufi-arabic-500-normal.woff2);font-weight:500}
@font-face{font-family:Naskh;src:url(%(r)sassets/fonts/noto-naskh-arabic-arabic-400-normal.woff2);font-weight:400}
@font-face{font-family:Naskh;src:url(%(r)sassets/fonts/noto-naskh-arabic-arabic-600-normal.woff2);font-weight:600}
@font-face{font-family:Naskh;src:url(%(r)sassets/fonts/noto-naskh-arabic-arabic-700-normal.woff2);font-weight:700}
@font-face{font-family:Plex;src:url(%(r)sassets/fonts/ibm-plex-sans-arabic-arabic-400-normal.woff2);font-weight:400}
@font-face{font-family:Plex;src:url(%(r)sassets/fonts/ibm-plex-sans-arabic-arabic-500-normal.woff2);font-weight:500}
@font-face{font-family:Quran;src:url(%(r)sassets/fonts/amiri-quran-arabic-400-normal.woff2)}'''
STAR='<svg class="star" viewBox="0 0 64 64" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2.2"><rect x="14" y="14" width="36" height="36"/><rect x="14" y="14" width="36" height="36" transform="rotate(45 32 32)"/></g></svg>'

def name_page(n,idx):
    pid=n['id'];url=f'{BASE}n/{pid}/'
    title=f"{n['plain']} — معناه وتجلياته وأسئلة التأمل | {SITE}"
    desc=cut(f"{n['tagline']}. {n['simple']}",155)
    ay=n['ayah']
    others=''.join(f"<li><span class='q'>{e(x['text'])}</span> <small>﴿{e(x['surah'])}: {e(x['num'])}﴾</small></li>" for x in n['ayat'] if x['ref']!=ay['ref'])
    had=''.join(f"<li>{e(h['text'])}<small>{e(h['src'])}</small></li>" for h in n['hadith'])
    prints=''.join(f"<a href='../../print/{pid}-{k}.html'>{v}</a>" for k,v in GL.items())
    chips=''.join(f"<a href='../{m['id']}/'{' aria-current=page' if m['id']==pid else ''}>{e(m['plain'])}</a>" for m in A)
    ld=json.dumps({'@context':'https://schema.org','@type':'Article','headline':title,'description':desc,'inLanguage':'ar','url':url,'image':f'{BASE}og/{pid}.jpg','publisher':{'@type':'Organization','name':SITE},'isPartOf':{'@type':'WebSite','name':SITE,'url':BASE}},ensure_ascii=False)
    return f'''<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:locale" content="ar_AR"><meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{e(n['plain'])} — {e(n['tagline'])}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}og/{pid}.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(n['plain'])} — {e(n['tagline'])}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{BASE}og/{pid}.jpg">
<meta name="theme-color" content="#0E1324">
<script type="application/ld+json">{ld}</script>
<style>{FONTS % {'r':'../../'}}
:root{{--bg:#F1F2F5;--ink:#1B2338;--gold:#A8761E;--card:#fff;--line:#d9dce4}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0E1324;--ink:#E9E6DD;--gold:#E3B45C;--card:#161d33;--line:#2a3350}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:400 18px/1.9 Naskh,serif}}
main{{max-width:760px;margin:0 auto;padding:28px 18px 60px}}
.hero{{text-align:center;padding:30px 0 10px;color:var(--gold)}}.star{{width:44px;height:44px}}
.kick{{font:500 14px Plex;letter-spacing:.04em;color:var(--ink);opacity:.65;margin-top:6px}}
h1{{font:700 clamp(54px,14vw,96px)/1.2 Kufi;margin:6px 0 0;color:var(--gold)}}
.tag{{font:600 21px/1.7 Naskh;margin:6px 0 0}}
h2{{font:700 20px Kufi;color:var(--gold);margin:30px 0 6px}}
.box{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px}}
.ay{{font:400 28px/2.1 Quran;text-align:center}}.ay small{{display:block;font:500 14px Plex;opacity:.65}}
ul{{padding:0 20px;margin:0}}li{{margin:8px 0}}li small{{display:block;font:400 14px Plex;opacity:.65}}.q{{font-family:Quran;font-size:22px}}
.cta{{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0 0;justify-content:center}}
.btn{{background:var(--gold);color:#fff;text-decoration:none;padding:11px 20px;border-radius:999px;font:600 16px Naskh}}
.btn.g{{background:none;color:var(--gold);border:1.5px solid var(--gold)}}
.row{{display:flex;gap:8px;flex-wrap:wrap}}.row a{{border:1px solid var(--line);color:var(--ink);text-decoration:none;padding:4px 14px;border-radius:999px;font:500 15px Plex;background:var(--card)}}
.row a[aria-current]{{background:var(--gold);color:#fff;border-color:var(--gold)}}
footer{{text-align:center;font:400 13px Plex;opacity:.6;margin-top:34px}}
</style></head><body><main>
<header class="hero">{STAR}<div class="kick">{SITE} · اسم من أسماء الله الحسنى</div><h1>{e(n['name'])}</h1><p class="tag">{e(n['tagline'])}</p></header>
<section><h2>المعنى</h2><div class="box"><p style="margin:0">{e(n['simple'])}</p></div></section>
<section><h2>آية الاسم</h2><div class="box ay">{e(ay['text'])}<small>﴿{e(ay['surah'])}: {e(ay['num'])}﴾</small></div></section>
<section><h2>المعنى العميق</h2><p>{e(n['deep'])}</p></section>
{('<section><h2>آيات أخرى</h2><ul>'+others+'</ul></section>') if others else ''}
{('<section><h2>من السنة</h2><ul>'+had+'</ul></section>') if had else ''}
<div class="cta"><a class="btn" href="../../#name-{pid}">افتح التجربة الكاملة للاسم</a><a class="btn g" href="../../#feel">قلبي الآن</a></div>
<section><h2>اطبع الاسم بمعناه وأسئلته وتجلياته (PDF)</h2><div class="row">{prints}</div></section>
<section><h2>أسماء أخرى</h2><div class="row">{chips}</div></section>
<footer>مادة تربوية للتأمل، وهي قيد المراجعة الشرعية الدائمة. {SITE}</footer>
</main></body></html>'''

def lines(n):return ''.join('<i></i>' for _ in range(n))
def print_page(n,g):
    G=n['groups'][g];ay=n['ayah'];lab=GL[g]
    qs=''.join(f"<li><span>{e(q)}</span><b>{lines(2)}</b></li>" for q in G['questions'])
    tj=''.join(f"<li><em></em>{e(t)}</li>" for t in G['tajalliyat'])
    tk=''.join(f"<div class='tk'><h4>{lbl}</h4><ul>"+''.join(f"<li>{e(t)}</li>" for t in G['tasks'][k])+"</ul></div>" for k,lbl in KL)
    had=n['hadith'][0] if n['hadith'] else None
    note=G.get('note','')
    notelbl='للمربّي' if g in('boy','girl') else 'ملاحظة'
    foot=f"<div class='pf'>{SITE} · {e(n['plain'])} · {lab} <span>{BASE.replace('https://','')}</span></div>"
    return f'''<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>{e(n['plain'])} — {lab} — {SITE} (للطباعة)</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<style>{FONTS % {'r':'../'}}
@page{{size:A4;margin:12mm}}
*{{box-sizing:border-box}}html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{margin:0;background:#ddd;color:#1B2338;font:400 12.5pt/1.85 Naskh,serif}}
.bar{{position:sticky;top:0;background:#1B2338;color:#fff;text-align:center;padding:10px;font:500 14px Plex}}
.bar button{{font:600 14px Naskh;background:#E3B45C;border:0;border-radius:999px;padding:6px 18px;margin:0 8px;cursor:pointer}}
.pg{{width:210mm;min-height:297mm;margin:12px auto;background:#fff;padding:12mm;position:relative;display:flex;flex-direction:column;break-after:page;overflow:hidden}}
.pg:last-child{{break-after:auto}}
.frame{{position:absolute;inset:6mm;border:1.2pt solid #A8761E;border-radius:3mm;opacity:.45;pointer-events:none}}
.frame:after{{content:"";position:absolute;inset:1.6mm;border:.5pt solid #A8761E;border-radius:2mm}}
.in{{position:relative;flex:1;padding:6mm 5mm 0;display:flex;flex-direction:column}}
.hd{{text-align:center;color:#A8761E}}.star{{width:12mm;height:12mm}}
.kick{{font:500 9pt Plex;color:#1B2338;opacity:.7;letter-spacing:.04em}}
h1{{font:700 66pt/1.15 Kufi;margin:2mm 0 0}}.tag{{font:600 14pt/1.6 Naskh;color:#1B2338;margin:0}}
.chip{{display:inline-block;border:1pt solid #A8761E;border-radius:99px;padding:0 4mm;font:500 10pt Plex;margin-top:3mm;color:#A8761E}}
h2{{font:700 14pt Kufi;color:#A8761E;margin:6mm 0 1.5mm;display:flex;align-items:center;gap:3mm}}
h2:after{{content:"";flex:1;height:.6pt;background:#A8761E;opacity:.4}}
.ayb{{border:.8pt solid #d8c9a6;background:#fbf7ec;border-radius:3mm;text-align:center;padding:3mm 5mm;font:400 21pt/2.1 Quran}}
.ayb small{{display:block;font:500 9pt Plex;opacity:.7}}
p{{margin:0}}.had{{font-size:10.5pt;border-right:2pt solid #A8761E;padding-right:3mm;margin-top:2mm}}.had small{{display:block;font:400 8.5pt Plex;opacity:.7}}
ol{{margin:0;padding:0;list-style:none;counter-reset:q}}
ol li{{counter-increment:q;margin:0 0 2.4mm;position:relative;padding-right:9mm;break-inside:avoid}}
ol li:before{{content:counter(q);position:absolute;right:0;top:0;width:6.5mm;height:6.5mm;border-radius:50%;border:.8pt solid #A8761E;color:#A8761E;font:700 9pt/6.2mm Kufi;text-align:center}}
ol li span{{font-weight:600}}ol li b{{display:block}}ol li b i{{display:block;height:5.6mm;border-bottom:.5pt dotted #8a8f9e}}
.cols{{columns:2;column-gap:8mm}}.cols ul{{list-style:none;margin:0;padding:0}}
.cols li{{display:flex;gap:2.6mm;margin:0 0 2.6mm;break-inside:avoid;font-size:11.5pt;line-height:1.65}}
.cols li em{{flex:none;width:4.2mm;height:4.2mm;border:.9pt solid #A8761E;border-radius:50%;margin-top:1.6mm}}
.sub{{font:400 10pt Plex;opacity:.7;margin:-1mm 0 3mm}}
.tkg{{display:grid;grid-template-columns:1fr 1fr;gap:3mm}}
.tk{{border:.8pt solid #d8c9a6;border-radius:3mm;padding:2.5mm 4mm;break-inside:avoid}}.tk h4{{font:700 11pt Kufi;color:#A8761E;margin:0 0 1mm}}
.tk ul{{margin:0;padding:0 4mm;font-size:10.5pt;line-height:1.6}}.tk li{{margin:0 0 1mm}}
.les{{margin-top:5mm;text-align:center;font:700 14pt/1.8 Naskh;color:#A8761E;border-top:.6pt solid #d8c9a6;border-bottom:.6pt solid #d8c9a6;padding:3mm}}
.nt{{margin-top:4mm;font-size:10.5pt;background:#f3f4f8;border-radius:3mm;padding:3mm 4mm}}.nt b{{font-family:Kufi;color:#A8761E}}
.pf{{margin-top:auto;padding-top:3mm;border-top:.5pt solid #d8c9a6;display:flex;justify-content:space-between;font:400 8pt Plex;opacity:.7}}
@media print{{body{{background:#fff}}.bar{{display:none}}.pg{{margin:0;box-shadow:none;width:auto;height:271mm;min-height:0;padding:0}}}}
</style></head><body>
<div class="bar">للطباعة أو الحفظ PDF <button onclick="print()">اطبع / احفظ PDF</button> <a style="color:#E3B45C" href="../pdf/{n['id']}-{g}.pdf">تحميل PDF جاهز</a></div>
<section class="pg"><div class="frame"></div><div class="in">
<div class="hd">{STAR}<div class="kick">{SITE}</div><h1>{e(n['name'])}</h1><p class="tag">{e(n['tagline'])}</p><span class="chip">لـ{lab}</span></div>
<h2>معنى الاسم</h2><p>{e(G['simple'])}</p>
<h2>آية الاسم</h2><div class="ayb">{e(ay['text'])}<small>﴿{e(ay['surah'])}: {e(ay['num'])}﴾</small></div>
<h2>المعنى الأعمق</h2><p>{e(G['deep'])}</p>
{('<div class="had">'+e(had['text'])+'<small>'+e(had['src'])+'</small></div>') if had else ''}
{foot}</div></section>
<section class="pg"><div class="frame"></div><div class="in"><h2 style="margin-top:2mm">أسئلة للتأمل والكتابة</h2><div class="sub">اقرأ السؤال، واكتب أول ما يخطر في قلبك.</div><ol>{qs}</ol>{foot}</div></section>
<section class="pg"><div class="frame"></div><div class="in"><h2 style="margin-top:2mm">تجليات الاسم في حياتي</h2><div class="sub">ضع علامة على ما لاحظتَه في أيامك هذا الأسبوع. التجليات علامات للتأمل لا وعد بحدوثها.</div><div class="cols"><ul>{tj}</ul></div>{foot}</div></section>
<section class="pg"><div class="frame"></div><div class="in"><h2 style="margin-top:2mm">مهام عملية</h2><div class="tkg">{tk}</div>
<div class="les">{e(G['lesson'])}</div>{('<div class="nt"><b>'+notelbl+':</b> '+e(note)+'</div>') if note else ''}{foot}</div></section>
</body></html>'''

(OUT/'n').mkdir(parents=True,exist_ok=True);(OUT/'print').mkdir(exist_ok=True)
for n in A:
    d=OUT/'n'/n['id'];d.mkdir(parents=True,exist_ok=True)
    (d/'index.html').write_text(name_page(n,0),encoding='utf-8')
    for g in GL:(OUT/'print'/f"{n['id']}-{g}.html").write_text(print_page(n,g),encoding='utf-8')
today=datetime.date.today().isoformat()
urls=[BASE]+[f"{BASE}n/{n['id']}/" for n in A]
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls)+'</urlset>\n')
(OUT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nDisallow: /print/\nSitemap: {BASE}sitemap.xml\n')
(OUT/'404.html').write_text(f'<!doctype html><meta charset=utf-8><meta http-equiv=refresh content="0;url={BASE}"><title>{SITE}</title><a href="{BASE}">{SITE}</a>')
json.dump([{'id':n['id'],'name':n['name'],'plain':n['plain'],'tagline':n['tagline']} for n in A],open(OUT/'og_list.json','w'),ensure_ascii=False)
print('pages',len(A),'print',len(A)*6)
