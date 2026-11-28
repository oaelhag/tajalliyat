// اختبار PWA بـ Playwright على نسخة مبنية (PWA=1).  node deploy/tests/pwa.test.js <مجلد-النسخة-المبنية>
const { chromium, devices } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2]);
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.json': 'application/json', '.css': 'text/css', '.woff2': 'font/woff2',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json', '.xml': 'application/xml', '.txt': 'text/plain' };
const PB = process.env.PWA_BASE || '/';                 // '/' أو '/pwa-preview/'
const state = { v2: false, posts: [], gets: [] };
const server = http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x'); let p = decodeURIComponent(u.pathname);
  if (p.startsWith('/backend/')) {                                     // محاكاة الباك إند
    state.posts.push(req.method + ' ' + p);
    res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(req.method === 'POST' ? '{"ok":true}' : '{"ok":false,"error":"method_not_allowed"}'); return;
  }
  if (PB !== '/' && p.startsWith(PB)) p = '/' + p.slice(PB.length);
  if (p.endsWith('/')) p += 'index.html';
  let f = path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404, { 'Content-Type': 'text/html' }); res.end(fs.readFileSync(path.join(ROOT, '404.html'))); return; }
  let body = fs.readFileSync(f);
  if (p === '/sw.js' && state.v2) body = Buffer.from(body.toString().replace(/const VERSION = '[^']+'/, "const VERSION = 'testv2'"));
  res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-cache' }); res.end(body);
});
let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const B = 'http://localhost:8790' + PB.replace(/\/$/, '');
(async () => {
  await new Promise(r => server.listen(8790, r));
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 360, height: 740 }, acceptDownloads: true });
  const page = await ctx.newPage();
  const errs = []; page.on('pageerror', e => errs.push(e.message));

  // ── 1) تثبيت الـ SW وملء الكاش
  await page.goto(B + '/', { waitUntil: 'networkidle' });
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.waitForFunction(async () => (await caches.keys()).some(k => k.startsWith('shell-')) && (await caches.keys()).some(k => k.startsWith('data-')));
  const info = await page.evaluate(async () => {
    const out = { keys: await caches.keys(), urls: [] };
    for (const k of out.keys) for (const r of await (await caches.open(k)).keys()) out.urls.push(k.split('-')[0] + ' ' + new URL(r.url).pathname);
    return out;
  });
  const V = (info.keys.find(k => k.startsWith('shell-')) || '').slice(6);
  ok(!!V && info.keys.includes('data-' + V), 'cache names tied to build version (' + V + ')');
  ok(info.urls.includes('data ' + PB + 'data.js'), 'data.js precached in data cache');
  ok(['shell ' + PB, 'shell ' + PB + 'guide.html', 'shell ' + PB + 'athar.html', 'shell ' + PB + 'offline.html', 'shell ' + PB + 'assets/fonts/fonts.css'].every(x => info.urls.includes(x)), 'shell precache has pages, offline.html, fonts css');
  ok(!info.urls.some(u => /\/backend\/|\/videos\/|\/pdf\/|\.mp4|\.pdf/.test(u)), 'no backend/videos/pdf in any cache');

  // ── 2) offline
  await page.reload({ waitUntil: 'networkidle' });
  ok(await page.evaluate(() => !!navigator.serviceWorker.controller), 'page is controlled by the service worker');
  await page.goto(B + '/n/rahman/', { waitUntil: 'networkidle' });           // يُحفظ في كاش التشغيل
  await ctx.setOffline(true);
  await page.goto(B + '/', { waitUntil: 'domcontentloaded' });
  ok((await page.title()).includes('تجليات الأسماء') && (await page.locator('nav').count()) > 0, 'offline: home loads from cache');
  await page.waitForFunction(() => document.querySelectorAll('.card, .grid, h1, h2').length > 0, null, { timeout: 8000 }).catch(() => {});
  ok(await page.evaluate(() => !!window.ASMA && window.ASMA.length > 40), 'offline: data.js available (names rendered from cache)');
  await page.goto(B + '/guide.html', { waitUntil: 'domcontentloaded' }); ok((await page.title()).includes('اسم يناسب حالك'), 'offline: guide.html');
  await page.goto(B + '/athar.html', { waitUntil: 'domcontentloaded' }); ok((await page.title()).includes('أثر الاسم'), 'offline: athar.html');
  await page.goto(B + '/n/rahman/', { waitUntil: 'domcontentloaded' }); ok((await page.title()).includes('الرحمن'), 'offline: previously visited page from runtime cache');
  await page.goto(B + '/n/hakim/', { waitUntil: 'domcontentloaded' });
  ok((await page.locator('h1').innerText()).includes('لا يوجد اتصال') && (await page.content()).includes('يمكنك قراءة ما فتحته سابقًا'), 'offline: unvisited page shows offline.html');
  await ctx.setOffline(false);

  // ── 3) تحديث الـ SW: شريط هادئ بدل التحديث الصامت
  await page.goto(B + '/', { waitUntil: 'networkidle' });
  state.v2 = true;
  await page.evaluate(() => window.__pwaReg.update());
  await page.waitForSelector('#pwa-update', { state: 'visible', timeout: 15000 }).then(() => ok(true, 'update bar appears'), () => ok(false, 'update bar appears'));
  ok((await page.locator('#pwa-update').innerText()).includes('يوجد تحديث، حدّث الصفحة'), 'update bar text is calm Arabic');
  ok(await page.evaluate(async (v) => { const r = window.__pwaReg; return !!r.waiting && r.active.scriptURL.includes('sw.js') && (await caches.keys()).includes('shell-' + v); }, V), 'new version waits (not silently activated); old caches still serving');
  await Promise.all([page.waitForNavigation({ timeout: 15000 }).catch(() => {}), page.click('#pwa-update-go')]);
  await page.waitForFunction(async () => (await caches.keys()).includes('shell-testv2'), null, { timeout: 15000 }).catch(() => {});
  const keys2 = await page.evaluate(() => caches.keys());
  ok(keys2.includes('shell-testv2') && keys2.includes('data-testv2') && !keys2.some(k => /^(shell|data)-/.test(k) && !k.endsWith('testv2')), 'after update: new version caches active, old removed');
  state.v2 = false;

  // ── 4) نموذج التواصل لا يتأثر بالـ SW
  await page.goto(B + '/', { waitUntil: 'networkidle' });
  state.posts.length = 0;
  const resp = page.waitForResponse(r => r.url().includes('/backend/api/contact.php'));
  await page.locator('#contactForm [name=name]').fill('اختبار'); await page.locator('#contactForm [name=email]').fill('a@b.co'); await page.locator('#contactForm [name=message]').fill('رسالة تجريبية');
  await page.locator('#contactForm button[type=submit]').click();
  const r = await resp;
  ok(!r.fromServiceWorker() && state.posts.includes('POST /backend/api/contact.php'), 'contact form POST goes straight to network (not via SW)');
  ok((await page.locator('#contactMsg').innerText()).includes('وصلتنا رسالتك'), 'contact form shows success');
  const g = await page.evaluate(async () => { const x = await fetch('/backend/api/contact.php'); return [x.status, await x.text()]; });
  ok(g[0] === 200 && g[1].includes('method_not_allowed'), 'GET /backend/ passes through');
  ok(await page.evaluate(async () => { for (const k of await caches.keys()) for (const q of await (await caches.open(k)).keys()) if (q.url.includes('/backend/')) return false; return true; }), '/backend/ never cached');

  // ── 5) الدفتر: تصدير/استيراد
  await page.evaluate(() => {
    localStorage.setItem('tajalli_athar_v1', JSON.stringify([{ id: 'a1', created: 100, note: 'محلي' }]));
    localStorage.setItem('journey', JSON.stringify({ done: { 'rahman-0': true }, notes: { 'rahman-0': 'ملاحظة محلية' } }));
    localStorage.setItem('tajalli_book_youth_v1', JSON.stringify({ notes: { c1: 'نص محلي' }, done: { c1: true }, read: {}, last: 'c1', fs: 1, theme: '' }));
    localStorage.setItem('aud', JSON.stringify('father'));
  });
  await page.reload({ waitUntil: 'networkidle' });
  const dl = page.waitForEvent('download'); await page.click('#pwa-export'); const d = await dl;
  const file = '/tmp/claude-0/diary-test.json'; fs.mkdirSync('/tmp/claude-0', { recursive: true }); await d.saveAs(file);
  const exp = JSON.parse(fs.readFileSync(file, 'utf8'));
  ok(exp.app === 'tajalliyat' && exp.kind === 'notebook' && exp.version === 1 && /^tajalliyat-diary-\d{4}-\d\d-\d\d\.json$/.test(d.suggestedFilename()), 'export: versioned JSON + filename');
  ok(exp.data.athar.length === 1 && exp.data.journey.done['rahman-0'] === true && exp.data.books.tajalli_book_youth_v1.notes.c1 === 'نص محلي' && exp.data.prefs.aud === 'father', 'export: athar + journey + books + prefs');
  // استيراد على «جهاز آخر»: بيانات مختلفة جزئياً → دمج بلا مسح
  const imp = { app: 'tajalliyat', kind: 'notebook', version: 1, exportedAt: 'x', data: {
    athar: [{ id: 'a1', created: 100, note: 'محلي' }, { id: 'a2', created: 200, note: 'مستورد' }],
    journey: { done: { 'rahman-1': true }, notes: { 'rahman-0': 'ملاحظة أخرى', 'rahman-1': 'جديدة' } },
    books: { tajalli_book_youth_v1: { notes: { c1: 'نص آخر', c2: 'فصل ثانٍ' }, done: { c2: true }, read: {}, last: 'c2', fs: 2, theme: 'dark' }, tajalli_book_mother_v1: { notes: { c1: 'أم' } } },
    prefs: { aud: 'boy', theme: 'dark' } } };
  fs.writeFileSync('/tmp/claude-0/diary-import.json', JSON.stringify(imp));
  await Promise.all([page.waitForNavigation({ timeout: 10000 }).catch(() => {}), page.setInputFiles('#pwa-file', '/tmp/claude-0/diary-import.json')]);
  await page.waitForLoadState('networkidle');
  const after = await page.evaluate(() => ({ athar: JSON.parse(localStorage.tajalli_athar_v1), j: JSON.parse(localStorage.journey), b: JSON.parse(localStorage.tajalli_book_youth_v1), m: localStorage.tajalli_book_mother_v1, aud: localStorage.aud, theme: localStorage.theme }));
  ok(after.athar.length === 2 && after.athar[0].id === 'a2' && after.athar.some(x => x.note === 'محلي'), 'import: athar merged by id, nothing lost');
  ok(after.j.done['rahman-0'] === true && after.j.done['rahman-1'] === true && after.j.notes['rahman-0'].includes('ملاحظة محلية') && after.j.notes['rahman-0'].includes('ملاحظة أخرى') && after.j.notes['rahman-1'] === 'جديدة', 'import: journey merged; conflicting notes keep both');
  ok(after.b.notes.c1.includes('نص محلي') && after.b.notes.c1.includes('نص آخر') && after.b.notes.c2 === 'فصل ثانٍ' && after.b.done.c1 && after.b.done.c2 && after.b.last === 'c1' && after.b.fs === 1, 'import: book notes merged, local settings kept');
  ok(!!after.m && after.aud === JSON.stringify('father') && after.theme === JSON.stringify('dark'), 'import: new book added; existing pref kept, missing pref filled');
  // ملف غير صالح + صيغة «أثر الاسم» القديمة
  fs.writeFileSync('/tmp/claude-0/bad.json', JSON.stringify({ app: 'other', data: {} }));
  await page.setInputFiles('#pwa-file', '/tmp/claude-0/bad.json'); await page.waitForTimeout(400);
  ok((await page.locator('#pwa-msg').innerText()).includes('ليس نسخة دفتر'), 'import: invalid file rejected with message');
  fs.writeFileSync('/tmp/claude-0/bad2.json', JSON.stringify({ app: 'tajalliyat', kind: 'notebook', version: 99, data: {} }));
  await page.setInputFiles('#pwa-file', '/tmp/claude-0/bad2.json'); await page.waitForTimeout(400);
  ok((await page.locator('#pwa-msg').innerText()).includes('ليس نسخة دفتر'), 'import: future version rejected');
  ok(await page.evaluate(() => JSON.parse(localStorage.tajalli_athar_v1).length === 2), 'import: rejected files change nothing');
  const legacy = await page.evaluate(() => { const v = window.__pwa.validate({ app: 'tajalli-athar', entries: [{ id: 'old1', created: 5 }] }); return !!v && v.athar.length === 1; });
  ok(legacy, 'import: accepts old «أثر الاسم» backup format');

  // ── 6) التثبيت: الزر ظاهر دائماً + ملاحظة Chrome
  const fire = () => page.evaluate(() => { window.__prompted = 0; const e = new Event('beforeinstallprompt', { cancelable: true }); e.prompt = () => { window.__prompted++; return Promise.resolve(); }; e.userChoice = Promise.resolve({ outcome: 'dismissed' }); window.dispatchEvent(e); });
  await page.reload({ waitUntil: 'networkidle' });
  ok(await page.locator('#pwa-install').isVisible(), 'install button is visible even before the browser offers install');
  ok((await page.locator('#pwa-panel p').first().innerText()).includes('صدّر دفترك قبل التثبيت حتى تنقله'), 'export notice appears before the install button');
  const note = await page.locator('#pwa-chrome-note').innerText();
  ok(note.includes('Chrome') && note.includes('139') && note.includes('إنشاء اختصار'), 'Chrome note: older than 139 may not work → create a shortcut');
  await page.click('#pwa-install');                                             // لا حدث تثبيت → خطوات يدوية
  ok((await page.locator('#pwa-msg').innerText()).includes('قائمة المتصفح') && (await page.locator('#pwa-msg').innerText()).includes('واتساب'), 'no direct prompt available: shows manual steps (incl. open in Chrome from WhatsApp)');
  await fire();
  await page.click('#pwa-install');
  ok((await page.evaluate(() => window.__prompted)) === 1 && await page.locator('#pwa-install').isVisible(), 'install prompt fires once and the button stays visible');
  await page.click('#pwa-install');
  ok((await page.evaluate(() => window.__prompted)) === 1 && (await page.locator('#pwa-msg').innerText()).includes('قائمة المتصفح'), 'second click does not re-prompt; shows manual steps');

  // ── 7) iPhone: تلميح قابل للإغلاق لا يتكرر + الزر يشرح الخطوات
  const ios = await browser.newContext({ ...devices['iPhone 13'] }); const ip = await ios.newPage();
  await ip.goto(B + '/', { waitUntil: 'networkidle' });
  ok(await ip.locator('.pwa-hint').isVisible() && (await ip.locator('.pwa-hint').innerText()).includes('إضافة إلى الشاشة الرئيسية'), 'iPhone: install hint shown');
  ok(await ip.locator('#pwa-install').isVisible() && (await ip.locator('#pwa-chrome-note').count()) === 0, 'iPhone: install button visible, no Chrome note');
  await ip.click('#pwa-install'); ok((await ip.locator('#pwa-msg').innerText()).includes('زر المشاركة'), 'iPhone: button explains Share → Add to Home Screen');
  await ip.click('.pwa-hint button'); await ip.reload({ waitUntil: 'networkidle' });
  ok((await ip.locator('.pwa-hint').count()) === 0 && await ip.locator('#pwa-install').isVisible(), 'iPhone: hint stays closed after dismissal; button remains');
  await ip.locator('#pwa-panel').scrollIntoViewIfNeeded(); await ip.screenshot({ path: '/tmp/claude-0/pwa-ios.png' }); await ios.close();

  // ── 7b) أندرويد قديم (Chrome 138): الزر ظاهر، لا يستدعي التثبيت المباشر، يعرض الاختصار
  const old = await browser.newContext({ viewport: { width: 360, height: 740 }, userAgent: 'Mozilla/5.0 (Linux; Android 8.1.0; Jelly Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.179 Mobile Safari/537.36' });
  const op = await old.newPage();
  await op.goto(B + '/', { waitUntil: 'networkidle' });
  await op.evaluate(() => { window.__prompted = 0; const e = new Event('beforeinstallprompt', { cancelable: true }); e.prompt = () => { window.__prompted++; return Promise.resolve(); }; e.userChoice = Promise.resolve({ outcome: 'dismissed' }); window.dispatchEvent(e); });
  ok(await op.locator('#pwa-install').isVisible(), 'old Android (Chrome 138): install button still visible');
  ok((await op.locator('#pwa-chrome-note').innerText()).includes('139') && (await op.locator('#pwa-chrome-note').evaluate(n => getComputedStyle(n).fontWeight)) >= 600, 'old Android: Chrome note shown (emphasised)');
  await op.click('#pwa-install');
  ok((await op.evaluate(() => window.__prompted)) === 0 && (await op.locator('#pwa-msg').innerText()).includes('إنشاء اختصار'), 'old Android: click shows the shortcut steps, never calls the crashing direct install');
  ok(!(await op.locator('#pwa-panel').innerText()).includes('صدّر دفترك قبل التثبيت') && await op.locator('#pwa-export').isVisible(), 'old Android: no export-before-install notice, export/import available');
  await op.locator('#pwa-panel').scrollIntoViewIfNeeded(); await op.screenshot({ path: '/tmp/claude-0/pwa-legacy.png' }); await old.close();

  // ── 8) قابلية التثبيت (CDP)
  const cdp = await ctx.newCDPSession(page);
  const man = await cdp.send('Page.getAppManifest'); const inst = await cdp.send('Page.getInstallabilityErrors');
  ok(inst.installabilityErrors.length === 0, 'Chrome installability errors: ' + (inst.installabilityErrors.map(e => e.errorId).join(',') || 'none'));
  ok(!man.errors.length, 'manifest parses without errors ' + JSON.stringify(man.errors));
  await page.locator('#pwa-panel').scrollIntoViewIfNeeded(); await page.screenshot({ path: '/tmp/claude-0/pwa-panel.png' });

  ok(errs.length === 0, 'no page JS errors ' + JSON.stringify(errs));
  await browser.close(); server.close();
  console.log(fails ? `\n${fails} FAILED` : '\nALL PASSED'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
