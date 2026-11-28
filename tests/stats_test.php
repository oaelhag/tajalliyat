<?php
// php tests/stats_test.php   (SQLite في الذاكرة؛ لا يلمس أي قاعدة حقيقية)
declare(strict_types=1);
require __DIR__ . '/../_private/stats_lib.php';

$fails = 0;
function ok(bool $c, string $m): void { global $fails; echo ($c ? 'PASS ' : 'FAIL ') . $m . "\n"; if (!$c) $fails++; }

function db(): PDO {
    $p = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
    $p->exec('CREATE TABLE stats_daily (day TEXT NOT NULL, kind TEXT NOT NULL, item TEXT NOT NULL DEFAULT "", n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, kind, item))');
    $p->exec('CREATE TABLE stats_rl (ip_hash TEXT NOT NULL, bucket INTEGER NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (ip_hash, bucket))');
    return $p;
}
$cfg = ['origins' => ['https://tajalliyat.com'], 'ip_salt' => 'salt', 'stats_tz' => 'Africa/Cairo'];
$ua = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/140 Mobile Safari/537.36';
$srv = ['REQUEST_METHOD' => 'POST', 'HTTP_ORIGIN' => 'https://tajalliyat.com', 'HTTP_USER_AGENT' => $ua, 'REMOTE_ADDR' => '203.0.113.7'];
$t0 = 1795867200; // 2026-11-28 12:00 UTC

// 1) طلب سليم يُسجَّل
$pdo = db();
[$st, $pl] = handle_hit($cfg, $srv, json_encode(['e' => [['visit', ''], ['device', ''], ['name', 'rahman'], ['feeling', 'sad'], ['search', 'hit'], ['search_name', 'latif'], ['share', 'whatsapp']]]), $pdo, $t0);
ok($st === 200 && $pl['n'] === 7, 'valid events are recorded (7)');
$T = stats_totals($pdo, '2026-11-01');
ok(($T['name']['rahman'] ?? 0) === 1 && ($T['feeling']['sad'] ?? 0) === 1 && ($T['visit'][''] ?? 0) === 1, 'totals aggregate by kind and item');
[$st, $pl] = handle_hit($cfg, $srv, json_encode(['e' => [['name', 'rahman']]]), $pdo, $t0 + 5);
ok(stats_totals($pdo, '2026-11-01')['name']['rahman'] === 2, 'second view increments the counter');

// 2) رفض
ok(handle_hit($cfg, ['REQUEST_METHOD' => 'GET'] + $srv, '{}', $pdo, $t0)[0] === 405, 'GET → 405');
ok(handle_hit($cfg, ['HTTP_ORIGIN' => 'https://evil.example'] + $srv, '{"e":[["visit",""]]}', $pdo, $t0)[0] === 403, 'foreign origin → 403');
ok(handle_hit($cfg, array_diff_key($srv, ['HTTP_ORIGIN' => 1]), '{"e":[["visit",""]]}', $pdo, $t0)[0] === 403, 'missing origin → 403');
$n0 = (int)$pdo->query('SELECT SUM(n) FROM stats_daily')->fetchColumn();
foreach (['HeadlessChrome/120', 'Googlebot/2.1', 'curl/8.0', 'python-requests/2', ''] as $bad) {
    $r = handle_hit($cfg, ['HTTP_USER_AGENT' => $bad] + $srv, '{"e":[["visit",""]]}', $pdo, $t0);
    if ($r[1]['n'] !== 0) { ok(false, "bot ignored: $bad"); }
}
ok((int)$pdo->query('SELECT SUM(n) FROM stats_daily')->fetchColumn() === $n0, 'bots / headless / empty UA are not counted');

// 3) التحقق من الأحداث: لا نص حرّ ولا عناصر غريبة
$bad = [['name', 'Rahman'], ['name', '<script>'], ['name', str_repeat('a', 41)], ['search', 'مذنب وأخاف'], ['feeling', 'sad; DROP TABLE'], ['unknown', 'x'], ['page', 'a/b'], ['visit', 'x'], ['ref', 'https://x.com/q?s=1'], 'oops', [5, 'x'], ['share', 'email']];
$before = (int)$pdo->query('SELECT SUM(n) FROM stats_daily')->fetchColumn();
[$st, $pl] = handle_hit($cfg, $srv, json_encode(['e' => $bad]), $pdo, $t0 + 10);
ok($pl['n'] === 0 && (int)$pdo->query('SELECT SUM(n) FROM stats_daily')->fetchColumn() === $before, 'invalid kinds/items/free text are all rejected');
ok(stats_parse(str_repeat('x', 5000)) === [] && stats_parse('not json') === [] && stats_parse('{"e":"x"}') === [], 'oversized / malformed bodies are ignored');
ok(count(stats_parse(json_encode(['e' => array_fill(0, 30, ['visit', ''])]))) === STATS_MAX_EVENTS, 'at most 12 events per request');

// 4) حدّ المعدّل
$pdo = db();
$ok = 0; $blocked = 0;
for ($i = 0; $i < 10; $i++) { $r = handle_hit($cfg, $srv, json_encode(['e' => array_fill(0, 10, ['visit', ''])]), $pdo, $t0); $r[0] === 200 ? $ok++ : $blocked++; }
ok($ok === 4 && $blocked === 6, "rate limit: 40 events/minute per hashed IP ($ok ok, $blocked blocked)");
ok(handle_hit($cfg, $srv, '{"e":[["visit",""]]}', $pdo, $t0 + 61)[0] === 200, 'limit resets next minute');
ok(handle_hit($cfg, ['REMOTE_ADDR' => '198.51.100.9'] + $srv, '{"e":[["visit",""]]}', $pdo, $t0)[0] === 200, 'another IP is not affected');
$rl = $pdo->query('SELECT ip_hash FROM stats_rl')->fetchAll(PDO::FETCH_COLUMN);
ok(!array_filter($rl, fn($h) => strpos($h, '203.0.113') !== false) && strlen($rl[0]) === 64, 'only a salted hash is kept for rate limiting (no raw IP)');

// 5) سقف العناصر الجديدة في اليوم
$pdo = db();
for ($i = 0; $i < STATS_MAX_ITEMS_PER_KIND_DAY + 20; $i++) stats_bump($pdo, '2026-11-28', 'name', 'x' . chr(97 + intdiv($i, 26) % 26) . chr(97 + $i % 26));
$c = (int)$pdo->query("SELECT COUNT(*) FROM stats_daily WHERE kind='name'")->fetchColumn();
ok($c <= STATS_MAX_ITEMS_PER_KIND_DAY, "new items per kind/day are capped ($c)");

// 5b) أخطاء الكتابة لا تُبلع (كانت تُرجع نجاحاً كاذباً): جدول ببنية خاطئة → استثناء، لا n=1
$bad = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$bad->exec('CREATE TABLE stats_daily (day TEXT NOT NULL, kind TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, kind))');   // ينقصه عمود item
$threw = false; try { stats_bump($bad, '2026-11-28', 'name', 'rahman'); } catch (Throwable $e) { $threw = true; }
ok($threw, 'a failing INSERT is surfaced instead of being swallowed as success');
ok(stats_error_code(new PDOException('x', 0)) !== '' && strpos(stats_error_code($e), 'rahman') === false, 'error code helper exposes no message text');
$dup = db(); stats_bump($dup, '2026-11-28', 'name', 'rahman');
$dupE = null; try { $dup->prepare('INSERT INTO stats_daily (day, kind, item, n) VALUES (?,?,?,1)')->execute(['2026-11-28', 'name', 'rahman']); } catch (PDOException $x) { $dupE = $x; }
ok($dupE !== null && stats_is_duplicate($dupE), 'duplicate-key errors are recognised (the only error that may be absorbed)');

// 6) اليوم بحسب المنطقة الزمنية
$pdo = db();
handle_hit($cfg, $srv, '{"e":[["visit",""]]}', $pdo, 1795906800);      // 2026-11-28 22:20 UTC = 00:20 يوم 29 في القاهرة
ok($pdo->query("SELECT day FROM stats_daily")->fetchColumn() === '2026-11-29', 'day follows configured timezone (Africa/Cairo)');

// 7) لوحة العرض: كلمة سر، تسمية عربية، لا تسريب
$dir = sys_get_temp_dir() . '/tj_stats_' . getmypid();
mkdir("$dir/api", 0777, true); mkdir("$dir/_private", 0777, true);
copy(__DIR__ . '/../api/stats.php', "$dir/api/stats.php"); copy(__DIR__ . '/../_private/stats_lib.php', "$dir/_private/stats_lib.php"); copy(__DIR__ . '/../_private/labels.json', "$dir/_private/labels.json");
$dbf = "$dir/t.db"; $p2 = new PDO('sqlite:' . $dbf); $p2->exec('CREATE TABLE stats_daily (day TEXT, kind TEXT, item TEXT, n INTEGER, PRIMARY KEY(day,kind,item)); CREATE TABLE stats_rl (ip_hash TEXT, bucket INTEGER, n INTEGER, PRIMARY KEY(ip_hash,bucket));');
$today = (new DateTimeImmutable('now', new DateTimeZone('UTC')))->format('Y-m-d');
foreach ([['visit', '', 5], ['device', '', 3], ['name', 'rahman', 4], ['name', 'latif', 2], ['feeling', 'sad', 3], ['search', 'miss', 1], ['ref', 'google', 2]] as [$k, $i, $n]) $p2->prepare('INSERT INTO stats_daily VALUES (?,?,?,?)')->execute([$today, $k, $i, $n]);
$tok = 'abcdefghijklmnop1234';
file_put_contents("$dir/_private/config.php", "<?php return ['dsn'=>'sqlite:$dbf','db_user'=>'','db_pass'=>'','origins'=>[],'stats_token'=>'$tok','stats_tz'=>'UTC'];");
$run = function (array $post, string $method = 'POST') use ($dir): array {
    $code = '$_SERVER["REQUEST_METHOD"]="' . $method . '";$_POST=' . var_export($post, true) . ';ob_start();register_shutdown_function(function(){file_put_contents("php://stdout", "\n#CODE=".http_response_code());});include "' . $dir . '/api/stats.php";';
    return [shell_exec('php -d display_errors=0 -r ' . escapeshellarg($code) . ' 2>/dev/null') ?? ''];
};
[$out] = $run([], 'GET');                          ok(strpos($out, 'type="password"') !== false && strpos($out, 'الرحمن') === false, 'GET shows only the password form');
[$out] = $run(['k' => 'wrong-wrong-wrong-1']);     ok(strpos($out, 'كلمة السر غير صحيحة') !== false && strpos($out, 'الرحمن') === false, 'wrong token: no data');
[$out] = $run(['k' => $tok, 'days' => 7]);
ok(strpos($out, 'الرحمن') !== false && strpos($out, 'اللطيف') !== false && strpos($out, 'حزين') !== false && strpos($out, 'جوجل') !== false, 'correct token: Arabic labels for names, feelings, referrers');
ok(strpos($out, 'diag: rows=7') !== false && strpos($out, 'sum_n=') !== false, 'dashboard shows a one-line diagnostic (row count, day range, window)');
ok(strpos($out, '<script') === false && strpos($out, 'noindex') !== false, 'dashboard has no scripts and is noindex');
// أول دخول (بلا حقل days) يجب أن يعرض بيانات اليوم: كان days=0 يقلب النافذة فتظهر أصفار
$p2->exec("INSERT OR REPLACE INTO stats_daily VALUES ('$today','visit','',9)");
[$out] = $run(['k' => $tok]);
ok(strpos($out, '<b>9</b>') !== false && preg_match('/window=(\d{4}-\d\d-\d\d)\.\.(\d{4}-\d\d-\d\d)/', $out, $w) && $w[1] <= $w[2], 'first login (no days field): default 30-day window includes today and shows the data');
[$out] = $run(['k' => $tok, 'days' => 'garbage']);
ok(strpos($out, '<b>9</b>') !== false, 'invalid days value falls back to 30');
// قاعدة فاضية، أو صفوف بلا «زيارة/جهاز»: يجب ألا تنهار اللوحة (كان max() يرمي TypeError → 500)
$p2->exec('DELETE FROM stats_daily');
[$out] = $run(['k' => $tok, 'days' => 30]);
ok(strpos($out, 'إحصاء تجليات الأسماء') !== false && strpos($out, 'Fatal') === false && strpos($out, 'لا بيانات بعد') !== false, 'dashboard renders with empty tables (no crash)');
$p2->prepare('INSERT INTO stats_daily VALUES (?,?,?,?)')->execute([$today, 'name', 'rahman', 2]);
[$out] = $run(['k' => $tok, 'days' => 30]);
ok(strpos($out, 'الرحمن') !== false && strpos($out, 'Fatal') === false, 'dashboard renders with rows but no visit/device rows');
$p2->exec('DROP TABLE stats_daily');                                  // خطأ غير متوقع: تظهر رسالة لصاحب الموقع لا 500 صامتة
[$out] = $run(['k' => $tok, 'days' => 30]);
ok(strpos($out, 'الجداول غير جاهزة') !== false || strpos($out, 'خطأ في اللوحة') !== false, 'missing tables: readable message, not a blank 500');
file_put_contents("$dir/_private/config.php", "<?php return ['dsn'=>'sqlite:$dbf','db_user'=>'','db_pass'=>'','origins'=>[],'stats_token'=>'CHANGE_ME_LONG_RANDOM'];");
[$out] = $run(['k' => 'CHANGE_ME_LONG_RANDOM']);  ok(strpos($out, 'غير مفعّلة') !== false && strpos($out, 'الرحمن') === false, 'sample/short token keeps the dashboard disabled');
echo $fails ? "\n$fails FAILED\n" : "\nALL PASSED\n"; exit($fails ? 1 : 0);
