// يرسم صور المعاينة (og/*.jpg بقياس 1200×630) والأيقونات باستعمال Playwright.
// الاستعمال: node deploy/gen_images.js <مجلد-الإخراج>   (يقرأ _img_jobs.json الذي ولّده gen_seo.py)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const OUT = path.resolve(process.argv[2]);
const jobs = JSON.parse(fs.readFileSync(path.join(OUT, '_img_jobs.json'), 'utf8'));
const font = n => `file://${OUT}/assets/fonts/${n}`;
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
// نفس تصميم البطاقات الأصلية (source/tools/render.js) لكن بالدومين الجديد
const css = `@font-face{font-family:Kufi;src:url(${font('reem-kufi-arabic-700-normal.woff2')});font-weight:700}
@font-face{font-family:Naskh;src:url(${font('noto-naskh-arabic-arabic-600-normal.woff2')});font-weight:600}
@font-face{font-family:Plex;src:url(${font('ibm-plex-sans-arabic-arabic-500-normal.woff2')});font-weight:500}
*{margin:0;box-sizing:border-box}body{width:1200px;height:630px;background:#0E1324;color:#E9E6DD;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;position:relative;direction:rtl}
.f{position:absolute;inset:24px;border:2px solid #E3B45C;opacity:.35;border-radius:8px}.f:after{content:"";position:absolute;inset:8px;border:1px solid #E3B45C;border-radius:5px}
.k{font:500 30px Plex;opacity:.75;letter-spacing:.04em;margin-bottom:18px}.n{font-weight:700;font-family:Kufi;color:#E3B45C;margin-top:0}.t{font:600 40px/1.6 Naskh;max-width:960px}.u{position:absolute;bottom:44px;font:500 24px Plex;opacity:.5;direction:ltr}
svg{width:70px;height:70px;color:#E3B45C;margin-bottom:6px}`;
const star = '<svg viewBox="0 0 64 64"><g fill="none" stroke="currentColor" stroke-width="2.2"><rect x="14" y="14" width="36" height="36"/><rect x="14" y="14" width="36" height="36" transform="rotate(45 32 32)"/></g></svg>';
const card = j => `<!doctype html><meta charset=utf-8><style>${css}</style><body><div class=f></div>${star}<div class=k>${esc(j.kick)}</div><div class=n style="font-size:${j.size}px;line-height:1.5">${esc(j.name)}</div><div class=t style="font-size:${j.tagSize || 40}px">${esc(j.tag)}</div><div class=u>tajalliyat.com</div>`;
const iconSvg = '<svg viewBox="0 0 64 64" width="100%" height="100%"><g fill="none" stroke="#E3B45C" stroke-width="2.6"><rect x="17" y="17" width="30" height="30"/><rect x="17" y="17" width="30" height="30" transform="rotate(45 32 32)"/></g></svg>';
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  const tmp = path.join(OUT, '_t.html');
  for (const j of jobs.og) {
    fs.writeFileSync(tmp, card(j));
    await p.goto('file://' + tmp);
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(80);
    fs.mkdirSync(path.dirname(path.join(OUT, j.path)), { recursive: true });
    await p.screenshot({ path: path.join(OUT, j.path), type: 'jpeg', quality: 84 });
  }
  const names = { 48: 'favicon-48.png', 180: 'apple-touch-icon.png', 192: 'icon-192.png', 512: 'icon-512.png' };
  for (const s of jobs.icons) {
    await p.setViewportSize({ width: s, height: s });
    fs.writeFileSync(tmp, `<!doctype html><meta charset=utf-8><body style="margin:0;background:#0E1324;width:${s}px;height:${s}px">${iconSvg}</body>`);
    await p.goto('file://' + tmp);
    await p.screenshot({ path: path.join(OUT, names[s]), type: 'png' });
  }
  fs.unlinkSync(tmp);
  await b.close();
  console.log('gen_images: ' + jobs.og.length + ' share images + ' + jobs.icons.length + ' icons');
})();
