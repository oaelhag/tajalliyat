#!/usr/bin/env python3
"""مصدر واحد لأرقام الموقع (عدد الأسماء والمنتجات والفيديوهات وحالات «قلبي الآن»).

الأرقام تُحسب من البيانات نفسها (data.js وproducts/ وvideos/)، ثم:
  - تُكتب في stats.json (للقراءة الآلية)،
  - وتُوضع في README.md وindex.html داخل علامات <!--stat:KEY-->...<!--/stat-->
    وقوائم <!--stat-list:NAME-->...<!--/stat-list-->،
  - ويقرؤها gen_books.py مباشرة (وصف الكتب)،
  - و--check يفشل إن اختلف نص الكتب (source/books/*.md) عن العدد الحالي.

التشغيل من جذر المستودع، بعد build وgen_static:
    python3 -I source/tools/site_stats.py          # يحسب ويكتب
    python3 -I source/tools/site_stats.py --check  # يتحقق فقط (للتكامل)
لا يُكتب عدد الأسماء بيدك في أي ملف: ضع العلامة وشغّل هذا السكربت."""
import json, re, sys, glob, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = 'https://oaelhag.github.io/tajalliyat/'
AR = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')

# ── الأعداد بالكلمات (1–99) ───────────────────────────────────────────
_M = {1: 'واحد', 2: 'اثنان', 3: 'ثلاثة', 4: 'أربعة', 5: 'خمسة', 6: 'ستة', 7: 'سبعة', 8: 'ثمانية', 9: 'تسعة'}
_F = {1: 'واحدة', 2: 'اثنتان', 3: 'ثلاث', 4: 'أربع', 5: 'خمس', 6: 'ست', 7: 'سبع', 8: 'ثماني', 9: 'تسع'}


def words(n, case='nom', fem=False, definite=False):
    """العدد بالكلمات. case: nom (مرفوع) أو obl (مجرور/منصوب)."""
    assert 1 <= n <= 99, n
    obl = case == 'obl'
    u = _F if fem else _M
    al = 'ال' if definite else ''
    if n == 10:
        out = [('عشر' if fem else 'عشرة')]
    elif n < 10:
        w = u[n]
        if n == 2:
            w = ('اثنتين' if fem else 'اثنين') if obl else w
        out = [w]
    elif n < 20:
        if n == 11:
            first = 'إحدى' if fem else 'أحد'
            out = [first, 'عشرة' if fem else 'عشر']
        elif n == 12:
            first = ('اثنتي' if fem else 'اثني') if obl else ('اثنتا' if fem else 'اثنا')
            out = [first, 'عشرة' if fem else 'عشر']
        else:
            out = [u[n - 10], 'عشرة' if fem else 'عشر']
        return ' '.join([al + out[0]] + out[1:])
    else:
        t, o = divmod(n, 10)
        tens = {2: 'عشر', 3: 'ثلاث', 4: 'أربع', 5: 'خمس', 6: 'ست', 7: 'سبع', 8: 'ثمان', 9: 'تسع'}[t]
        tens = tens + ('ين' if obl else 'ون')
        parts = []
        if o:
            parts.append(words(o, case, fem))
        parts.append(tens)
        return ' و'.join(al + p for p in parts)
    return al + out[0]


def phrase(n, singular_acc, plural, case='nom', fem=False):
    """العدد مع المعدود: «اثنان وأربعون اسماً»، «ثمانية أسماء»."""
    assert n >= 3, 'العدد أقل من ٣ يحتاج صيغة مثنى'
    w = words(n, case, fem)
    return f'{w} {plural}' if n <= 10 else f'{w} {singular_acc}'


# ── حساب الأرقام من البيانات ─────────────────────────────────────────
def load():
    d = (ROOT / 'data.js').read_text(encoding='utf-8')
    i = d.index('window.ASMA=') + 12
    A, _ = json.JSONDecoder().raw_decode(d[i:])
    j = d.index('window.FEEL=') + 12
    F, _ = json.JSONDecoder().raw_decode(d[j:])
    return A, F


def compute():
    A, F = load()
    st = {
        'names': len(A),
        'name_products': len(glob.glob(str(ROOT / 'products/names/*.json'))),
        'videos': len(glob.glob(str(ROOT / 'videos/*.mp4'))),
        'feelings': len(F),
        'print_pages': len(glob.glob(str(ROOT / 'print/*.html'))),
        'pdf_files': len(glob.glob(str(ROOT / 'pdf/*.pdf'))),
    }
    return st, A


def tokens(st):
    n = st['names']
    return {
        'names.latin': str(n),
        'names.ar': str(n).translate(AR),
        'names.phrase': phrase(n, 'اسماً', 'أسماء'),
        'names.def_obl': words(n, 'obl', definite=True),
        'products.phrase_obl': phrase(st['name_products'], 'اسماً', 'أسماء', 'obl'),
        'videos.phrase_obl': phrase(st['videos'], 'اسماً', 'أسماء', 'obl'),
        'feelings.phrase': phrase(st['feelings'], 'حالة', 'حالات', fem=True),
        'print_pages.latin': str(st['print_pages']),
    }


# ── القوائم (تُولَّد من البيانات) ─────────────────────────────────────
def lists(A):
    return {
        'names': '\n'.join(f"- [{x['plain']}]({BASE}n/{x['id']}/)" for x in A),
        'site': ''.join(f'<a href="#name-{x["id"]}">{x["plain"]}</a>' for x in A),
    }


TOK = re.compile(r'(<!--stat:([a-z_.]+)-->)(.*?)(<!--/stat-->)', re.S)
LST = re.compile(r'(<!--stat-list:([a-z]+)-->)(.*?)(<!--/stat-list-->)', re.S)


def stamp(text, tk, ls):
    def t(m):
        assert m.group(2) in tk, 'علامة غير معروفة: ' + m.group(2)
        return m.group(1) + tk[m.group(2)] + m.group(4)

    def l(m):
        assert m.group(2) in ls, 'قائمة غير معروفة: ' + m.group(2)
        sep = '\n' if m.group(2) == 'names' else ''
        return m.group(1) + sep + ls[m.group(2)] + sep + m.group(4)

    return LST.sub(l, TOK.sub(t, text))


STAMPED = ['README.md', 'index.html']


def check_books(tk):
    """نصوص الكتب لا تُولَّد (تمرّ على المراجع)، فنتحقق فقط أن العدد فيها يطابق الحالي."""
    bad = []
    expect = tk['names.phrase']
    for f in sorted(glob.glob(str(ROOT / 'source/books/book_*.md'))):
        head = '\n'.join(pathlib.Path(f).read_text(encoding='utf-8').splitlines()[:6])
        if expect not in head:
            bad.append(f'{pathlib.Path(f).name}: يُتوقع «{expect}» في أول الملف')
    return bad


def selftest():
    assert words(42, 'nom') == 'اثنان وأربعون', words(42)
    assert words(42, 'obl', definite=True) == 'الاثنين والأربعين'
    assert words(35, 'obl') == 'خمسة وثلاثين'
    assert phrase(8, 'اسماً', 'أسماء', 'obl') == 'ثمانية أسماء'
    assert phrase(13, 'حالة', 'حالات', fem=True) == 'ثلاث عشرة حالة', phrase(13, 'حالة', 'حالات', fem=True)
    assert phrase(42, 'اسماً', 'أسماء') == 'اثنان وأربعون اسماً'
    assert words(20) == 'عشرون' and words(99, 'obl') == 'تسعة وتسعين' and words(12, 'obl') == 'اثني عشر'


def main():
    selftest()
    check_only = '--check' in sys.argv
    st, A = compute()
    tk, ls = tokens(st), lists(A)
    problems = []
    for rel in STAMPED:
        p = ROOT / rel
        old = p.read_text(encoding='utf-8')
        new = stamp(old, tk, ls)
        if new != old:
            if check_only:
                problems.append(f'{rel}: أرقام قديمة (شغّل site_stats.py)')
            else:
                p.write_text(new, encoding='utf-8')
                print('حُدّث', rel)
    problems += check_books(tk)
    if not check_only:
        (ROOT / 'stats.json').write_text(json.dumps(st, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(st, ensure_ascii=False))
    if problems:
        print('\n'.join(problems))
        sys.exit(1)


if __name__ == '__main__':
    main()
