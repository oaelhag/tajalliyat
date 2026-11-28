// واجهة الجوال الصغير (240px مثل Jelly Pro) و360px: مشاركة مدمجة، حذف نموذج جوجل، لوحة التثبيت.
// node deploy/tests/ui.test.js <نسخة-مبنية> [مجلد-اللقطات]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2]);
const SHOTS = process.argv[3] || '/tmp/claude-0/ui-shots';
fs.mkdirSync(SHOTS, { recursive: true });
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.json': 'application/json', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json', '.xml': 'application/xml', '.txt': 'text/plain' };
const posts = [];
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.startsWith('/backend/')) { posts.push(req.method + ' ' + p); res.writeHead(200, { 'Content-Type': 'application/json' }); res.end('{"ok":true}'); return; }
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end('nf'); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-cache' }); res.end(fs.readFileSync(f));
});
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const B = 'http://localhost:8797';
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await new Promise(r => server.listen(8797, r));
  const home = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  ok(!/docs\.google\.com|forms\.gle|google\.com\/forms/.test(home), 'no Google Form / Docs reference left in the home page');
  const browser = await chromium.launch();
  for (const [label, vp] of [['w240', { width: 240, height: 432 }], ['w360', { width: 360, height: 740 }]]) {
    const ctx = await browser.newContext({ viewport: vp, hasTouch: true, serviceWorkers: 'block' });
    const page = await ctx.newPage(); const errs = []; page.on('pageerror', e => errs.push(e.message));
    await page.goto(B + '/', { waitUntil: 'networkidle' }); await wait(500);
    ok((await page.locator('iframe').count()) === 0 && (await page.locator('.contact').count()) === 0 && (await page.locator('#contactForm').count()) === 1, `[${label}] old Google contact block is gone; our own form remains`);
    // مشاركة مدمجة
    ok((await page.locator('#v-today .shbtn').count()) >= 3, `[${label}] day card has compact share buttons (day tajalli, ayah, question)`);
    ok((await page.locator('#v-today .share:visible').count()) === 0, `[${label}] no full row of 3 share pills is visible any more`);
    const geo = await page.evaluate(() => {
      const r = document.querySelector('#v-today .rowshare'); const p = r.querySelector('p').getBoundingClientRect(), b = r.querySelector('.shbtn').getBoundingClientRect();
      const a = document.querySelector('#v-today .ayah .shbtn').getBoundingClientRect();
      return { sameLine: b.top >= p.top - 2 && b.top < p.bottom, bw: b.width, bh: b.height, ayahH: a.height, overflowX: document.documentElement.scrollWidth > innerWidth };
    });
    ok(geo.sameLine && geo.bw >= 40 && geo.bh >= 40, `[${label}] share button sits on the same line as the text (${Math.round(geo.bw)}×${Math.round(geo.bh)})`);
    ok(!geo.overflowX, `[${label}] no horizontal overflow`);
    await page.screenshot({ path: `${SHOTS}/${label}-1-today.png` });
    for (const sel of ['#v-today .rowshare .shbtn', '#v-today .ayah .shbtn', '#v-today .trio .shbtn']) {
      const btn = page.locator(sel).first(); await btn.scrollIntoViewIfNeeded(); await btn.click(); await wait(250);
      const m = await page.evaluate(() => { const e = document.querySelector('.shwrap.open .shmenu'); if (!e) return null; const r = e.getBoundingClientRect(); const hdr = document.querySelector('.top').getBoundingClientRect().bottom; const nv = document.querySelector('nav'); const navTop = nv && getComputedStyle(nv).position === 'fixed' ? nv.getBoundingClientRect().top : innerHeight; return { n: e.querySelectorAll('button,a').length, l: r.left, r: r.right, w: innerWidth, b: r.bottom, t: r.top, navTop, hdr }; });
      ok(m && m.n === 3 && m.l >= 0 && m.r <= m.w && m.b <= m.navTop + 1 && m.t >= m.hdr - 1, `[${label}] ${sel.split(' ').slice(-2).join(' ')}: menu has 3 options and stays inside the screen, between the top bar and the bottom bar`);
      if (sel.includes('rowshare')) await page.screenshot({ path: `${SHOTS}/${label}-2-share-menu.png` });
      await page.keyboard.press('Escape'); await wait(150);
    }
    // اللوحة: مطوية، في الصفحة الأولى فقط
    const panel = page.locator('#pwa-panel');
    ok((await panel.count()) === 1 && !(await panel.evaluate(d => d.open)), `[${label}] install panel is collapsed by default`);
    const sh = await panel.locator('summary').boundingBox();
    ok(sh && sh.height >= 44 && sh.height < 70, `[${label}] collapsed panel is one touch-sized line (${Math.round(sh.height)}px)`);
    await panel.scrollIntoViewIfNeeded(); await page.screenshot({ path: `${SHOTS}/${label}-3-panel-collapsed.png` });
    await panel.locator('summary').click(); await wait(200);
    ok(await page.locator('#pwa-install').isVisible(), `[${label}] tapping the line reveals the install button`);
    await page.screenshot({ path: `${SHOTS}/${label}-4-panel-open.png` });
    for (const h of ['#names', '#feel', '#journey', '#feel-sad', '#name-rahman']) {
      await page.evaluate(x => { location.hash = x; }, h); await wait(350);
      ok(!(await panel.isVisible()), `[${label}] panel hidden on ${h}`);
    }
    await page.evaluate(() => { location.hash = '#today'; }); await wait(350);
    ok(await panel.isVisible(), `[${label}] panel visible again on the first page`);
    // نموذج التواصل
    posts.length = 0;
    await page.locator('#contactForm [name=name]').fill('اختبار'); await page.locator('#contactForm [name=email]').fill('a@b.co'); await page.locator('#contactForm [name=message]').fill('رسالة');
    await page.locator('#contactForm button[type=submit]').click(); await wait(500);
    ok((await page.locator('#contactMsg').innerText()).includes('وصلتنا رسالتك') && posts.includes('POST /backend/api/contact.php'), `[${label}] contact form works`);
    // الصفحات الأخرى: لا لوحة
    for (const u of ['/guide.html', '/athar.html']) { await page.goto(B + u, { waitUntil: 'networkidle' }); await wait(300); ok((await page.locator('#pwa-panel').count()) === 0, `[${label}] no install panel on ${u}`); }
    // شاشة المشاعر: تبقى القائمة والرابط يعملان
    await page.goto(B + '/#feel', { waitUntil: 'networkidle' }); await wait(400);
    await page.screenshot({ path: `${SHOTS}/${label}-5-feel.png` });
    ok(errs.length === 0, `[${label}] no JS errors ${JSON.stringify(errs)}`);
    await ctx.close();
  }
  await browser.close(); server.close();
  console.log(fails ? `\n${fails} FAILED` : '\nALL PASSED'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
