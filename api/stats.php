<?php
declare(strict_types=1);

/** لوحة الإحصاء (أرقام مجمّعة فقط). محمية بكلمة سر `stats_token` في config.php (تُكتب هناك يدوياً على الخادم). */
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex, nofollow');
header("Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'");
header('Referrer-Policy: no-referrer');

$base = dirname(__DIR__) . '/_private';
$cfgFile = $base . '/config.php';
$h = static fn($s): string => htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');

function page(string $title, string $body, int $code = 200): void
{
    http_response_code($code);
    echo '<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
       . '<meta name="robots" content="noindex,nofollow"><title>' . htmlspecialchars($title) . '</title><style>'
       . ':root{--bg:#F1F2F5;--ink:#1B2338;--card:#fff;--line:#d9dce4;--gold:#8F600F;--bar:#c9a24e}'
       . '@media(prefers-color-scheme:dark){:root{--bg:#0E1324;--ink:#E9E6DD;--card:#161d33;--line:#2a3350;--gold:#E3B45C;--bar:#9b7a2f}}'
       . '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.8 system-ui,sans-serif;padding:16px}'
       . 'main{max-width:900px;margin:0 auto}h1{font-size:1.4rem;color:var(--gold)}h2{font-size:1.1rem;margin:22px 0 6px;color:var(--gold)}'
       . '.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}.c{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px}.c b{display:block;font-size:1.6rem}'
       . 'table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}td,th{padding:6px 12px;text-align:start;border-bottom:1px solid var(--line)}'
       . 'td.n{width:5em;font-variant-numeric:tabular-nums}.bar{height:8px;background:var(--bar);border-radius:4px}.mut{opacity:.7;font-size:.9rem}'
       . 'input,button,select{font:inherit;padding:8px 12px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink)}button{cursor:pointer;color:var(--gold);border-color:var(--gold)}'
       . '</style></head><body><main>' . $body . '</main></body></html>';
    exit;
}

$form = static fn(string $err = ''): string =>
    '<h1>إحصاء تجليات الأسماء</h1>' . ($err !== '' ? '<p style="color:#b3261e">' . htmlspecialchars($err) . '</p>' : '')
    . '<form method="post"><p><label>كلمة السر<br><input type="password" name="k" autocomplete="current-password" required minlength="8" style="width:100%;max-width:22em"></label></p><button type="submit">دخول</button></form>';

if (!is_file($cfgFile)) page('غير مهيّأ', '<h1>غير مهيّأ</h1>', 503);
require_once $base . '/stats_lib.php';
$cfg = require $cfgFile;
$token = (string)($cfg['stats_token'] ?? '');
if (strlen($token) < 16 || $token === 'CHANGE_ME_LONG_RANDOM') page('غير مهيّأ', '<h1>اللوحة غير مفعّلة</h1><p>أضف <code>stats_token</code> (16 حرفاً على الأقل) إلى config.php على الخادم.</p>', 503);

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') page('دخول', $form());
if (!hash_equals($token, (string)($_POST['k'] ?? ''))) { sleep(1); page('دخول', $form('كلمة السر غير صحيحة'), 403); }

// أي خطأ غير متوقع بعد كلمة السر الصحيحة: يُسجَّل ويظهر سببه لصاحب الموقع فقط (بدل صفحة 500 صامتة)
set_exception_handler(static function (Throwable $e) {
    error_log('stats.php: ' . $e);
    page('خطأ', '<h1>خطأ في اللوحة</h1><p dir="ltr">' . htmlspecialchars(get_class($e) . ': ' . $e->getMessage() . ' (line ' . $e->getLine() . ')') . '</p>', 500);
});

try {
    $pdo = new PDO($cfg['dsn'], $cfg['db_user'], $cfg['db_pass'], [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
    $req = (int)($_POST['days'] ?? 30);                                  // أول دخول بلا حقل days: الافتراضي 30 (كان يُقرأ ثانية فيصير 0 ⇒ نافذة مقلوبة وأصفار)
    $days = in_array($req, [7, 30, 90, 365], true) ? $req : 30;
    $tz = new DateTimeZone($cfg['stats_tz'] ?? 'UTC');
    $today = new DateTimeImmutable('now', $tz);
    $from = $today->modify('-' . ($days - 1) . ' days')->format('Y-m-d');
    $T = stats_totals($pdo, $from);
    $series = stats_series($pdo, $from);
    $diag = $pdo->query('SELECT COUNT(*) AS c, MIN(day) AS a, MAX(day) AS b, COALESCE(SUM(n), 0) AS s FROM stats_daily')->fetch(PDO::FETCH_ASSOC);
} catch (Throwable $e) {
    error_log('stats.php: ' . $e->getMessage());
    page('خطأ', '<h1>الجداول غير جاهزة</h1><p>شغّل ملف SQL الخاص بالإحصاء في phpMyAdmin أولاً.</p>', 503);
}

$labels = is_file($base . '/labels.json') ? (json_decode((string)file_get_contents($base . '/labels.json'), true) ?: []) : [];
$nameOf = static fn(string $id): string => ($labels['names'][$id] ?? $id);
$feelOf = static fn(string $id): string => ($labels['feelings'][$id] ?? $id);
$ar = ['entry' => ['home' => 'الرئيسية', 'name' => 'صفحة اسم', 'feel' => 'صفحة شعور', 'feel_hub' => 'قلبي الآن', 'books' => 'الكتب', 'book' => 'كتاب', 'guide' => 'اسم يناسب حالك', 'athar' => 'أثر الاسم', 'other' => 'أخرى'],
       'ref' => ['direct' => 'مباشر', 'google' => 'جوجل', 'bing' => 'بنج', 'duckduckgo' => 'دك دك جو', 'yandex' => 'ياندكس', 'whatsapp' => 'واتساب', 'facebook' => 'فيسبوك', 'instagram' => 'إنستجرام', 'twitter' => 'إكس/تويتر', 'telegram' => 'تيليجرام', 'youtube' => 'يوتيوب', 'other' => 'أخرى'],
       'page' => ['home' => 'الرئيسية', 'names' => 'الأسماء', 'feel_hub' => 'قلبي الآن', 'journey' => 'رحلتي', 'videos' => 'فيديوهات', 'guide' => 'اسم يناسب حالك', 'athar' => 'أثر الاسم', 'books' => 'الكتب'],
       'tab' => ['tajalliyat' => 'التجليات', 'questions' => 'أسئلة التأمل', 'tasks' => 'المهام العملية'],
       'aud' => ['boy' => 'طفل', 'girl' => 'طفلة', 'youngman' => 'شاب', 'youngwoman' => 'شابة', 'father' => 'أب', 'mother' => 'أم'],
       'share' => ['copy' => 'نسخ', 'whatsapp' => 'واتساب', 'card' => 'بطاقة', 'page' => 'رابط صفحة'],
       'pwa' => ['install_click' => 'ضغط زر التثبيت', 'install_accepted' => 'تم التثبيت', 'export' => 'تصدير الدفتر', 'import' => 'استيراد الدفتر', 'standalone_open' => 'فتح من التطبيق المثبّت'],
       'search' => ['hit' => 'بحث وُجدت له نتيجة', 'miss' => 'بحث بلا نتيجة']];

$tbl = static function (string $title, array $rows, callable $label, int $limit = 15) use ($h): string {
    arsort($rows);
    $rows = array_slice($rows, 0, $limit, true);
    if (!$rows) return '<h2>' . $h($title) . '</h2><p class="mut">لا بيانات بعد.</p>';
    $max = max($rows);
    $o = '<h2>' . $h($title) . '</h2><table>';
    foreach ($rows as $k => $n) $o .= '<tr><td>' . $h($label((string)$k)) . '</td><td class="n">' . (int)$n . '</td><td style="width:35%"><div class="bar" style="width:' . max(2, (int)round(100 * $n / $max)) . '%"></div></td></tr>';
    return $o . '</table>';
};
$map = static fn(string $kind) => static fn(string $k): string => $ar[$kind][$k] ?? $k;

$visits = array_sum($T['visit'] ?? []);
$devices = array_sum($T['device'] ?? []);
$d0 = $today->format('Y-m-d');
$todayV = $series[$d0]['visit'] ?? 0;
$todayD = $series[$d0]['device'] ?? 0;

$o = '<h1>إحصاء تجليات الأسماء</h1>'
   . '<form method="post"><input type="hidden" name="k" value="' . $h($_POST['k']) . '"><label>الفترة: <select name="days" onchange="this.form.submit()">';
foreach ([7 => 'آخر 7 أيام', 30 => 'آخر 30 يوماً', 90 => 'آخر 90 يوماً', 365 => 'آخر سنة'] as $v => $t) $o .= '<option value="' . $v . '"' . ($v === $days ? ' selected' : '') . '>' . $t . '</option>';
$o .= '</select></label> <noscript><button>عرض</button></noscript></form>'
    . '<p class="mut">أرقام مجمّعة مجهولة: بلا كوكيز ولا IP ولا نص مكتوب. «الأجهزة» تقدير لعدد المتصفحات المختلفة في اليوم، وليست أشخاصاً بأعيانهم. التوقيت: ' . $h($cfg['stats_tz'] ?? 'UTC') . '.</p>'
    . '<div class="cards"><div class="c">زيارات (الفترة)<b>' . $visits . '</b></div><div class="c">أجهزة (مجموع أيام الفترة)<b>' . $devices . '</b></div>'
    . '<div class="c">زيارات اليوم<b>' . $todayV . '</b></div><div class="c">أجهزة اليوم<b>' . $todayD . '</b></div></div>';

$o .= '<h2>حسب اليوم</h2><table><tr><th>اليوم</th><th>زيارات</th><th>أجهزة</th><th></th></tr>';
$maxV = max(array_merge([1], array_map(static fn($r) => (int)($r['visit'] ?? 0), array_values($series))));   // مصفوفة: تصلح حتى لو لا توجد أيام
foreach (array_reverse($series, true) as $d => $r) $o .= '<tr><td>' . $h($d) . '</td><td class="n">' . ($r['visit'] ?? 0) . '</td><td class="n">' . ($r['device'] ?? 0) . '</td><td style="width:30%"><div class="bar" style="width:' . max(2, (int)round(100 * ($r['visit'] ?? 0) / $maxV)) . '%"></div></td></tr>';
$o .= '</table>';

$o .= $tbl('الأسماء الأكثر مشاهدة', $T['name'] ?? [], $nameOf)
    . $tbl('المشاعر الأكثر اختياراً', $T['feeling'] ?? [], $feelOf, 20)
    . $tbl('الأسماء الأكثر بحثاً (عند تضييق البحث على ثلاثة أسماء أو أقل)', $T['search_name'] ?? [], $nameOf)
    . $tbl('نتائج البحث', $T['search'] ?? [], $map('search'))
    . $tbl('من أين دخلوا', $T['ref'] ?? [], $map('ref'))
    . $tbl('أول صفحة في الزيارة', $T['entry'] ?? [], $map('entry'))
    . $tbl('الأقسام', $T['page'] ?? [], static fn(string $k): string => $ar['page'][$k] ?? $k)
    . $tbl('تبويبات صفحة الاسم', $T['tab'] ?? [], $map('tab'))
    . $tbl('الفئة المختارة', $T['aud'] ?? [], $map('aud'))
    . $tbl('المشاركة', $T['share'] ?? [], $map('share'))
    . $tbl('التطبيق والدفتر', $T['pwa'] ?? [], $map('pwa'));
$o .= '<p class="mut" dir="ltr" style="margin-top:28px">diag: rows=' . (int)$diag['c'] . ' | first_day=' . $h($diag['a'] ?? '-') . ' | last_day=' . $h($diag['b'] ?? '-') . ' | sum_n=' . (int)$diag['s']
    . ' | window=' . $h($from) . '..' . $h($d0) . ' (' . $h($cfg['stats_tz'] ?? 'UTC') . ') | server_now_utc=' . gmdate('Y-m-d H:i') . '</p>';
page('إحصاء', $o);
