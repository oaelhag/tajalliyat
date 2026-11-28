/* PWA — تسجيل الـ service worker، شريط التحديث، زر التثبيت، وتصدير/استيراد الدفتر.
 * لا يغيّر أي مفتاح تخزين موجود. المفتاحان الجديدان الوحيدان: tajalli_pwa_install_v1 و tajalli_pwa_ios_hint_v1.
 */
(function () {
  'use strict';
  var BASE = new URL('./', document.currentScript.src).pathname;      // '/' على الإنتاج
  var LS = { install: 'tajalli_pwa_install_v1', ios: 'tajalli_pwa_ios_hint_v1', legacy: 'tajalli_pwa_legacy_hint_v1' };
  var ATHAR = 'tajalli_athar_v1', JOURNEY = 'journey', PREFS = ['aud', 'theme', 'rtime'];
  var BOOK_KEY = /^tajalli_book_[a-z0-9]+_v1$/;
  var FORMAT = { app: 'tajalliyat', kind: 'notebook', version: 1 };
  var MAX_IMPORT = 5 * 1024 * 1024;

  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function parse(s, d) { try { return s == null ? d : JSON.parse(s); } catch (e) { return d; } }
  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (k === 'text') e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { e.append(c); });
    return e;
  }
  // أندرويد بـ Chrome أقدم من 139 (آخر إصدار لأندرويد 8 و9): التطبيق المثبّت (WebAPK) ينهار على هذه الأجهزة، فنعرض «إنشاء اختصار» بدل التثبيت
  var chromeMajor = +((navigator.userAgent.match(/Chrome\/(\d+)/) || [])[1] || 0);
  var legacyAndroid = /android/i.test(navigator.userAgent) && chromeMajor > 0 && chromeMajor < 139;
  var isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;

  /* ───────────── الأنماط (ترث ألوان الصفحة، فتناسب الوضعين الليلي والنهاري) ───────────── */
  var css = el('style', { text:
    '#pwa-panel{max-width:46em;margin:34px auto 18px;padding:16px 18px;border:1px solid currentColor;border-radius:14px;font:inherit;line-height:1.8;opacity:.95}' +
    '#pwa-panel h2{font-size:1.05em;margin:0 0 6px}#pwa-panel p{margin:6px 0}' +
    '#pwa-panel .pwa-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}' +
    '#pwa-panel button,#pwa-update button{font:inherit;color:inherit;background:none;border:1.5px solid currentColor;border-radius:999px;min-height:44px;min-width:44px;padding:0 18px;cursor:pointer}' +
    '#pwa-panel button:focus-visible,#pwa-update button:focus-visible{outline:2px solid currentColor;outline-offset:3px}' +
    '#pwa-panel .pwa-hint{display:flex;gap:10px;align-items:flex-start;justify-content:space-between;border-top:1px dashed currentColor;margin-top:12px;padding-top:10px}' +
    '#pwa-panel .pwa-hint button{flex:none;padding:0 12px}' +
    '#pwa-msg{font-size:.95em}#pwa-msg:empty{display:none}' +
    '#pwa-update{position:fixed;z-index:2147483000;inset-inline:12px;bottom:calc(var(--navh,0px) + 12px + env(safe-area-inset-bottom,0px));max-width:30em;margin-inline:auto;display:flex;gap:10px;align-items:center;justify-content:space-between;padding:10px 14px;border-radius:14px;background:#0E1324;color:#E9E6DD;border:1px solid #E3B45C;font:500 15px/1.7 system-ui,sans-serif;box-shadow:0 6px 24px rgba(0,0,0,.35)}' +
    '#pwa-update button{color:#E3B45C;min-height:40px}' });
  document.head.append(css);

  /* ───────────── شريط التحديث ───────────── */
  var reloading = false;
  function showUpdate(reg) {
    if (document.getElementById('pwa-update')) return;
    var bar = el('div', { id: 'pwa-update', role: 'status' }, [
      el('span', { text: 'يوجد تحديث، حدّث الصفحة' }),
      el('span', {}, [
        el('button', { type: 'button', id: 'pwa-update-go', text: 'حدّث' }),
        el('button', { type: 'button', 'aria-label': 'إغلاق', text: '×', style: 'border-color:transparent;margin-inline-start:4px' })
      ])
    ]);
    bar.querySelector('#pwa-update-go').onclick = function () {
      if (reg.waiting) reg.waiting.postMessage({ type: 'SKIP_WAITING' }); else location.reload();
    };
    bar.querySelectorAll('button')[1].onclick = function () { bar.remove(); };
    document.body.append(bar);
  }

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('controllerchange', function () {
      if (reloading) return; reloading = true; location.reload();
    });
    window.addEventListener('load', function () {
      navigator.serviceWorker.register(BASE + 'sw.js', { scope: BASE }).then(function (reg) {
        if (reg.waiting && navigator.serviceWorker.controller) showUpdate(reg);
        reg.addEventListener('updatefound', function () {
          var w = reg.installing; if (!w) return;
          w.addEventListener('statechange', function () {
            if (w.state === 'installed' && navigator.serviceWorker.controller) showUpdate(reg);
          });
        });
        var last = Date.now();
        document.addEventListener('visibilitychange', function () {
          if (document.visibilityState === 'visible' && Date.now() - last > 3600e3) { last = Date.now(); reg.update().catch(function () {}); }
        });
        window.__pwaReg = reg;
      }).catch(function () {});
    });
  }

  /* ───────────── الدفتر: تصدير ───────────── */
  function collect() {
    var data = { athar: parse(lsGet(ATHAR), []), journey: parse(lsGet(JOURNEY), null), books: {}, prefs: {} };
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (BOOK_KEY.test(k)) data.books[k] = parse(localStorage.getItem(k), null);
      }
    } catch (e) {}
    PREFS.forEach(function (k) { var v = lsGet(k); if (v != null) data.prefs[k] = parse(v, v); });
    return data;
  }
  function stamp() { var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }

  function doExport(msg) {
    var payload = Object.assign({}, FORMAT, { exportedAt: new Date().toISOString(), data: collect() });
    var name = 'tajalliyat-diary-' + stamp() + '.json';
    var blob = new Blob([JSON.stringify(payload, null, 1)], { type: 'application/json' });
    var file; try { file = new File([blob], name, { type: 'application/json' }); } catch (e) {}
    if (isIOS && file && navigator.canShare && navigator.canShare({ files: [file] })) {      // iPhone: ورقة المشاركة → «حفظ في الملفات»
      navigator.share({ files: [file], title: 'دفتر تجليات الأسماء' }).then(function () { msg('تم تجهيز نسخة الدفتر.'); }).catch(function (e) {
        if (!e || e.name !== 'AbortError') msg('تعذّر التصدير، جرّب مرة أخرى.');
      });
      return;
    }
    var a = el('a', { href: URL.createObjectURL(blob), download: name });
    document.body.append(a); a.click(); a.remove();
    msg('حُفظت نسخة الدفتر في ملف على جهازك.');
  }

  /* ───────────── الدفتر: استيراد ودمج بلا مسح ───────────── */
  var isObj = function (v) { return v && typeof v === 'object' && !Array.isArray(v); };
  var stats;
  function mergeText(a, b) {
    if (a === b || !b) return a;
    if (!a) { stats.added++; return b; }
    if (a.indexOf(b) !== -1) return a;
    if (b.indexOf(a) !== -1) { stats.added++; return b; }
    stats.conflicts++;
    return a + '\n\n' + b;                                  // نحتفظ بالنصين معاً
  }
  function merge(local, imp, key) {
    if (imp == null) return local;
    if (local == null) { stats.added++; return imp; }
    if (typeof local === 'string' && typeof imp === 'string') return key === 'notes' || key === 'note' ? mergeText(local, imp) : (local || imp);
    if (typeof local === 'boolean' && typeof imp === 'boolean') return local || imp;
    if (Array.isArray(local) && Array.isArray(imp)) {
      var seen = {}; local.forEach(function (x) { seen[JSON.stringify(x)] = 1; });
      imp.forEach(function (x) { var s = JSON.stringify(x); if (!seen[s]) { seen[s] = 1; local.push(x); stats.added++; } });
      return local;
    }
    if (isObj(local) && isObj(imp)) {
      Object.keys(imp).forEach(function (k) {
        if (k === '__proto__' || k === 'constructor' || k === 'prototype') return;
        local[k] = (k in local) ? (key === 'notes' ? mergeText(String(local[k] || ''), String(imp[k] || '')) : merge(local[k], imp[k], k)) : (stats.added++, imp[k]);
      });
      return local;
    }
    return local;                                           // نوعان مختلفان: يبقى المحلي
  }

  function validate(o) {
    if (!isObj(o)) return null;
    if (o.app === 'tajalli-athar' && Array.isArray(o.entries)) o = { data: { athar: o.entries } };      // نسخة «أثر الاسم» القديمة
    else if (o.app !== FORMAT.app || o.kind !== FORMAT.kind || !Number.isInteger(o.version) || o.version > FORMAT.version || !isObj(o.data)) return null;
    var d = o.data, out = { athar: [], journey: null, books: {}, prefs: {} };
    if (d.athar != null) {
      if (!Array.isArray(d.athar)) return null;
      for (var i = 0; i < d.athar.length; i++) { var x = d.athar[i]; if (!isObj(x) || x.id == null) return null; }
      out.athar = d.athar;
    }
    if (d.journey != null) { if (!isObj(d.journey) || (d.journey.done != null && !isObj(d.journey.done)) || (d.journey.notes != null && !isObj(d.journey.notes))) return null; out.journey = d.journey; }
    if (d.books != null) {
      if (!isObj(d.books)) return null;
      for (var k in d.books) { if (!BOOK_KEY.test(k) || !(d.books[k] == null || isObj(d.books[k]))) return null; out.books[k] = d.books[k]; }
    }
    if (d.prefs != null) {
      if (!isObj(d.prefs)) return null;
      PREFS.forEach(function (k) { if (k in d.prefs) out.prefs[k] = d.prefs[k]; });
    }
    return out;
  }

  function apply(imp) {
    stats = { added: 0, conflicts: 0 };
    if (imp.athar.length) {                                                              // اتحاد حسب المعرّف
      var cur = parse(lsGet(ATHAR), []), have = {};
      if (!Array.isArray(cur)) cur = [];
      cur.forEach(function (x) { have[String(x && x.id)] = 1; });
      imp.athar.forEach(function (x) { if (!have[String(x.id)]) { cur.push(x); have[String(x.id)] = 1; stats.added++; } });
      cur.sort(function (a, b) { return (b && b.created || 0) - (a && a.created || 0); });
      lsSet(ATHAR, JSON.stringify(cur));
    }
    if (imp.journey) {
      var j = parse(lsGet(JOURNEY), null); if (!isObj(j)) j = { done: {}, notes: {} };
      j.done = isObj(j.done) ? j.done : {}; j.notes = isObj(j.notes) ? j.notes : {};
      var done = merge(j.done, imp.journey.done || {}, 'done'), notes = merge(j.notes, imp.journey.notes || {}, 'notes');
      j.done = done; j.notes = notes;
      Object.keys(imp.journey).forEach(function (k) { if (!(k in j)) j[k] = imp.journey[k]; });
      lsSet(JOURNEY, JSON.stringify(j));
    }
    Object.keys(imp.books).forEach(function (k) {
      var l = parse(lsGet(k), null);
      lsSet(k, JSON.stringify(l == null ? (stats.added++, imp.books[k]) : merge(l, imp.books[k], k)));
    });
    Object.keys(imp.prefs).forEach(function (k) { if (lsGet(k) == null) lsSet(k, JSON.stringify(imp.prefs[k])); });   // التفضيلات: لا تُستبدل
    return stats;
  }

  function doImport(file, msg) {
    if (file.size > MAX_IMPORT) { msg('الملف كبير جداً، ليس نسخة دفتر.'); return; }
    var r = new FileReader();
    r.onload = function () {
      var imp; try { imp = validate(JSON.parse(r.result)); } catch (e) { imp = null; }
      if (!imp) { msg('هذا الملف ليس نسخة دفتر من «تجليات الأسماء».'); return; }
      var s = apply(imp);
      msg('تم الدمج: ' + s.added + ' عنصر جديد' + (s.conflicts ? ('، و' + s.conflicts + ' ملاحظة حُفظ نصاها معاً') : '') + '. لم يُحذف شيء. سيُحدَّث العرض الآن…');
      setTimeout(function () { location.reload(); }, 1600);
    };
    r.onerror = function () { msg('تعذّرت قراءة الملف.'); };
    r.readAsText(file);
  }

  /* ───────────── لوحة التثبيت والدفتر ───────────── */
  function buildPanel() {
    if (document.getElementById('pwa-panel')) return;
    var msgEl = el('p', { id: 'pwa-msg', role: 'status' });
    var msg = function (t) { msgEl.textContent = t; };
    var panel = el('section', { id: 'pwa-panel', 'aria-label': 'التطبيق ونسخة الدفتر' });
    panel.append(el('h2', { text: standalone ? 'نسخة الدفتر' : (legacyAndroid ? 'اختصار على الشاشة الرئيسية' : 'ثبّت التطبيق') }));
    if (!standalone && !legacyAndroid) panel.append(el('p', { text: 'صدّر دفترك قبل التثبيت حتى تنقله.' }));
    var row = el('div', { class: 'pwa-row' });
    var exp = el('button', { type: 'button', id: 'pwa-export', text: 'تصدير الدفتر' });
    var imp = el('button', { type: 'button', id: 'pwa-import', text: 'استيراد الدفتر' });
    var file = el('input', { type: 'file', accept: 'application/json,.json', hidden: '', id: 'pwa-file' });
    exp.onclick = function () { doExport(msg); };
    imp.onclick = function () { file.click(); };
    file.onchange = function () { if (file.files[0]) doImport(file.files[0], msg); file.value = ''; };
    row.append(exp, imp, file);
    var inst = el('button', { type: 'button', id: 'pwa-install', text: 'ثبّت التطبيق', hidden: '' });
    row.append(inst);
    panel.append(row, msgEl);

    // أندرويد/كروم: زر واحد، يظهر مرة واحدة فقط
    var deferred = null;
    window.addEventListener('beforeinstallprompt', function (e) {
      e.preventDefault();
      if (standalone || legacyAndroid || lsGet(LS.install)) return;
      deferred = e; inst.hidden = false;
    });
    inst.onclick = function () {
      if (!deferred) return;
      var d = deferred; deferred = null; inst.hidden = true; lsSet(LS.install, String(Date.now()));
      d.prompt(); d.userChoice.then(function (c) { msg(c && c.outcome === 'accepted' ? 'تم التثبيت.' : ''); });
    };
    window.addEventListener('appinstalled', function () { inst.hidden = true; lsSet(LS.install, String(Date.now())); });

    // الجهاز القديم: تلميح الاختصار بدل التثبيت
    if (legacyAndroid && !standalone && !lsGet(LS.legacy)) {
      var lclose = el('button', { type: 'button', 'aria-label': 'إغلاق التلميح', text: '×' });
      var lhint = el('div', { class: 'pwa-hint', role: 'note' }, [
        el('span', { text: 'من قائمة Chrome اختر «إضافة إلى الشاشة الرئيسية» ثم «إنشاء اختصار». يفتح الموقع ويعمل بدون إنترنت.' }), lclose]);
      lclose.onclick = function () { lsSet(LS.legacy, String(Date.now())); lhint.remove(); };
      panel.append(lhint);
    }

    // iPhone: تلميح قابل للإغلاق، لا يتكرر بعد إغلاقه
    if (isIOS && !standalone && !lsGet(LS.ios)) {
      var close = el('button', { type: 'button', 'aria-label': 'إغلاق التلميح', text: '×' });
      var hint = el('div', { class: 'pwa-hint', role: 'note' }, [
        el('span', { text: 'للتثبيت على iPhone: اضغط زر المشاركة في Safari، ثم «إضافة إلى الشاشة الرئيسية».' }), close]);
      close.onclick = function () { lsSet(LS.ios, String(Date.now())); hint.remove(); };
      panel.append(hint);
    }

    var foot = document.querySelector('footer');
    if (foot && foot.parentNode) foot.parentNode.insertBefore(panel, foot);
    else (document.querySelector('main') || document.body).after(panel);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', buildPanel); else buildPanel();

  window.__pwa = { collect: collect, validate: validate, apply: apply };   // للاختبار الآلي
})();
