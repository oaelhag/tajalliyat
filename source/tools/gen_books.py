#!/usr/bin/env python3
"""يولّد القارئ التفاعلي لكل كتاب (books/<id>/index.html) وصفحة المكتبة (books/index.html)
من source/books/book_<id>.md.  التشغيل من جذر المستودع:  python3 source/tools/gen_books.py"""
import re,json,html,sys,pathlib,markdown
ROOT=pathlib.Path(__file__).resolve().parents[2]
SITE='https://oaelhag.github.io/tajalliyat'
BOOKS={
 'youth':dict(title='دليل الشاب',pdf='dalil-alshab',who='للشاب',
   desc='اثنان وأربعون اسماً من أسماء الله الحسنى في مواقف الحياة: الخوف والقرار والرزق والضعف والفقد والذنب والخلاف.',
   parts=[('أنا والقرار',[1,2,3],'أنا، وخوفي، وقراري'),('الرزق والضعف والضيق',[4,5,6],'العمل، والضعف، وضيق الحال'),('الفقد والصحبة والذنب',[7,8,9],'فقدٌ وصحبة وعودة'),('الخلاف والإحسان',[10,11],'ظلمٌ وغضب وبرّ')]),
 'father':dict(title='دليل الأب',pdf='dalil-alab',who='للأب',
   desc='اثنان وأربعون اسماً من أسماء الله الحسنى في مواقف البيت: الأولاد والرزق والغضب والقدوة والقلق والفقد والشكر.',
   parts=[('البيت والأمانة',[1,2,3],'أولاد، وحضور، وغضب'),('الرزق والقدوة والتربية',[4,5,6],'الرزق، والقدوة، والقرار والدعاء'),('العودة والقلق والضيق',[7,8,9],'اعتذار، وقلق، وضيق حال'),('الفقد والشكر',[10,11],'فقدٌ وشكر وختام')]),
}
AR=str.maketrans('0123456789','٠١٢٣٤٥٦٧٨٩'); FR=str.maketrans('٠١٢٣٤٥٦٧٨٩','0123456789')
def ar(n): return str(n).translate(AR)
def esc(s): return html.escape(s,quote=True)
BACK={'خاتمة':('end','خاتمة'),'ملحق أ':('app-a','أ'),'ملحق ب':('app-b','ب'),'ملحق ج':('app-c','ج'),'ملحق د':('app-d','د'),'ملحق هـ':('app-e','هـ')}
MDX=lambda t: markdown.markdown(t,extensions=['tables','sane_lists'])

def body_html(md,chnum=None):
    b=MDX(md)
    b=re.sub(r'<hr\s*/?>','',b)
    def h2(m):
        x=m.group(1)
        cls={'مدخل الفصل':'intro','مراجعة الفصل':'rev'}.get(x) or ('shid' if x.startswith('وقت الشدة') else 'nm')
        return f'<h2 class="{cls}">{x}</h2>'
    b=re.sub(r'<h2>(.+?)</h2>',h2,b)
    cmap={'لاحِظ':'look','جرّب':'try','دوّن أثرك':'note','احفظ':'keep','المعنى':'mean'}
    def sec(m):
        h,x=m.group(1),m.group(2); c=cmap.get(h.strip(),'stn')
        return f'<div class="box {c}"><h3>{h}</h3>{x}</div>'
    b=re.sub(r'<h3>(.+?)</h3>(.*?)(?=<h3>|<h2|<h1|$)',sec,b,flags=re.S)
    b=b.replace('<p><strong>في الموقع:</strong>','<p class="now"><strong>في الموقع:</strong>')
    b=b.replace('<p><strong>موقف:</strong>','<p class="scene"><strong>موقف:</strong>').replace('<p><strong>السؤال:</strong>','<p class="ask"><strong>السؤال:</strong>').replace('<p><strong>سؤال الفصل:</strong>','<p class="ask"><strong>سؤال الفصل:</strong>')
    for k,c in (('تجلٍّ ظاهر','s1'),('تجلٍّ خفي','s2'),('المقلوب','s3')):
        b=b.replace(f'<p><strong>{k}:</strong>',f'<p class="st {c}"><strong>{k}</strong>')
    b=re.sub(r'(«[^»]{4,300}»)(\s*\((?:[^()٠-٩0-9<]+)\s+[٠-٩0-9]+\))',r'<span class="q">\1</span>\2',b)
    b=re.sub(r'<p>(<strong>«.*?)</p>',r'<p class="verse">\1</p>',b)
    # وقت الشدة ومراجعة الفصل
    b=re.sub(r'<h2 class="shid">(.+?)</h2>(.*?)(?=<h2 class="rev">|$)',r'<div class="shidbox"><h2 class="shid">\1</h2>\2</div>',b,flags=re.S)
    b=re.sub(r'<h2 class="rev">(.+?)</h2>(.*)$',r'<div class="revbox"><h2 class="rev">\1</h2>\2</div>',b,flags=re.S)
    return b

def names_pass(b,bk):
    """يلفّ كل اسم في section ويحوّل الحقول إلى عناصر تفاعلية."""
    chunks=re.split(r'(?=<h2 class="nm">)',b)
    out=[chunks[0]]; names=[]
    for ch in chunks[1:]:
        # آخر قطعة قد تتضمن shidbox/revbox بعد الاسم الأخير: افصلها
        tail=''
        m=re.search(r'<div class="shidbox">',ch)
        if m: ch,tail=ch[:m.start()],ch[m.start():]
        mid=re.search(r'<code>n/(\w+)/</code>',ch); nid=mid.group(1) if mid else None
        title=re.match(r'<h2 class="nm">(.+?)</h2>',ch).group(1)
        # ملاحظات: textarea
        def notes(m):
            lis=re.findall(r'<li>(.*?)</li>',m.group(0),flags=re.S)
            items=''.join(f'<div class="nq"><label for="t-{nid}-{i}">{i}. {q}</label><textarea id="t-{nid}-{i}" data-note="{nid}-{i}" data-q="{esc(re.sub("<[^>]+>","",q))}" data-name="{esc(re.sub("<[^>]+>","",title))}" rows="3" placeholder="اكتب هنا… (تُحفظ على جهازك فقط)"></textarea></div>' for i,q in enumerate(lis,1))
            return f'<div class="box note"><h3>دوّن أثرك</h3>{items}<p class="small">تُحفظ كتابتك على هذا الجهاز وفي هذا المتصفح فقط، ولا تُرسل إلى أي خادم.</p></div>'
        ch=re.sub(r'<div class="box note">.*?</div>(?=\s*(?:<div class="box|$))',notes,ch,flags=re.S)
        # جرّب: خانة أنجزت
        ch=re.sub(r'(<div class="box try"><h3>جرّب</h3>)(.*?)(</div>)',lambda m:f'{m.group(1)}{m.group(2)}<label class="done"><input type="checkbox" data-task="{nid}"> أنجزتُ مهمة هذا الأسبوع</label>{m.group(3)}',ch,flags=re.S)
        # ما يُنقل: استبدله برابط صفحة الاسم
        def now(m):
            fm=re.search(r'يناسب من يشعر بـ: ([^.<]+)\.',m.group(0)); ft=f'يناسب من يشعر بـ: {fm.group(1)}.<br>' if fm else ''
            return f'<p class="now">{ft}<a class="btn" href="../../n/{nid}/">افتح صفحة الاسم</a> <a class="btn" href="../../athar.html">أثر الاسم في حياتي</a></p>'
        ch=re.sub(r'<p class="now">.*?</p>',now,ch,flags=re.S)
        ch=ch.replace('<p class="now">','<p class="now">') 
        out.append(f'<section class="name" id="n-{nid}" data-name="{esc(re.sub("<[^>]+>","",title))}">{ch}</section>'+tail)
        names.append((nid,re.sub('<[^>]+>','',title)))
    return ''.join(out),names

def build_book(bk):
    cfg=BOOKS[bk]
    t=(ROOT/f'source/books/book_{bk}.md').read_text(encoding='utf-8')
    cover,rest=t.split('\n---\n',1)
    blocks=re.split(r'(?m)^(?=# )',rest)
    front_md,blocks=blocks[0],blocks[1:]
    arts=[]; toc=[]  # arts: (id,title,html,part)
    chap_meta={}
    # الواجهة الأمامية
    fb=body_html(front_md)
    # روابط الفصول في جدول «ابدأ من شعورك»
    def link_chs(m):
        cell=m.group(1)
        nums=re.split(r'[،,]\s*',cell.strip())
        return '<td>'+'، '.join(f'<a href="#c{n.translate(FR)}">{n}</a>' if n.translate(FR).isdigit() else n for n in nums)+'</td>'
    fb=re.sub(r'<td>([٠-٩، ]+)</td>',link_chs,fb)
    arts.append(('front','مدخل الكتاب',f'<header class="hero"><p class="kicker">تجليات الأسماء</p><h1>{cfg["title"]}</h1><p class="sub">{cfg["desc"]}</p><p class="by">المطوّر: أسامة عبد الهادي الهاجري</p><p class="row"><a class="btn main" href="#c1">ابدأ القراءة</a><a class="btn" href="../pdf/{cfg["pdf"]}-screen.pdf" download>تنزيل PDF</a><a class="btn quiet" href="../">كل الكتب</a></p></header>{fb}',0))
    for b in blocks:
        h=re.match(r'# (.+)',b).group(1); md=re.sub(r'(?m)^# .+\n','',b,count=1)
        m=re.match(r'الفصل\s+([٠-٩]+)\s*:\s*(.+)',h)
        if m:
            n=int(m.group(1).translate(FR)); title=m.group(2).strip()
            pi=next(i for i,p in enumerate(cfg['parts']) if n in p[1])+1
            bh,names=names_pass(body_html(md,n),bk)
            bh=bh.replace('<h2 class="intro">مدخل الفصل</h2>','')
            hdr=f'<header class="chead"><span class="badge">{ar(n)}</span><div><p class="kicker">الجزء {ar(pi)} ▪ {esc(cfg["parts"][pi-1][0])}</p><h1>{title}</h1></div></header>'
            arts.append((f'c{n}',title,hdr+bh,pi)); chap_meta[n]=(title,names,pi)
        else:
            key=next((k for k in BACK if h.startswith(k)),None)
            aid=BACK[key][0] if key else 'x'
            bh=body_html(md)
            if aid=='app-b':
                # الفصل في فهرس الأسماء رابط
                bh=re.sub(r'<td>([٠-٩]+)</td>',lambda m:f'<td><a href="#c{m.group(1).translate(FR)}">{m.group(1)}</a></td>',bh)
            if aid=='app-e':
                bh=re.sub(r'<td>([٠-٩]+)</td>(?=</tr>)',lambda m:f'<td><a href="#c{m.group(1).translate(FR)}">{m.group(1)}</a></td>',bh)
            arts.append((aid,h,f'<header class="chead plain"><div><p class="kicker">في آخر الكتاب</p><h1>{h}</h1></div></header>{bh}',5))
    # الفهرس
    tl=['<p class="tocsearch"><label for="q" class="sr">بحث في الكتاب</label><input id="q" type="search" placeholder="ابحث في الكتاب…" autocomplete="off"></p><div id="results" aria-live="polite"></div><div id="tocbody">',
        '<a class="tocrow" data-go="front" href="#front"><span>مدخل الكتاب</span></a>']
    for i,(pn,chs,sub) in enumerate(cfg['parts'],1):
        tl.append(f'<div class="tpart" data-part="{i}"><b>الجزء {ar(i)}</b> {pn}</div>')
        for n in chs:
            title,names,_=chap_meta[n]
            nl=''.join(f'<a class="tn" data-go="n-{nid}" href="#n-{nid}">{nm}</a>' for nid,nm in names)
            tl.append(f'<div class="tch" data-part="{i}"><a class="tocrow" data-go="c{n}" href="#c{n}"><span class="cn">{ar(n)}</span><span>{title}</span><span class="ck" aria-hidden="true"></span></a><div class="tnames">{nl}</div></div>')
    tl.append('<div class="tpart" data-part="5"><b>في آخر الكتاب</b></div>')
    for aid,title,_,_ in arts:
        if aid in ('end','app-a','app-b','app-c','app-d','app-e'): tl.append(f'<a class="tocrow" data-go="{aid}" href="#{aid}"><span>{title}</span></a>')
    tl.append('<a class="tocrow" data-go="notes" href="#notes"><span>ملاحظاتي</span></a></div>')
    sections=''.join(f'<article class="art" id="{aid}" data-part="{p}" data-title="{esc(t)}" hidden>{h}</article>' for aid,t,h,p in arts)
    page=f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{cfg["title"]} | تجليات الأسماء</title>
<meta name="description" content="{esc(cfg["desc"])} كتاب مجاني للقراءة هنا أو للتنزيل PDF.">
<link rel="canonical" href="{SITE}/books/{bk}/">
<meta property="og:type" content="book"><meta property="og:locale" content="ar_AR"><meta property="og:site_name" content="تجليات الأسماء"><meta property="og:title" content="{cfg["title"]} | تجليات الأسماء"><meta property="og:description" content="{esc(cfg["desc"])}"><meta property="og:image" content="{SITE}/books/img/cover-{bk}.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:,">
<link rel="stylesheet" href="../../assets/fonts/fonts.css"><link rel="stylesheet" href="../reader.css">
</head><body data-book="{bk}" data-title="{cfg["title"]}" data-pdf="{cfg["pdf"]}">
<a class="skip" href="#main">انتقل إلى المحتوى</a>
<header class="bar"><button class="ibtn" id="tocBtn" aria-expanded="false" aria-controls="toc" aria-label="الفهرس">☰</button><a class="bt" href="#front"><b>{cfg["title"]}</b></a><span class="sp"></span><button class="ibtn" id="setBtn" aria-expanded="false" aria-controls="settings" aria-label="إعدادات القراءة">Aa</button><div class="prog" aria-hidden="true"><i id="progBar"></i></div></header>
<div id="settings" class="pop" hidden><p><b>حجم الخط</b></p><div class="row"><button class="btn" id="fsDown" aria-label="تصغير الخط">أ−</button><button class="btn" id="fsUp" aria-label="تكبير الخط">أ+</button></div><p><b>المظهر</b></p><div class="row"><button class="btn" data-theme="light" aria-pressed="false">فاتح</button><button class="btn" data-theme="sepia" aria-pressed="false">دافئ</button><button class="btn" data-theme="dark" aria-pressed="false">ليلي</button></div><p><b>تنزيل الكتاب</b></p><div class="col"><a class="btn" href="../pdf/{cfg["pdf"]}-screen.pdf" download>PDF بالألوان (للشاشة)</a><a class="btn" href="../pdf/{cfg["pdf"]}-print.pdf" download>PDF للطباعة</a></div></div>
<aside id="toc" class="drawer" hidden aria-label="الفهرس"><div class="dh"><b>الفهرس</b><button class="ibtn" id="tocClose" aria-label="إغلاق">✕</button></div><div class="progtxt" id="progTxt"></div>{''.join(tl)}</aside>
<div id="scrim" hidden></div>
<main id="main" tabindex="-1">{sections}<article class="art" id="notes" data-part="5" data-title="ملاحظاتي" hidden></article><nav class="pn" id="pn" aria-label="التنقل بين الفصول"></nav></main>
<footer class="foot"><p>{cfg["title"]} من موقع «تجليات الأسماء». المطوّر: أسامة عبد الهادي الهاجري. نسخة مجانية للقراءة والمشاركة بلا تعديل.</p><p><a href="../">كل الكتب</a> · <a href="../../">الموقع</a></p></footer>
<script src="../reader.js"></script></body></html>'''
    (ROOT/f'books/{bk}').mkdir(parents=True,exist_ok=True)
    (ROOT/f'books/{bk}/index.html').write_text(page,encoding='utf-8')
    return len(page),len(arts)

def build_library():
    cards=''
    for bk,c in BOOKS.items():
        cards+=f'''<article class="bk"><a class="cv" href="{bk}/"><img src="img/cover-{bk}.jpg" alt="غلاف {c["title"]}" width="320" height="456" loading="lazy"></a><div class="bi"><h2><a href="{bk}/">{c["title"]}</a></h2><p>{c["desc"]}</p><p class="row"><a class="btn main" href="{bk}/">اقرأ هنا</a><a class="btn" href="pdf/{c["pdf"]}-screen.pdf" download>تنزيل PDF بالألوان</a><a class="btn" href="pdf/{c["pdf"]}-print.pdf" download>تنزيل PDF للطباعة</a></p><p class="small"><a href="pdf/{c["pdf"]}-screen.pdf" target="_blank" rel="noopener">فتح الـPDF في المتصفح</a></p></div></article>'''
    page=f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>كتب مجانية | تجليات الأسماء</title>
<meta name="description" content="كتابان مجانيان من «تجليات الأسماء»: دليل الشاب ودليل الأب. اقرأهما هنا بنسخة تفاعلية تتيح لك التدوين، أو نزّل ملف PDF للقراءة أو الطباعة.">
<link rel="canonical" href="{SITE}/books/"><meta property="og:type" content="website"><meta property="og:locale" content="ar_AR"><meta property="og:site_name" content="تجليات الأسماء"><meta property="og:title" content="كتب مجانية | تجليات الأسماء"><meta property="og:image" content="{SITE}/books/img/cover-youth.jpg">
<link rel="icon" href="data:,"><link rel="stylesheet" href="../assets/fonts/fonts.css"><link rel="stylesheet" href="reader.css"></head>
<body class="lib"><header class="bar"><a class="bt" href="../"><b>تجليات الأسماء</b></a><span class="sp"></span></header>
<main id="main"><h1>كتب مجانية</h1><p class="lead">كتابان يمشيان مع أسماء الله الحسنى في مواقف الحياة. في كل اسم معناه وآيته وحديثه، وموقف وأسئلة وخطوة صغيرة. اقرأ هنا، ودوّن ما يخطر لك (يُحفظ على جهازك فقط)، أو نزّل الملف.</p>{cards}
<p class="note">هذه الكتب للقراءة والتأمل، وليست مرجعاً شرعياً ولا طبياً ولا نفسياً. المطوّر: أسامة عبد الهادي الهاجري.</p></main>
<footer class="foot"><p><a href="../">الموقع الرئيسي</a></p></footer></body></html>'''
    (ROOT/'books/index.html').write_text(page,encoding='utf-8')

if __name__=='__main__':
    for bk in BOOKS: print(bk,build_book(bk))
    build_library()
