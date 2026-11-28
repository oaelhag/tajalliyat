#!/usr/bin/env python3
"""يزيل اسم المطوّر من كل ملفات النسخة المنشورة على Hostinger (main لا يُلمس).
يعمل على ملفات النص (HTML/JS/JSON/XML) وعلى ملفات PDF للكتب، ثم يتحقق، ويفشّل البناء إن بقي أثر للاسم.

الاستعمال: scrub_developer.py <مجلد-الإخراج>
"""
import sys, re, pathlib, subprocess, tempfile, shutil, collections
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream

OUT = pathlib.Path(sys.argv[1])
NAME = 'أسامة عبد الهادي الهاجري'
LEFT = re.compile(r'أسامة عبد|الهاجري|oaelhag', re.I)            # أي أثر للاسم أو لحساب GitHub
TEXT_EXT = {'.html', '.js', '.json', '.xml', '.txt', '.css', '.webmanifest', '.ics', '.svg'}


def die(msg):
    sys.exit('scrub_developer: ' + msg)


# ───────────── 1) ملفات النص ─────────────
RULES = [
    (re.compile(r'<p class="by">المطوّر:[^<]*</p>'), ''),                                  # سطر المطوّر في غلاف الكتاب
    (re.compile(r'<p[^>]*>تطوير ' + NAME + r'</p>'), ''),                                  # تذييل guide.html
    (re.compile(r'<br>تطوير ' + NAME), ''),                                                # تذييل الرئيسية
    (re.compile(r'\s*المطوّر:\s*' + NAME + r'\.?'), ''),                                   # جملة صفحة الحقوق في الكتب
    (re.compile(r'"publisher": \{"@type": "Person", "name": "' + NAME + r'"\}'),
     '"publisher": {"@type": "Organization", "name": "تجليات الأسماء"}'),                  # JSON-LD
]
changed = collections.Counter()
for p in OUT.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in TEXT_EXT:
        continue
    s = p.read_text(encoding='utf-8', errors='ignore')
    if not LEFT.search(s) and 'المطوّر' not in s:
        continue
    o = s
    for rx, rep in RULES:
        s = rx.sub(rep, s)
    if s != o:
        p.write_text(s, encoding='utf-8'); changed[p.name] += 1
left = [str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file() and p.suffix.lower() in TEXT_EXT
        and LEFT.search(p.read_text(encoding='utf-8', errors='ignore'))]
if left:
    die('name still present in text files: ' + ', '.join(left))
print(f'scrub_developer: {sum(changed.values())} text edits in {len(changed)} files')

# ───────────── 2) ملفات PDF للكتب (سطر واحد في صفحة الحقوق) ─────────────
if not shutil.which('pdftotext'):
    die('pdftotext is required to verify the PDFs')


def ptext(path, first=None, last=None):
    cmd = ['pdftotext'] + (['-f', str(first), '-l', str(last)] if first else []) + [str(path), '-']
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def text_y(ops, i):
    j = i
    while ops[j][1] != b'Tm':
        j += 1
    return round(float(ops[j][0][5]), 1)


def blocks(ops):
    out, i = [], 0
    while i < len(ops):
        if ops[i][1] == b'BT':
            e = i
            while ops[e][1] != b'ET':
                e += 1
            out.append((i, e, text_y(ops, i)))
            i = e
        i += 1
    return out


def scrub_pdf(path):
    if not LEFT.search(ptext(path).replace('‫', '').replace('‪', '')) and 'المطّو' not in ptext(path):
        return False
    before = ptext(path, 2, 2)
    n_before = len([l for l in before.splitlines() if l.strip()])
    r = PdfReader(str(path))
    for y in sorted({b[2] for b in blocks(ContentStream(r.pages[1].get_contents(), r).operations)}, reverse=True):
        w = PdfWriter(clone_from=r)
        pg = w.pages[1]
        cs = ContentStream(pg.get_contents(), w)
        ops = cs.operations
        sel = [b for b in blocks(ops) if b[2] == y]
        lo, hi = sel[0][0], sel[-1][1]
        if sum(e - s + 1 for s, e, _ in sel) != hi - lo + 1:
            continue                                   # يجب أن تكون الكتل متجاورة
        cs.operations = ops[:lo] + ops[hi + 1:]
        pg.replace_contents(cs)
        tmp = pathlib.Path(tempfile.mkdtemp()) / 't.pdf'
        w.write(str(tmp))
        after = ptext(tmp, 2, 2)
        n_after = len([l for l in after.splitlines() if l.strip()])
        if not re.search(r'أسامة|الهاج|oaelhag|المطّو|المطوّر', after) and 0 < n_before - n_after <= 2:
            shutil.move(str(tmp), str(path)); return True
        shutil.rmtree(tmp.parent)
    die(f'could not safely remove the name from {path.name}')


n = 0
for pdf in sorted((OUT / 'books' / 'pdf').glob('*.pdf')):
    n += scrub_pdf(pdf)
for pdf in OUT.rglob('*.pdf'):                          # تحقق نهائي من كل الـ PDF
    t = ptext(pdf)
    if re.search(r'أسامة|الهاج\s*ري|oaelhag', t):
        die('name still present in ' + str(pdf.relative_to(OUT)))
print(f'scrub_developer: {n} book PDFs cleaned; all PDFs verified')
