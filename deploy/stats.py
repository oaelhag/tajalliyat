#!/usr/bin/env python3
"""يضيف الإحصاء المجهول إلى النسخة المبنية (يُشغَّل فقط عند STATS=1).
- ينسخ stats.js ويربطه في كل الصفحات (عدا print/ وoffline).
- يضيف سطر الإفصاح في تذييل الرئيسية (النص من deploy/content/site_texts.json: analytics_notice).
الاستعمال: stats.py <مجلد-الإخراج>
"""
import sys, re, html, pathlib, shutil

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import texts

OUT = pathlib.Path(sys.argv[1])
HERE = pathlib.Path(__file__).parent / 'stats'
NOTICE = texts.ar('analytics_notice', allow_draft=True)


def die(m):
    sys.exit('stats: ' + m)


shutil.copyfile(HERE / 'stats.js', OUT / 'stats.js')
tag = '<script src="/stats.js" defer></script>'
n = 0
for p in sorted(OUT.rglob('*.html')):
    rel = p.relative_to(OUT).as_posix()
    if rel.startswith(('print/', 'source/')) or rel in ('offline.html', '404.html'):
        continue
    s = p.read_text(encoding='utf-8')
    if 'stats.js' in s:
        continue
    anchor = '</head>' if '</head>' in s else ('<style>' if rel == 'index.html' else None)
    if anchor is None:
        die('no head anchor in ' + rel)
    p.write_text(s.replace(anchor, tag + '\n' + anchor, 1), encoding='utf-8'); n += 1

ip = OUT / 'index.html'
s = ip.read_text(encoding='utf-8')
old = 'من المصحف.</footer>'
if s.count(old) != 1:
    die('footer anchor not found exactly once')
s = s.replace(old, 'من المصحف.<br><span class="stats-note">' + html.escape(NOTICE) + '</span></footer>')
ip.write_text(s, encoding='utf-8')
print(f'stats: stats.js linked in {n} pages, privacy notice added to the home footer')
