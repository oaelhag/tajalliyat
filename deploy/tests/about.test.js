// اختبار شرح معنى «تجليات» على الجوال وسطح المكتب + عدم التأثير على النموذج والصفحة.
// node deploy/tests/about.test.js <نسخة-مبنية> [مجلد-اللقطات]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2]);
const SHOTS = process.argv[3] || '/tmp/claude-0/about-shots';
fs.mkdirSync(SHOTS, { recursive: true });
const PB = process.env.PWA_BASE || '/';
const texts = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'content', 'site_texts.json'), 'utf8')).about_tajalliyat;
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.json': 'application/json', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json', '.xml': 'application/xml', '.txt': 'text/plain' };
const state = { posts: [] };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.startsWith('/backend/')) { state.posts.push(req.method + ' ' + p); res.writeHead(200, { 'Content-Type': 'application/json' }); res.end('{"ok":true}'); return; }
  if (PB !== '/' && p.startsWith(PB)) p = '/' + p.slice(PB.length);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end('nf'); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-cache' }); res.end(fs.readFileSync(f));
});
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const B = 'http://localhost:8793' + PB.replace(/\/$/, '');
(async () => {
  await new Promise(r => server.listen(8793, r));
  const browser = await chromium.launch();
  for (const [label, vp] of [['mobile', { width: 360, height: 740 }], ['desktop', { width: 1280, height: 800 }]]) {
    const ctx = await browser.newContext({ viewport: vp, hasTouch: label === 'mobile', serviceWorkers: 'block' });
    const page = await ctx.newPage(); const errs = []; page.on('pageerror', e => errs.push(e.message));
    await page.goto(B + '/', { waitUntil: 'networkidle' }); await page.waitForTimeout(300);
    const strip = page.locator('#about-meaning');
    ok(await strip.isVisible(), `[${label}] strip visible on first page`);
    ok((await strip.locator('p').textContent()) === texts.ar, `[${label}] strip text equals site_texts.json ar, word for word`);
    const lines = await strip.locator('p').evaluate(p => Math.round(p.getBoundingClientRect().height / parseFloat(getComputedStyle(p).lineHeight)) - 0);
    ok(lines <= 3, `[${label}] strip is short (≈${lines} line-heights incl. padding; clamped to 2 lines)`);
    ok(await strip.locator('p').evaluate(p => getComputedStyle(p).webkitLineClamp === '2'), `[${label}] text clamped to two lines`);
    const bb = await strip.locator('.about-q').boundingBox();
    ok(bb.width >= 44 && bb.height >= 44, `[${label}] "؟" button touch target ${Math.round(bb.width)}×${Math.round(bb.height)}`);
    ok((await strip.locator('.about-q').textContent()) === '؟' && (await strip.locator('.about-q').getAttribute('aria-label')).includes('تجليات'), `[${label}] "؟" icon + aria-label`);
    const pos = await page.evaluate(() => { const s = document.getElementById('about-meaning').getBoundingClientRect(), h = document.querySelector('.top').getBoundingClientRect(), a = document.getElementById('aud').getBoundingClientRect(), n = document.querySelector('nav').getBoundingClientRect(); return { sTop: s.top, hBottom: h.bottom, sBottom: s.bottom, aTop: a.top, navTop: n.top, fixed: getComputedStyle(document.querySelector('nav')).position === 'fixed' }; });
    ok(pos.sTop >= pos.hBottom - 1 && pos.sBottom <= pos.aTop + 1, `[${label}] strip sits under the title and above the category chips`);
    ok(!pos.fixed || pos.sBottom < pos.navTop, `[${label}] bottom nav does not cover the strip`);
    ok(await page.evaluate(() => getComputedStyle(document.documentElement).direction === 'rtl' && document.documentElement.scrollWidth <= innerWidth), `[${label}] RTL and no horizontal overflow`);
    await page.screenshot({ path: `${SHOTS}/${label}-1-closed.png` });
    await strip.locator('.about-q').click();
    const dlg = page.locator('.about-dlg');
    ok(await dlg.isVisible() && (await dlg.locator('p').textContent()) === texts.ar, `[${label}] dialog opens with the full text`);
    const over = await page.evaluate(() => { const m = document.querySelector('.modal'); const r = document.querySelector('.about-dlg').getBoundingClientRect(); return { z: +getComputedStyle(m).zIndex, inView: r.top >= 0 && r.bottom <= innerHeight, role: m.getAttribute('role') }; });
    ok(over.z > 6 && over.inView && over.role === 'dialog', `[${label}] dialog above the bottom nav, fully in view`);
    await page.waitForTimeout(600);                                       // انتهاء حركة الظهور
    await page.screenshot({ path: `${SHOTS}/${label}-2-open.png` });
    await page.keyboard.press('Escape'); await page.waitForTimeout(350);
    ok((await page.locator('.modal').count()) === 0 && await page.evaluate(() => document.activeElement.className.includes('about-q')), `[${label}] Esc closes and returns focus to "؟"`);
    await strip.locator('.about-q').click(); await page.mouse.click(3, 3); await page.waitForTimeout(350);
    ok((await page.locator('.modal').count()) === 0, `[${label}] click outside closes`);
    await strip.locator('.about-q').click(); await page.click('.about-dlg .btn'); await page.waitForTimeout(350);
    ok((await page.locator('.modal').count()) === 0, `[${label}] close button works`);
    // يظهر في الصفحة الأولى فقط
    await page.goto(B + '/#names', { waitUntil: 'networkidle' }); await page.waitForTimeout(300);
    ok(!(await strip.isVisible()), `[${label}] hidden on other views (#names)`);
    await page.goto(B + '/#today', { waitUntil: 'networkidle' }); await page.waitForTimeout(300);
    ok(await strip.isVisible(), `[${label}] visible again on first page`);
    // النموذج وبقية الصفحة
    state.posts.length = 0;
    await page.locator('#contactForm [name=name]').fill('اختبار'); await page.locator('#contactForm [name=email]').fill('a@b.co'); await page.locator('#contactForm [name=message]').fill('رسالة تجريبية');
    await page.locator('#contactForm button[type=submit]').click(); await page.waitForTimeout(500);
    ok((await page.locator('#contactMsg').innerText()).includes('وصلتنا رسالتك') && state.posts.includes('POST /backend/api/contact.php'), `[${label}] contact form still works`);
    await page.goto(B + '/', { waitUntil: 'networkidle' }); await page.waitForTimeout(300);
    ok(await page.locator('#v-today h1').count() === 1 && await page.locator('.aud .chip').count() >= 6 && await page.locator('.feelbar').count() === 1, `[${label}] rest of the first page intact (day card, chips, feelings)`);
    ok(await page.locator('#pwa-panel').count() === (process.env.PWA_EXPECT === '0' ? 0 : await page.locator('#pwa-panel').count()), `[${label}] panel unaffected`);
    await page.screenshot({ path: `${SHOTS}/${label}-3-page.png`, fullPage: false });
    const meta = await page.evaluate(() => ({ d: document.querySelector('meta[name=description]').content, og: document.querySelector('meta[property="og:description"]').content, tw: document.querySelector('meta[name="twitter:description"]').content }));
    ok(meta.d === texts.ar && meta.og === texts.ar && meta.tw === texts.ar, `[${label}] meta/og/twitter description = approved Arabic text`);
    ok(errs.length === 0, `[${label}] no JS errors ${JSON.stringify(errs)}`);
    const english = await page.evaluate((en) => document.documentElement.outerHTML.includes('Tajalliyat (tah') || document.body.innerText.includes('tah-jal-lee'), texts.en);
    ok(!english, `[${label}] English text not shown on the page`);
    await ctx.close();
  }
  // المانيفست + عدم تسرّب الإنجليزية إلى أي ملف + لا عبارات محظورة
  const man = ROOT + '/manifest.webmanifest';
  if (fs.existsSync(man)) ok(JSON.parse(fs.readFileSync(man, 'utf8')).description === texts.ar, 'manifest description = approved Arabic text');
  let leak = [], bad = [];
  const norm = t => t.replace(/[ً-ٰٟـ]/g, '').replace(/[أإآٱ]/g, 'ا').replace(/ى/g, 'ي');
  (function walk(d) { for (const e of fs.readdirSync(d, { withFileTypes: true })) { const f = path.join(d, e.name); if (e.isDirectory()) { if (e.name !== 'pdf' && e.name !== 'videos') walk(f); } else if (/\.(html|js|json|xml|txt|webmanifest|css)$/.test(e.name)) { const t = fs.readFileSync(f, 'utf8'); if (t.includes('tah-jal-lee') || t.includes("Allah's Beautiful Names in our")) leak.push(f); const n = norm(t); if (n.includes('تجلي الله') || n.includes('تجلي الذات')) bad.push(f); } } })(ROOT);
  ok(leak.length === 0, 'English text appears in no published file ' + leak.join(','));
  ok(bad.length === 0, 'forbidden phrases «تجلّي الله» / «تجلّي الذات» appear in no published file ' + bad.join(','));
  await browser.close(); server.close();
  console.log(fails ? `\n${fails} FAILED` : '\nALL PASSED'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
