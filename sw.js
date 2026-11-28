/* Service worker — تجليات الأسماء
 * يُولَّد من deploy/pwa/sw.js بواسطة deploy/pwa.py (يستبدل __PLACEHOLDERS__).
 * قواعد: GET من نفس الأصل فقط؛ لا /backend/؛ لا فيديو ولا PDF؛ لا skipWaiting تلقائي.
 */
const VERSION = '84721c0c699b';
const BASE = '/pwa-preview/';                         // '/' على الإنتاج
const CORE = ["/pwa-preview/", "/pwa-preview/guide.html", "/pwa-preview/athar.html", "/pwa-preview/offline.html", "/pwa-preview/manifest.webmanifest", "/pwa-preview/pwa.js", "/pwa-preview/icon.svg", "/pwa-preview/favicon-48.png", "/pwa-preview/apple-touch-icon.png", "/pwa-preview/icon-192.png", "/pwa-preview/icon-512.png", "/pwa-preview/assets/fonts/amiri-quran-arabic-400-normal.woff2", "/pwa-preview/assets/fonts/fonts.css", "/pwa-preview/assets/fonts/ibm-plex-sans-arabic-arabic-400-normal.woff2", "/pwa-preview/assets/fonts/ibm-plex-sans-arabic-arabic-500-normal.woff2", "/pwa-preview/assets/fonts/ibm-plex-sans-arabic-arabic-600-normal.woff2", "/pwa-preview/assets/fonts/noto-naskh-arabic-arabic-400-normal.woff2", "/pwa-preview/assets/fonts/noto-naskh-arabic-arabic-600-normal.woff2", "/pwa-preview/assets/fonts/noto-naskh-arabic-arabic-700-normal.woff2", "/pwa-preview/assets/fonts/reem-kufi-arabic-500-normal.woff2", "/pwa-preview/assets/fonts/reem-kufi-arabic-700-normal.woff2"];                           // القشرة: يجب أن تنجح كلها
const OPTIONAL = ["/pwa-preview/books/", "/pwa-preview/feel/", "/pwa-preview/books/reader.css", "/pwa-preview/books/reader.js"];                   // قشرة إضافية: تُحمَّل إن أمكن
const DATA_FILES = ["/pwa-preview/data.js", "/pwa-preview/prod.js", "/pwa-preview/news.js"];                     // data.js وغيره: stale-while-revalidate

const SHELL = 'shell-' + VERSION;
const DATA = 'data-' + VERSION;
const PAGES = 'pages-v1', IMGS = 'img-v1';       // كاش وقت التشغيل بحد أقصى للعدد
const MAX_PAGES = 60, MAX_IMGS = 150;
const OFFLINE = BASE + 'offline.html';

const rel = p => '/' + p.slice(BASE.length);     // المسار نسبةً إلى جذر الموقع
const dataSet = new Set(DATA_FILES);

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const shell = await caches.open(SHELL);
    const data = await caches.open(DATA);
    const fresh = u => new Request(u, { cache: 'reload' });   // يتجاوز كاش المتصفح والـ CDN
    await Promise.all([...CORE.map(u => shell.add(fresh(u))), ...DATA_FILES.map(u => data.add(fresh(u)))]);
    await Promise.allSettled(OPTIONAL.map(u => shell.add(fresh(u))));
    // لا skipWaiting هنا: الصفحة تعرض شريط «يوجد تحديث» والمستخدم هو من يقرّر
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) {
      if ((k.startsWith('shell-') && k !== SHELL) || (k.startsWith('data-') && k !== DATA)) await caches.delete(k);
    }
    await self.clients.claim();
  })());
});

self.addEventListener('message', e => {
  if (e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting();
});

async function trim(cache, max) {
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - max; i++) await cache.delete(keys[i]);
}

// ملاحظة: res.clone() يجب أن يحدث قبل أول await، وإلا تكون الصفحة قد بدأت تستهلك الجسم
async function put(name, req, res, max) {
  if (!res || !res.ok || res.type !== 'basic') return;
  const copy = res.clone();
  const c = await caches.open(name);
  await c.put(req, copy);
  if (max) await trim(c, max);
}

// تنقّل بين الصفحات: الشبكة أولاً، ثم ما فُتح سابقاً، ثم offline.html
async function navigate(e) {
  const req = e.request;
  try {
    const res = await fetch(req);
    if (!rel(new URL(req.url).pathname).startsWith('/print/')) e.waitUntil(put(PAGES, req, res, MAX_PAGES).catch(() => {}));
    return res;
  } catch (err) {
    const hit = (await caches.match(req, { ignoreSearch: true })) || (await caches.match(OFFLINE));
    return hit || new Response('offline', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
  }
}

// stale-while-revalidate داخل كاش محدد
async function swr(e, name, max) {
  const cache = await caches.open(name);
  const hit = await cache.match(e.request, { ignoreSearch: true });
  const net = fetch(e.request, { cache: 'no-cache' }).then(res => { const saved = put(name, e.request, res, max).catch(() => {}); e.waitUntil(saved); return res; }).catch(() => null);
  e.waitUntil(net);
  return hit || (await net) || Response.error();
}

// الكاش أولاً ثم الشبكة، مع حفظ وقت التشغيل
async function cacheFirst(e, name, max) {
  const req = e.request;
  const hit = await caches.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  e.waitUntil(put(name, req, res, max).catch(() => {}));
  return res;
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;                              // POST وغيره: يمر للشبكة كما هو
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (!url.pathname.startsWith(BASE)) return;
  const r = rel(url.pathname);
  if (r.startsWith('/backend/')) return;                         // نموذج التواصل والـ API: لا يُلمس أبداً
  if (r.startsWith('/videos/') || r.startsWith('/pdf/') || r.startsWith('/books/pdf/') || /\.(mp4|webm|pdf)$/i.test(r)) return;
  if (req.headers.has('range')) return;
  if (r === '/sw.js' || r === '/manifest.webmanifest') return;   // دائماً من الشبكة

  if (req.mode === 'navigate') { e.respondWith(navigate(e)); return; }
  if (dataSet.has(url.pathname)) { e.respondWith(swr(e, DATA)); return; }
  if (/^\/(images|og)\//.test(r) || r.startsWith('/books/img/')) { e.respondWith(cacheFirst(e, IMGS, MAX_IMGS)); return; }
  if (r.startsWith('/books/')) { e.respondWith(swr(e, PAGES, MAX_PAGES)); return; }
  if (r.startsWith('/print/')) return;
  // الخطوط والأيقونات وبقية الملفات الثابتة
  e.respondWith(cacheFirst(e, SHELL, 0).catch(() => Response.error()));
});
