// يعيد توليد ملفات pdf/<id>-<group>.pdf من صفحات print/*.html في النسخة المبنية،
// بنفس طريقة الأداة الأصلية (source/tools/render.js: A4 + printBackground + preferCSSPageSize)،
// حتى يظهر عنوان الموقع الجديد في التذييل بدل عنوان GitHub القديم.
// الاستعمال: node deploy/gen_pdfs.js <مجلد-الإخراج>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const OUT = path.resolve(process.argv[2]);
const dir = path.join(OUT, 'print');
const files = fs.readdirSync(dir).filter(f => f.endsWith('.html')).sort();
fs.mkdirSync(path.join(OUT, 'pdf'), { recursive: true });
(async () => {
  const b = await chromium.launch();
  const bad = [];
  let next = 0;
  const worker = async () => {
    const p = await b.newPage();
    while (next < files.length) {
      const f = files[next++];
      await p.goto('file://' + path.join(dir, f));
      await p.evaluate(() => document.fonts.ready);
      const out = path.join(OUT, 'pdf', f.replace(/\.html$/, '.pdf'));
      await p.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true });
      const pages = (fs.readFileSync(out, 'latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
      if (pages !== 4) bad.push(f + ':' + pages);
    }
    await p.close();
  };
  await Promise.all([worker(), worker(), worker(), worker()]);
  await b.close();
  console.log('gen_pdfs: ' + files.length + ' PDFs; not 4 pages: ' + (bad.join(' ') || 'none'));
  if (bad.length) process.exit(1);
})();
