/* إحصاء مجهول ومجمّع — تجليات الأسماء
 * يرسل أرقاماً فقط (نوع حدث + معرّف اسم/شعور من قائمة مسموحة) إلى /backend/api/hit.php.
 * لا كوكيز، لا IP من جهتنا، لا عنوان صفحة كامل، ولا نص يكتبه الزائر (البحث يُرسَل كـ hit/miss وأسماء مطابقة فقط).
 * يحترم Do Not Track وGlobal Privacy Control: إن كانا مفعّلين لا يُرسل شيء.
 * العلامتان المحليتان: tajalli_d (تاريخ آخر يوم عُدّ فيه هذا المتصفح) و sessionStorage tajalli_s (جلسة واحدة = زيارة واحدة).
 */
(function () {
  'use strict';
  if (window.__statsLoaded) return; window.__statsLoaded = true;
  if (navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.msDoNotTrack === '1' || navigator.globalPrivacyControl === true) return;
  var EP = '/backend/api/hit.php';
  var q = [], timer = null;

  function flush() {
    timer = null;
    if (!q.length) return;
    var body = JSON.stringify({ e: q.splice(0, 12) });
    try { fetch(EP, { method: 'POST', body: body, keepalive: true, headers: { 'Content-Type': 'text/plain;charset=UTF-8' }, credentials: 'omit' }).catch(function () {}); } catch (e) {}
    if (q.length) timer = setTimeout(flush, 300);
  }
  function send(kind, item) {
    q.push([kind, item || '']);
    if (!timer) timer = setTimeout(flush, 900);
  }
  window.__stat = send;                                                // يستعمله pwa.js
  addEventListener('pagehide', flush);
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden') flush(); });

  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function today() { var d = new Date(); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }

  /* ───────── المسار → نوع الصفحة ───────── */
  function pathInfo() {
    var p = location.pathname.replace(/\/index\.html$/, '/');
    var m;
    if ((m = p.match(/\/n\/([a-z]+)\/?$/))) return { entry: 'name', name: m[1] };
    if ((m = p.match(/\/feel\/([a-z]+)\/?$/))) return { entry: 'feel', feeling: m[1] };
    if (/\/feel\/?$/.test(p)) return { entry: 'feel_hub', page: 'feel_hub' };
    if ((m = p.match(/\/books\/([a-z]+)\/?$/))) return { entry: 'book', page: 'book_' + m[1] };
    if (/\/books\/?$/.test(p)) return { entry: 'books', page: 'books' };
    if (/\/guide\.html$/.test(p)) return { entry: 'guide', page: 'guide' };
    if (/\/athar\.html$/.test(p)) return { entry: 'athar', page: 'athar' };
    if (/\/(index\.html)?$/.test(p) && !/\/(n|feel|books|print|pdf)\//.test(p)) return { entry: 'home', spa: true };
    return { entry: 'other' };
  }
  function refCategory() {
    var r = document.referrer;
    if (!r) return 'direct';
    var h; try { h = new URL(r).hostname.replace(/^www\./, '').replace(/^m\./, ''); } catch (e) { return 'other'; }
    if (h === location.hostname.replace(/^www\./, '')) return null;                     // تنقل داخلي
    var map = [[/(^|\.)google\./, 'google'], [/(^|\.)bing\.com$/, 'bing'], [/duckduckgo/, 'duckduckgo'], [/yandex/, 'yandex'],
      [/(^|\.)(wa\.me|whatsapp\.com)$/, 'whatsapp'], [/facebook\.com$|(^|\.)fb\.com$|^l\.facebook/, 'facebook'], [/instagram\.com$/, 'instagram'],
      [/(^|\.)(t\.co|twitter\.com|x\.com)$/, 'twitter'], [/(^|\.)(t\.me|telegram\.org)$/, 'telegram'], [/youtube\.com$|youtu\.be$/, 'youtube']];
    for (var i = 0; i < map.length; i++) if (map[i][0].test(h)) return map[i][1];
    return 'other';
  }

  /* ───────── زيارة جديدة (جلسة متصفح) ───────── */
  var info = pathInfo(), isNew = false;
  try { isNew = !sessionStorage.getItem('tajalli_s'); sessionStorage.setItem('tajalli_s', '1'); } catch (e) { isNew = true; }
  if (isNew) {
    send('visit');
    if (lsGet('tajalli_d') !== today()) { lsSet('tajalli_d', today()); send('device'); }     // جهاز/متصفح واحد في اليوم (تقريبي)
    send('entry', info.entry);
    var ref = refCategory(); if (ref) send('ref', ref);
    if ((window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true) send('pwa', 'standalone_open');
  }

  /* ───────── مشاهدات الصفحات ───────── */
  var lastHash = null;
  function view() {
    if (info.name) send('name', info.name);
    if (info.feeling) send('feeling', info.feeling);
    if (info.page) send('page', info.page);
    if (!info.spa) return;
    var h = location.hash || '#today', m;
    if (h === lastHash) return; lastHash = h;
    if ((m = h.match(/^#name-([a-z]+)/))) { send('name', m[1]); return; }
    if ((m = h.match(/^#feel-([a-z]+)/))) { send('feeling', m[1]); return; }
    var map = { '#today': 'home', '#names': 'names', '#feel': 'feel_hub', '#journey': 'journey', '#videos': 'videos' };
    send('page', map[h] || 'home');
  }
  view();
  if (info.spa) addEventListener('hashchange', view);

  /* ───────── البحث: بلا نص، فقط hit/miss والأسماء المطابقة (٣ أو أقل) ───────── */
  function norm(t) {
    return String(t || '').replace(/[ً-ٰٟـ]/g, '').replace(/[أإآٱ]/g, 'ا').replace(/ى/g, 'ي').replace(/ة/g, 'ه').replace(/\s+/g, ' ').trim().toLowerCase();
  }
  var searchT = null;
  document.addEventListener('input', function (e) {
    var t = e.target;
    if (!t || !t.classList || !t.classList.contains('qsearch')) return;
    clearTimeout(searchT);
    searchT = setTimeout(function () {
      var v = norm(t.value);
      if (v.length < 2) return;
      var names = window.ASMA || [], hits = [];
      for (var i = 0; i < names.length; i++) {
        var n = names[i];
        if (norm(n.plain).indexOf(v) !== -1 || norm(n.name).indexOf(v) !== -1 || norm(n.tagline).indexOf(v) !== -1) hits.push(n.id);
      }
      send('search', hits.length ? 'hit' : 'miss');
      if (hits.length && hits.length <= 3) hits.forEach(function (id) { send('search_name', id); });
    }, 1600);
  }, true);

  /* ───────── نقرات: مشاركة، تبويبات، فئة ───────── */
  document.addEventListener('click', function (e) {
    var el = e.target && e.target.closest ? e.target.closest('a,button') : null;
    if (!el) return;
    if (el.closest('.share')) {
      var href = el.getAttribute('href') || '', txt = el.textContent || '';
      if (/^https:\/\/wa\.me\//.test(href)) send('share', 'whatsapp');
      else if (txt.indexOf('نسخ') !== -1) send('share', 'copy');
      else if (txt.indexOf('بطاقة') !== -1) send('share', 'card');
      else if (/\/feel\//.test(href)) send('share', 'page');
      return;
    }
    if (el.closest('.tabs') && el.getAttribute('role') === 'tab') {
      var tx = el.textContent || '';
      send('tab', tx.indexOf('التجليات') !== -1 ? 'tajalliyat' : tx.indexOf('أسئلة') !== -1 ? 'questions' : tx.indexOf('المهام') !== -1 ? 'tasks' : '');
      return;
    }
    if (el.closest('#aud') && el.classList.contains('chip')) {
      setTimeout(function () { var a = lsGet('aud'); try { a = JSON.parse(a); } catch (x) {} if (typeof a === 'string') send('aud', a); }, 80);
    }
  }, true);
})();
