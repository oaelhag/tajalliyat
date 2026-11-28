// اختبار الإحصاء في الواجهة (نسخة مبنية بـ STATS=1).  node deploy/tests/stats.test.js <نسخة-مبنية>
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(process.argv[2]);
const notice = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'content', 'site_texts.json'), 'utf8')).analytics_notice.ar;
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.json': 'application/json', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json', '.xml': 'application/xml', '.txt': 'text/plain' };
const hits = []; const posts = [];
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p === '/backend/api/hit.php') {
    let b = ''; req.on('data', d => b += d); req.on('end', () => { try { JSON.parse(b).e.forEach(e => hits.push(e)); posts.push(b); } catch (e) { posts.push('BAD:' + b); } res.writeHead(200, { 'Content-Type': 'application/json' }); res.end('{"ok":true}'); }); return;
  }
  if (p.startsWith('/backend/')) { posts.push(req.method + ' ' + p); res.writeHead(200, { 'Content-Type': 'application/json' }); res.end('{"ok":true}'); return; }
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end('nf'); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-cache' }); res.end(fs.readFileSync(f));
});
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const B = 'http://localhost:8794';
const has = (k, i) => hits.some(e => e[0] === k && e[1] === i);
const count = (k, i) => hits.filter(e => e[0] === k && (i === undefined || e[1] === i)).length;
const wait = ms => new Promise(r => setTimeout(r, ms));
// نفس القوائم المسموحة في الخادم (stats_lib.php)
const ALLOWED = { visit: /^$/, device: /^$/, entry: /^(home|name|feel|feel_hub|books|book|guide|athar|other)$/, page: /^(home|names|feel_hub|journey|videos|guide|athar|books|book_[a-z]{3,10})$/, name: /^[a-z]{2,24}$/, feeling: /^[a-z]{2,24}$/, search: /^(hit|miss)$/, search_name: /^[a-z]{2,24}$/, tab: /^(tajalliyat|questions|tasks)$/, aud: /^(boy|girl|youngman|youngwoman|father|mother)$/, share: /^(copy|whatsapp|card|page)$/, ref: /^(direct|google|bing|duckduckgo|yandex|whatsapp|facebook|instagram|twitter|telegram|youtube|other)$/, pwa: /^(install_click|install_accepted|export|import|standalone_open)$/ };

(async () => {
  await new Promise(r => server.listen(8794, r));
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 360, height: 740 }, serviceWorkers: 'block' });
  const page = await ctx.newPage(); const ext = new Set(); const errs = [];
  page.on('request', r => { const u = new URL(r.url()); if (!['localhost', ''].includes(u.hostname) && !r.url().startsWith('data:')) ext.add(u.hostname); });
  page.on('pageerror', e => errs.push(e.message));

  // 1) الرئيسية: زيارة جديدة
  await page.goto(B + '/', { waitUntil: 'networkidle' }); await wait(1500);
  ok(count('visit') === 1 && count('device') === 1 && has('entry', 'home') && has('ref', 'direct') && has('page', 'home'), 'home: visit + device + entry + referrer + page recorded once');
  ok((await page.locator('footer').innerText()).includes(notice), 'home footer shows the anonymous-stats notice');

  // 2) تنقّل داخل التطبيق
  await page.evaluate(() => { location.hash = '#name-rahman'; }); await wait(300);
  await page.evaluate(() => { location.hash = '#feel-sad'; }); await wait(300);
  await page.evaluate(() => { location.hash = '#names'; }); await wait(1500);
  ok(has('name', 'rahman') && has('feeling', 'sad') && has('page', 'names'), 'hash routes: name, feeling and section views recorded');
  ok(count('visit') === 1 && count('device') === 1, 'navigation inside the same session does not add visits');

  // 3) البحث: لا نص، فقط hit/miss وأسماء مطابقة
  await page.goto(B + '/#names', { waitUntil: 'networkidle' }); await page.reload({ waitUntil: 'networkidle' }); await wait(500);
  const sb = page.locator('.qsearch').first();
  const SECRET = 'أشعر بالذنب وعملت شيئاً سيئاً';
  await sb.fill('رحمن'); await wait(2600);
  ok(has('search', 'hit') && has('search_name', 'rahman'), 'search: a matching query records hit + the matched name');
  await sb.fill('zzzzqq'); await wait(2600);
  ok(has('search', 'miss'), 'search: no match records miss');
  await sb.fill(SECRET); await wait(2600);
  ok(!posts.some(b => b.includes('ذنب') || b.includes('zzzz') || b.includes('رحمن') || b.includes(SECRET)), 'search: typed text never leaves the browser');

  // 4) نقرات: مشاركة وفئة وتبويب
  await page.goto(B + '/', { waitUntil: 'networkidle' }); await page.reload({ waitUntil: 'networkidle' }); await wait(500);
  await page.locator('.aud .chip', { hasText: 'أب' }).first().click(); await wait(1500);
  ok(has('aud', 'father'), 'audience chip recorded');
  await page.locator('.share button', { hasText: 'نسخ' }).first().click().catch(() => {}); await wait(1500);
  ok(has('share', 'copy'), 'share: copy recorded');
  await page.goto(B + '/#name-rahman', { waitUntil: 'networkidle' }); await page.reload({ waitUntil: 'networkidle' }); await wait(500);
  await page.locator('.tabs button', { hasText: 'أسئلة' }).first().click(); await wait(1500);
  ok(has('tab', 'questions'), 'name tab recorded');

  // 5) صفحات ثابتة (زوار جوجل): دخول مباشر
  const sctx = await browser.newContext({ serviceWorkers: 'block' }); const sp = await sctx.newPage();
  await sp.goto(B + '/n/hakim/', { waitUntil: 'networkidle' }); await wait(1500);
  ok(has('entry', 'name') && has('name', 'hakim'), 'static name page: entry=name and name recorded');
  await sp.goto(B + '/feel/anxious/', { waitUntil: 'networkidle' }); await wait(1500);
  ok(has('feeling', 'anxious'), 'static feeling page: feeling recorded');
  const v = count('visit'), d = count('device');
  await sp.goto(B + '/feel/', { waitUntil: 'networkidle' }); await wait(1200);
  ok(count('visit') === v && count('device') === d && has('page', 'feel_hub'), 'second page in the same session: no extra visit/device');
  const sp2 = await sctx.newPage(); await sp2.goto(B + '/guide.html', { waitUntil: 'networkidle' }); await wait(1500);
  ok(count('visit') === v + 1 && count('device') === d && has('page', 'guide'), 'new tab = new visit, but the same device is not counted twice that day');
  await sctx.close();

  // 6) احترام Do Not Track
  const dnt = await browser.newContext({ serviceWorkers: 'block' }); await dnt.addInitScript(() => Object.defineProperty(navigator, 'doNotTrack', { value: '1' }));
  const dp = await dnt.newPage(); const before = hits.length;
  await dp.goto(B + '/', { waitUntil: 'networkidle' }); await wait(1800);
  ok(hits.length === before, 'Do Not Track: nothing is sent'); await dnt.close();

  // 7) الحمولة: قوائم مسموحة فقط، بلا مفاتيح أو نصوص أخرى
  ok(hits.every(e => ALLOWED[e[0]] && ALLOWED[e[0]].test(e[1] || '')) && posts.every(b => { try { return Object.keys(JSON.parse(b)).join() === 'e'; } catch (x) { return false; } }), 'every event is an allowed kind with an allowed item');
  ok(ext.size === 0, 'no request to any external host ' + [...ext].join(','));

  // 8) نموذج التواصل لا يتأثر
  await page.goto(B + '/', { waitUntil: 'networkidle' });
  const nContact = posts.length;
  await page.locator('#contactForm [name=name]').fill('اختبار'); await page.locator('#contactForm [name=email]').fill('a@b.co'); await page.locator('#contactForm [name=message]').fill('رسالة');
  await page.locator('#contactForm button[type=submit]').click(); await wait(600);
  ok((await page.locator('#contactMsg').innerText()).includes('وصلتنا رسالتك') && posts.some(b => b === 'POST /backend/api/contact.php'), 'contact form still works');
  ok(errs.length === 0, 'no JS errors ' + JSON.stringify(errs));
  await browser.close(); server.close();
  console.log(`\n${hits.length} events captured in ${posts.length} requests`);
  console.log(fails ? `${fails} FAILED` : 'ALL PASSED'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
