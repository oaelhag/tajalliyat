#!/usr/bin/env python3
"""تحسينات SEO ومعاينة المشاركة على نسخة Hostinger المبنية (main لا يُلمس).

الاستعمال:  gen_seo.py <مجلد-الإخراج> [gen|check]
  gen   : صفحات «قلبي الآن» الثابتة، روابط قابلة للزحف في الرئيسية، أيقونات وmanifest،
          إكمال أوسمة OG/Twitter/JSON-LD الناقصة، وتحديث sitemap.
  check : بعد توليد الصور، ينسخ og/default.jpg مكان أي صورة معاينة مفقودة.
المحتوى كله من data.js المنشور أصلاً (window.FEEL / window.ASMA)؛ لا نصوص جديدة.
"""
import sys, json, re, html, struct, pathlib, datetime

OUT = pathlib.Path(sys.argv[1])
MODE = sys.argv[2] if len(sys.argv) > 2 else 'gen'
BASE = 'https://tajalliyat.com'
SITE = 'تجليات الأسماء'
TODAY = datetime.date.today().isoformat()
DEFAULT_ALT = 'تجليات الأسماء: تأمّل أسماء الله الحسنى'
esc = lambda s: html.escape(str(s), quote=True)


def die(msg):
    sys.exit('gen_seo: ' + msg)


# ───────────────────────── وضع الفحص ─────────────────────────
if MODE == 'check':
    default = OUT / 'og' / 'default.jpg'
    fixed = 0
    for page in OUT.rglob('*.html'):
        for ref in set(re.findall(r'content="https://tajalliyat\.com/(og/[^"]+\.jpg)"', page.read_text(encoding='utf-8'))):
            if not (OUT / ref).exists():
                (OUT / ref).write_bytes(default.read_bytes()); fixed += 1; print('fallback image for', ref)
    for f in ['icon.svg', 'favicon-48.png', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png', 'icon-maskable-192.png', 'icon-maskable-512.png']:
        if not (OUT / f).exists():
            print('WARNING: missing', f)
    print('gen_seo check: ok,', fixed, 'fallbacks')
    sys.exit(0)

# ───────────────────────── قراءة البيانات ─────────────────────────
raw = (OUT / 'data.js').read_text(encoding='utf-8')
dec = json.JSONDecoder()


def grab(var):
    key = 'window.' + var + '='
    return dec.raw_decode(raw[raw.index(key) + len(key):])[0]


NAMES = {n['id']: n for n in grab('ASMA')}
FEEL = grab('FEEL')
assert len(FEEL) >= 10 and len(NAMES) >= 40, 'unexpected data'

# موضوع كل شعور بصيغة تقرأ جيداً بعد «عند»
TOPIC = {'sad': 'الحزن', 'anxious': 'القلق', 'lonely': 'الوحدة', 'guilty': 'الشعور بالذنب', 'angry': 'الغضب',
         'wronged': 'الشعور بالظلم', 'tired': 'التعب', 'confused': 'الحيرة', 'grateful': 'الامتنان',
         'worried': 'الهمّ', 'afraid': 'الخوف', 'rizq': 'طلب الرزق', 'weak': 'الشعور بالضعف'}
for f in FEEL:
    if f['id'] not in TOPIC:
        die('no topic for feeling ' + f['id'])

CARE = ('إن كان الحزن أو القلق ثقيلاً ويطول أسابيع، أو راودتك أفكار بإيذاء نفسك، فالحديث مع طبيب أو مختص '
        'نفسي أو شخص تثق به جزء من الأخذ بالأسباب، ولا يتعارض مع التوكل على الله.')

# أنماط الصفحة من صفحة اسم موجودة (نفس الشكل تماماً)
tpl = (OUT / 'n' / 'rahman' / 'index.html').read_text(encoding='utf-8')
CSS = re.search(r'<style>(.*?)</style>', tpl, re.S).group(1).replace('../../assets', '/assets')
STAR = ('<svg class="star" viewBox="0 0 64 64" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2.2">'
        '<rect x="14" y="14" width="36" height="36"/><rect x="14" y="14" width="36" height="36" transform="rotate(45 32 32)"/></g></svg>')
HEAD_COMMON = '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + '</script>'


def crumbs(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(items)]}


def head(title, desc, url, image, alt, extra_ld, og_type='article'):
    return f'''<!doctype html>
<html lang="ar" dir="rtl"><head>{HEAD_COMMON}
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}"><meta property="og:locale" content="ar_AR"><meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(alt)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{image}"><meta name="twitter:image:alt" content="{esc(alt)}">
<meta name="theme-color" content="#0E1324">
{ld(extra_ld)}
<style>{CSS}
h1.sm{{font-size:clamp(30px,8vw,54px);line-height:1.5}}ol.st{{padding:0 22px}}ol.st li{{margin:10px 0}}.care{{font:400 15px/1.9 Plex;opacity:.8;margin-top:26px}}
.cards{{display:grid;gap:10px}}.cards a.box{{display:block;text-decoration:none;color:inherit}}.cards a.box b{{color:var(--gt);font:600 20px Plex}}</style></head><body><main>
'''


FOOT = '<footer>مادة تربوية للتأمل، وهي قيد المراجعة الشرعية الدائمة. ' + SITE + '</footer>\n</main></body></html>\n'


def others(cur):
    links = ''.join(f"<a href='/feel/{x['id']}/'" + (' aria-current=page' if x['id'] == cur else '') + f">{esc(x['label'])}</a>" for x in FEEL)
    return f'<section><h2>مشاعر أخرى</h2><div class="row">{links}</div></section>'


# ───────────────────────── صفحات «قلبي الآن» ─────────────────────────
feel_dir = OUT / 'feel'
feel_dir.mkdir(exist_ok=True)
jobs = {'og': [], 'icons': [48, 180, 192, 512]}

for f in FEEL:
    t = TOPIC[f['id']]
    url = f'{BASE}/feel/{f["id"]}/'
    img = f'{BASE}/og/feel-{f["id"]}.jpg'
    nm = [NAMES[i] for i in f['names'] if i in NAMES]
    title = f'أسماء الله الحسنى عند {t}: كلمة وآية ودعاء وخطوات | {SITE}'
    desc = f"{f['open']} آية ودعاء وثلاث خطوات صغيرة مع أسماء الله: " + ' و'.join(n['plain'] for n in nm[:3]) + '.'
    alt = f'بطاقة: أسماء الله الحسنى عند {t}'
    graph = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': title, 'description': desc, 'url': url, 'inLanguage': 'ar', 'image': img,
         'isPartOf': {'@type': 'WebSite', 'name': SITE, 'url': BASE + '/'},
         'publisher': {'@type': 'Organization', 'name': SITE, 'url': BASE + '/'},
         'about': [{'@type': 'Thing', 'name': n['plain'], 'url': f'{BASE}/n/{n["id"]}/'} for n in nm]},
        crumbs([(SITE, BASE + '/'), ('قلبي الآن', BASE + '/feel/'), (f['label'], url)])]}
    a = f['ayah']
    names_html = ''.join(
        f'<a class="box" href="/n/{n["id"]}/"><b>{esc(n["plain"])}</b> — {esc(n["tagline"])}<p style="margin:6px 0 0">{esc((f.get("how") or {}).get(n["id"], ""))}</p></a>'
        for n in nm)
    steps = ''.join(f'<li>{esc(x)}</li>' for x in f['now'])
    body = f'''<header class="hero">{STAR}<div class="kick">{SITE} · قلبي الآن</div><h1 class="sm">أسماء الله الحسنى عند {esc(t)}</h1><p class="tag">{esc(f['open'])}</p></header>
<section><h2>كلمة للقلب</h2><div class="box"><p style="margin:0">{esc(f['message'])}</p></div></section>
<section><h2>آية</h2><div class="box ay">﴿{esc(a['text'])}﴾<small>سورة {esc(a['surah'])}، الآية {esc(a['num'])}</small></div></section>
<section><h2>أسماء ترافقك في هذا الشعور</h2><div class="cards">{names_html}</div></section>
<section><h2>الآن، في دقائق</h2><ol class="st">{steps}</ol></section>
<section><h2>دعاء</h2><div class="had">{esc(f['dua']['text'])}<small>{esc(f['dua']['src'])}</small></div></section>
<div class="cta"><a class="btn" href="/#feel-{f['id']}">افتحها في الموقع التفاعلي</a><a class="btn g" href="/guide.html">اسم يناسب حالك</a><a class="btn g" href="/feel/">كل المشاعر</a></div>
{others(f['id'])}
<p class="care">{CARE}</p>
'''
    d = feel_dir / f['id']
    d.mkdir(exist_ok=True)
    (d / 'index.html').write_text(head(title, desc, url, img, alt, graph) + body + FOOT, encoding='utf-8')
    jobs['og'].append({'path': f'og/feel-{f["id"]}.jpg', 'kick': 'أسماء الله الحسنى عند', 'name': t, 'tag': f['open'],
                       'size': 130 if len(t) <= 8 else 96, 'tagSize': 34 if len(f['open']) > 55 else 40})

# صفحة الفهرس /feel/
hub_url = BASE + '/feel/'
hub_title = f'قلبي الآن: بماذا تشعر؟ أسماء الله الحسنى لكل حال | {SITE}'
hub_desc = ('اختر ما تشعر به: حزن، قلق، وحدة، ذنب، غضب، ظلم، تعب، حيرة، خوف أو ضعف. '
            'ستجد كلمة تطمئنك وآية ودعاءً وخطوات صغيرة والأسماء التي ترافقك.')
hub_img = BASE + '/og/feel.jpg'
hub_graph = {'@context': 'https://schema.org', '@graph': [
    {'@type': 'CollectionPage', 'name': hub_title, 'description': hub_desc, 'url': hub_url, 'inLanguage': 'ar', 'image': hub_img,
     'isPartOf': {'@type': 'WebSite', 'name': SITE, 'url': BASE + '/'},
     'hasPart': [{'@type': 'WebPage', 'name': f['label'], 'url': f'{BASE}/feel/{f["id"]}/'} for f in FEEL]},
    crumbs([(SITE, BASE + '/'), ('قلبي الآن', hub_url)])]}
cards = ''.join(f'<a class="box" href="/feel/{f["id"]}/"><b>{esc(f["label"])}</b> — عند {esc(TOPIC[f["id"]])}<p style="margin:6px 0 0">{esc(f["open"])}</p></a>' for f in FEEL)
hub = (head(hub_title, hub_desc, hub_url, hub_img, 'بطاقة: قلبي الآن — بماذا تشعر؟', hub_graph, 'website') +
       f'<header class="hero">{STAR}<div class="kick">{SITE}</div><h1 class="sm">قلبي الآن: بماذا تشعر؟</h1><p class="tag">اختر ما تشعر به، وانظر أي اسم من أسماء الله الحسنى يرافقك فيه.</p></header>'
       f'<section><div class="cards">{cards}</div></section>'
       '<div class="cta"><a class="btn" href="/#feel">افتحها في الموقع التفاعلي</a><a class="btn g" href="/guide.html">اسم يناسب حالك</a></div>'
       f'<p class="care">{CARE}</p>' + FOOT)
(feel_dir / 'index.html').write_text(hub, encoding='utf-8')
jobs['og'].append({'path': 'og/feel.jpg', 'kick': SITE, 'name': 'قلبي الآن', 'tag': 'بماذا تشعر؟ كلمة وآية ودعاء وأسماء ترافقك', 'size': 150})

# صور المعاينة القديمة فيها عنوان GitHub مرسوماً داخل الصورة → نعيد رسمها بالدومين الجديد
og_list = json.loads((OUT / 'og_list.json').read_text(encoding='utf-8'))
for n in og_list:
    jobs['og'].append({'path': f'og/{n["id"]}.jpg', 'kick': 'تجليات الأسماء · اسم من أسماء الله الحسنى', 'name': n['name'], 'tag': n['tagline'], 'size': 170})
jobs['og'].append({'path': 'og/default.jpg', 'kick': 'أسماء الله الحسنى', 'name': SITE,
                   'tag': 'عِش أسماء الله الحسنى في يومك: معنى وتأمل وتجلٍّ لكل اسم', 'size': 170})
(OUT / '_img_jobs.json').write_text(json.dumps(jobs, ensure_ascii=False), encoding='utf-8')

# ───────────────────────── الصفحة الرئيسية: روابط قابلة للزحف ─────────────────────────
ip = OUT / 'index.html'
s = ip.read_text(encoding='utf-8')
m = re.search(r'<details class="sitenames">.*?</details>', s, re.S)
if not m:
    die('sitenames block not found in index.html')
block = m.group(0)
n_links = len(re.findall(r'href="#name-([a-z]+)"', block))
if n_links < 40:
    die(f'expected 42 name links, got {n_links}')
new_block = re.sub(r'href="#name-([a-z]+)"', r'href="/n/\1/"', block)
new_block = new_block.replace('اضغط على أي اسم لتفتح صفحته داخل الموقع.', 'اضغط على أي اسم لتفتح صفحته.')
feel_block = ('<details class="sitenames" id="feel-list" open><summary>بماذا تشعر الآن؟ (' + str(len(FEEL)) + ')</summary>'
              '<p>صفحة لكل شعور: كلمة وآية ودعاء وخطوات صغيرة والأسماء التي ترافقك.</p><div>' +
              ''.join(f'<a href="/feel/{f["id"]}/">{esc(f["label"])}</a>' for f in FEEL) + '</div></details>')
s = s.replace(block, new_block + '\n  ' + feel_block, 1)

# صفحة الحالة داخل التطبيق: رابط ثابت للصفحة المستقلة (للمشاركة بمعاينة صحيحة)
OLD = "(f.how&&f.how[id])||''));}))),\n    careNote());"
if s.count(OLD) != 1:
    die('feel() anchor not found')
NEW = ("(f.how&&f.how[id])||''));}))),\n    h('p',{class:'muted small'},h('a',{href:SITE_URL+'feel/'+f.id+'/'},'صفحة مستقلة لهذه الحالة (للحفظ والمشاركة)'),' · ',"
       "h('a',{href:'https://wa.me/?text='+encodeURIComponent(f.open+'\\n'+SITE_URL+'feel/'+f.id+'/'),target:'_blank',rel:'noopener'},'شاركها عبر واتساب')),\n    careNote());")
s = s.replace(OLD, NEW, 1)
ip.write_text(s, encoding='utf-8')

# guide.html: محتوى احتياطي ثابت وعنوان H1 (الـ JS يستبدله عند التشغيل)
gp = OUT / 'guide.html'
g = gp.read_text(encoding='utf-8')
G_OLD = '<main id="app" aria-live="polite"></main>'
if g.count(G_OLD) != 1:
    die('guide main anchor not found')
gdesc = re.search(r'<meta name="description" content="(.*?)"', g).group(1)
fallback = (f'<main id="app" aria-live="polite"><h1>اسم يناسب حالك</h1><p>{gdesc}</p>'
            '<p>' + ' · '.join(f'<a href="/feel/{f["id"]}/">{esc(f["label"])}</a>' for f in FEEL) + '</p></main>')
gp.write_text(g.replace(G_OLD, fallback, 1), encoding='utf-8')

# ───────────────────────── أيقونات و manifest ─────────────────────────
(OUT / 'icon.svg').write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#0E1324"/>'
    '<g fill="none" stroke="#E3B45C" stroke-width="2.6"><rect x="17" y="17" width="30" height="30"/>'
    '<rect x="17" y="17" width="30" height="30" transform="rotate(45 32 32)"/></g></svg>\n', encoding='utf-8')
(OUT / 'site.webmanifest').write_text(json.dumps({
    'name': SITE, 'short_name': 'تجليات', 'lang': 'ar', 'dir': 'rtl', 'start_url': '/', 'display': 'standalone',
    'background_color': '#0E1324', 'theme_color': '#0E1324',
    'icons': [{'src': '/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
              {'src': '/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]}, ensure_ascii=False, indent=1), encoding='utf-8')

# ───────────────────────── إكمال الأوسمة الناقصة في كل الصفحات ─────────────────────────
ICON_LINKS = '<link rel="icon" href="/icon.svg" type="image/svg+xml"><link rel="icon" href="/favicon-48.png" sizes="48x48" type="image/png">'


def has(s, k):
    return re.search(r'(?:property|name)="%s"' % re.escape(k), s) is not None


def get(s, k):
    m = re.search(r'(?:property|name)="%s"\s+content="(.*?)"' % re.escape(k), s)
    return html.unescape(m.group(1)) if m else None


def jpg_dims(p):
    d = p.read_bytes(); i = 2
    while i < len(d):
        if d[i] != 0xFF:
            i += 1; continue
        if d[i + 1] in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack('>HH', d[i + 5:i + 9]); return w, h
        i += 2 + struct.unpack('>H', d[i + 2:i + 4])[0]
    return None


def page_url(rel):
    if rel == 'index.html': return BASE + '/'
    if rel.endswith('/index.html'): return BASE + '/' + rel[:-10]
    return BASE + '/' + rel


touched = 0
for p in sorted(OUT.rglob('*.html')):
    rel = p.relative_to(OUT).as_posix()
    if rel.startswith(('print/', 'source/')) or rel == '404.html':
        continue
    s = p.read_text(encoding='utf-8')
    anchor = '</head>' if '</head>' in s else ('<style>' if rel == 'index.html' else None)
    if anchor is None:
        continue
    canon = (re.search(r'<link rel="canonical" href="(.*?)"', s) or [None, page_url(rel)])[1]
    title = get(s, 'og:title') or re.search(r'<title>(.*?)</title>', s, re.S).group(1).strip()
    desc = get(s, 'og:description') or get(s, 'description') or ''
    image = get(s, 'og:image') or BASE + '/og/default.jpg'
    local = OUT / image.replace(BASE + '/', '')
    dims = (1200, 630) if image.startswith(BASE + '/og/') else (jpg_dims(local) if local.exists() and local.suffix == '.jpg' else None)
    alt = DEFAULT_ALT if image.endswith('/og/default.jpg') else title
    add = []
    if 'rel="icon"' not in s: add.append(ICON_LINKS)
    if 'apple-touch-icon' not in s: add.append('<link rel="apple-touch-icon" href="/apple-touch-icon.png">')
    if 'rel="manifest"' not in s: add.append('<link rel="manifest" href="/site.webmanifest">')
    if not has(s, 'theme-color'): add.append('<meta name="theme-color" content="#0E1324">')
    for k, v in [('og:type', 'website'), ('og:locale', 'ar_AR'), ('og:site_name', SITE), ('og:title', title),
                 ('og:description', desc), ('og:url', canon), ('og:image', image), ('og:image:alt', alt)]:
        if v and not has(s, k): add.append(f'<meta property="{k}" content="{esc(v)}">')
    if dims:
        for k, v in [('og:image:width', dims[0]), ('og:image:height', dims[1])]:
            if not has(s, k): add.append(f'<meta property="{k}" content="{v}">')
    card = 'summary_large_image' if dims and dims[0] / dims[1] >= 1.6 else 'summary'
    for k, v in [('twitter:card', card), ('twitter:title', title), ('twitter:description', desc),
                 ('twitter:image', image), ('twitter:image:alt', alt)]:
        if v and not has(s, k): add.append(f'<meta name="{k}" content="{esc(v)}">')
    graph = []
    if 'application/ld+json' not in s:
        graph.append({'@type': 'WebPage', 'name': title, 'description': desc, 'url': canon, 'inLanguage': 'ar', 'image': image,
                      'isPartOf': {'@type': 'WebSite', 'name': SITE, 'url': BASE + '/'},
                      'publisher': {'@type': 'Organization', 'name': SITE, 'url': BASE + '/'}})
    if 'BreadcrumbList' not in s and rel != 'index.html':
        trail = [(SITE, BASE + '/')]
        if rel.startswith('books/') and rel != 'books/index.html': trail += [('الكتب المجانية', BASE + '/books/')]
        if rel.startswith('n/'):
            nid = rel.split('/')[1]
            trail += [(NAMES[nid]['plain'] if nid in NAMES else title, canon)]
        else:
            trail += [(re.sub(r'\s*\|.*$', '', title), canon)]
        graph.append(crumbs(trail))
    if graph:
        add.append(ld({'@context': 'https://schema.org', '@graph': graph}))
    if add:
        s = s.replace(anchor, '\n'.join(add) + '\n' + anchor, 1)
        p.write_text(s, encoding='utf-8'); touched += 1
print(f'gen_seo: {len(FEEL)} feeling pages + hub, {len(og_list)+len(FEEL)+2} share images queued, {touched} pages completed')

# ───────────────────────── sitemap ─────────────────────────
sp = OUT / 'sitemap.xml'
sm = sp.read_text(encoding='utf-8')
new_urls = [hub_url] + [f'{BASE}/feel/{f["id"]}/' for f in FEEL]
entries = ''.join(f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in new_urls if f'<loc>{u}</loc>' not in sm)
sm = sm.replace('</urlset>', entries + '</urlset>')
for u in (BASE + '/', BASE + '/guide.html'):
    sm = re.sub(r'(<loc>%s</loc><lastmod>)[^<]*' % re.escape(u), r'\g<1>' + TODAY, sm)
sp.write_text(sm, encoding='utf-8')
