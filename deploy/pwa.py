#!/usr/bin/env python3
"""يحوّل النسخة المبنية إلى PWA (يُشغَّل فقط عند PWA=1 في build_hostinger.sh).

الاستعمال: pwa.py <مجلد-الإخراج> [BASE=/] [preview]
  BASE     مسار النشر ('/' على الإنتاج؛ '/pwa-preview/' لمعاينة داخل مجلد).
  preview  يمنع الفهرسة (noindex + robots + X-Robots-Tag) لنسخ المعاينة.
"""
import os, sys, json, re, hashlib, pathlib

OUT = pathlib.Path(sys.argv[1])
BASE = sys.argv[2] if len(sys.argv) > 2 else '/'
PREVIEW = 'preview' in sys.argv[3:]
HERE = pathlib.Path(__file__).parent / 'pwa'
NAME, SHORT = 'تجليات الأسماء', 'تجليات'
THEME = '#0E1324'                                   # لون الموقع الليلي (--paper في الوضع الداكن)
if not (BASE.startswith('/') and BASE.endswith('/')):
    sys.exit('pwa: BASE must start and end with /')


def die(m):
    sys.exit('pwa: ' + m)


def read(p):
    return pathlib.Path(p).read_text(encoding='utf-8')


# ───────────── 1) manifest ─────────────
manifest = {
    'id': BASE, 'name': NAME, 'short_name': SHORT, 'description': 'تأمّل أسماء الله الحسنى: معنى كل اسم وتجلٍّ يومي ودفتر لأثره في حياتك.',
    'lang': 'ar', 'dir': 'rtl', 'start_url': BASE + '?source=pwa', 'scope': BASE, 'display': 'standalone',
    'background_color': THEME, 'theme_color': THEME, 'categories': ['education', 'lifestyle'],
    'icons': [
        {'src': BASE + 'icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
        {'src': BASE + 'icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
        {'src': BASE + 'icon-maskable-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'maskable'},
        {'src': BASE + 'icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}],
    'shortcuts': [{'name': 'اسم يناسب حالك', 'url': BASE + 'guide.html'}, {'name': 'أثر الاسم في حياتي', 'url': BASE + 'athar.html'}]}
if os.environ.get('ABOUT') == '1':                  # وصف المانيفست من النص العربي المعتمد نفسه
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import texts
    manifest['description'] = texts.ar('about_tajalliyat')
for f in ['icon-192.png', 'icon-512.png', 'icon-maskable-192.png', 'icon-maskable-512.png', 'apple-touch-icon.png', 'favicon-48.png', 'icon.svg']:
    if not (OUT / f).exists():
        die('missing ' + f)
(OUT / 'manifest.webmanifest').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
if (OUT / 'site.webmanifest').exists():
    (OUT / 'site.webmanifest').unlink()

# ───────────── 2) offline.html و pwa.js ─────────────
(OUT / 'offline.html').write_text(read(HERE / 'offline.html').replace('__BASE__', BASE), encoding='utf-8')
(OUT / 'pwa.js').write_text(read(HERE / 'pwa.js'), encoding='utf-8')

# ───────────── 3) الصفحات: روابط manifest/pwa.js + (اختياري) BASE و noindex ─────────────
APPLE = ('<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">'
         '<meta name="apple-mobile-web-app-title" content="' + SHORT + '"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">')
PAGES_WITH_APP = {'index.html', 'guide.html', 'athar.html'}
for p in sorted(OUT.rglob('*.html')):
    rel = p.relative_to(OUT).as_posix()
    if rel.startswith(('print/', 'source/')) or rel == 'offline.html':
        continue
    s = read(p); o = s
    if BASE != '/':                                      # معاينة داخل مجلد: الروابط المطلقة من الجذر تحتاج البادئة (قبل إضافة روابطنا)
        s = re.sub(r'(\s(?:href|src|action|poster)=["\'])/(?!/)', lambda m: m.group(1) + BASE, s)
        s = re.sub(r'url\(/(?!/)', 'url(' + BASE, s)
    s = s.replace('/site.webmanifest', BASE + 'manifest.webmanifest').replace(BASE + BASE.lstrip('/') + 'manifest.webmanifest', BASE + 'manifest.webmanifest')
    anchor = '</head>' if '</head>' in s else ('<style>' if rel == 'index.html' else None)
    add = ''
    if rel in PAGES_WITH_APP:
        if anchor is None:
            die('no head anchor in ' + rel)
        if 'rel="manifest"' not in s:
            add += '<link rel="manifest" href="' + BASE + 'manifest.webmanifest">'
        add += APPLE + '<script src="' + BASE + 'pwa.js" defer></script>'
    if PREVIEW and 'name="robots" content="noindex' not in s and anchor:
        s = re.sub(r'<meta name="robots" content="[^"]*"\s*/?>', '', s)
        add += '<meta name="robots" content="noindex,nofollow">'
    if add:
        s = s.replace(anchor, add + '\n' + anchor, 1)
    if s != o:
        p.write_text(s, encoding='utf-8')
missing = [r for r in PAGES_WITH_APP if 'pwa.js' not in read(OUT / r)]
if missing:
    die('pwa.js not linked in ' + ', '.join(missing))

# ───────────── 4) sw.js بإصدار من هاش الملفات ─────────────
fonts = sorted(f.name for f in (OUT / 'assets' / 'fonts').iterdir() if f.is_file())
CORE = [BASE, BASE + 'guide.html', BASE + 'athar.html', BASE + 'offline.html', BASE + 'manifest.webmanifest', BASE + 'pwa.js',
        BASE + 'icon.svg', BASE + 'favicon-48.png', BASE + 'apple-touch-icon.png', BASE + 'icon-192.png', BASE + 'icon-512.png'] + \
       [BASE + 'assets/fonts/' + f for f in fonts]
DATA = [BASE + 'data.js', BASE + 'prod.js', BASE + 'news.js']
OPTIONAL = [BASE + 'books/', BASE + 'feel/', BASE + 'books/reader.css', BASE + 'books/reader.js']


def local(url):
    r = url[len(BASE):]
    f = OUT / (r + 'index.html' if (r == '' or r.endswith('/')) else r)
    return f


h = hashlib.sha1((HERE / 'sw.js').read_bytes())
for u in CORE + DATA + OPTIONAL:
    f = local(u)
    if not f.exists():
        if u in OPTIONAL:
            continue
        die('precache file missing: ' + u)
    h.update(u.encode()); h.update(f.read_bytes())
VERSION = h.hexdigest()[:12]
sw = read(HERE / 'sw.js')
for k, v in {'__VERSION__': VERSION, '__BASE__': BASE, '__CORE__': json.dumps(CORE), '__OPTIONAL__': json.dumps([u for u in OPTIONAL if local(u).exists()]),
             '__DATA__': json.dumps(DATA)}.items():
    sw = sw.replace(k, v)
if re.search(r'__(VERSION|BASE|CORE|OPTIONAL|DATA)__', sw):
    die('unreplaced placeholder in sw.js')
(OUT / 'sw.js').write_text(sw, encoding='utf-8')

# ───────────── 5) معاينة: منع الفهرسة ─────────────
if PREVIEW:
    (OUT / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
    if (OUT / 'sitemap.xml').exists():
        (OUT / 'sitemap.xml').unlink()
    ht = OUT / '.htaccess'
    ht.write_text(read(ht) + '\n# معاينة: لا فهرسة\n<IfModule mod_headers.c>\n  Header set X-Robots-Tag "noindex, nofollow"\n</IfModule>\n', encoding='utf-8')
print(f'pwa: version {VERSION}, base {BASE}, {len(CORE)} core + {len(DATA)} data files' + (', PREVIEW (noindex)' if PREVIEW else ''))
