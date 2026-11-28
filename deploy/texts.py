#!/usr/bin/env python3
"""مصدر واحد لنصوص الموقع المعتمدة (deploy/content/site_texts.json) + فحص القاعدة اللغوية.

القاعدة: لا تُستعمل عبارتا «تجلّي الله» و«تجلّي الذات» في أي نص جديد. المعنى المعتمد هو «آثار الأسماء التي نلاحظها».
الفحص:  python3 deploy/texts.py --check
"""
import json, pathlib, re, sys

CONTENT = pathlib.Path(__file__).parent / 'content'
FORBIDDEN = ['تجلّي الله', 'تجلّي الذات']


def norm(t):
    """يوحّد الرسم قبل المقارنة: يحذف التشكيل والتطويل، ويوحّد الألف والياء."""
    t = re.sub('[ً-ٰٟـ]', '', t)
    t = re.sub('[أإآٱ]', 'ا', t).replace('ى', 'ي')
    return re.sub(r'\s+', ' ', t)


def lint(text, where=''):
    n = norm(text)
    for bad in FORBIDDEN:
        if norm(bad) in n:
            raise SystemExit(f'texts: العبارة المحظورة «{bad}» وردت في {where or "نص"}؛ المعنى المعتمد: آثار الأسماء التي نلاحظها.')


def _load(name):
    return json.loads((CONTENT / name).read_text(encoding='utf-8'))


def ar(key):
    """النص العربي المعتمد لمفتاح؛ يفشل إن لم يكن status = approved."""
    e = _load('site_texts.json').get(key)
    if not isinstance(e, dict) or not e.get('ar'):
        raise SystemExit(f'texts: المفتاح غير موجود: {key}')
    if e.get('status') != 'approved':
        raise SystemExit(f'texts: النص «{key}» غير معتمد (status={e.get("status")})')
    lint(e['ar'], key)
    return e['ar']


def en(key):
    """النص الإنجليزي: للمترجمين فقط؛ لا يُعرض في أي صفحة الآن."""
    return _load('site_texts.json')[key]['en']


def check_all():
    st = _load('site_texts.json')
    for k, v in st.items():
        if isinstance(v, dict):
            assert v.get('status') in ('approved', 'draft'), f'{k}: status غير صالح'
            for lang in ('ar', 'en'):
                assert v.get(lang), f'{k}: الحقل {lang} ناقص'
                lint(v[lang], f'{k}.{lang}')
    g = _load('glossary.json')
    seen = set()
    for t in g['terms']:
        assert t['status'] in ('approved', 'draft') and t['ar'] and t['en'], f'مصطلح ناقص: {t}'
        assert t['ar'] not in seen, f'مصطلح مكرر: {t["ar"]}'
        seen.add(t['ar'])
        lint(t['ar'] + ' ' + t['en'], 'glossary')
        if t['status'] == 'approved':
            assert t.get('source'), f'مصطلح معتمد بلا مصدر: {t["ar"]}'
    return len(st) - 1, len(g['terms'])


if __name__ == '__main__':
    if '--check' in sys.argv:
        n, m = check_all()
        print(f'texts: OK ({n} text keys, {m} glossary terms)')
