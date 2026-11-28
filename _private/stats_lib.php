<?php
declare(strict_types=1);

/**
 * إحصاء مجهول ومجمّع: أرقام يومية فقط (يوم، نوع، عنصر، عدد).
 * لا يُحفظ IP ولا معرّف ولا نص يكتبه الزائر ولا عنوان الصفحة الكامل.
 * الجدول stats_daily(day, kind, item, n) وجدول stats_rl للحدّ من التلاعب (بصمة مشفّرة مؤقتة تُحذف خلال ساعتين).
 */

const STATS_MAX_EVENTS = 12;          // أحداث في الطلب الواحد
const STATS_MAX_BODY = 2048;          // بايت
const STATS_RATE_PER_MINUTE = 40;     // أحداث لكل بصمة في الدقيقة
const STATS_MAX_ITEMS_PER_KIND_DAY = 300; // يمنع إغراق الجدول بعناصر عشوائية

/** نوع الحدث → نمط العنصر المسموح (أي شيء خارج ذلك يُرفض). */
function stats_kinds(): array
{
    $id = '/^[a-z]{2,24}$/';
    return [
        'visit'       => '/^$/',                                                  // زيارة (جلسة متصفح)
        'device'      => '/^$/',                                                  // جهاز/متصفح فريد في اليوم (تقريبي)
        'entry'       => '/^(home|name|feel|feel_hub|books|book|guide|athar|other)$/', // أول صفحة في الجلسة
        'page'        => '/^(home|names|feel_hub|journey|videos|guide|athar|books|book_[a-z]{3,10})$/',
        'name'        => $id,                                                     // مشاهدة اسم
        'feeling'     => $id,                                                     // مشاهدة شعور
        'search'      => '/^(hit|miss)$/',                                        // بحث بلا نص
        'search_name' => $id,                                                     // اسم طابقه البحث (≤3 أسماء)
        'tab'         => '/^(tajalliyat|questions|tasks)$/',
        'aud'         => '/^(boy|girl|youngman|youngwoman|father|mother)$/',
        'share'       => '/^(copy|whatsapp|card|page)$/',
        'ref'         => '/^(direct|google|bing|duckduckgo|yandex|whatsapp|facebook|instagram|twitter|telegram|youtube|other)$/',
        'pwa'         => '/^(install_click|install_accepted|export|import|standalone_open)$/',
    ];
}

/** يقبل جسم الطلب (نص JSON: {"e":[["kind","item"],...]}) ويرجع أحداثاً صالحة فقط. */
function stats_parse(string $body): array
{
    if ($body === '' || strlen($body) > STATS_MAX_BODY) return [];
    $j = json_decode($body, true);
    if (!is_array($j) || !isset($j['e']) || !is_array($j['e'])) return [];
    $kinds = stats_kinds();
    $out = [];
    foreach (array_slice($j['e'], 0, STATS_MAX_EVENTS) as $e) {
        if (!is_array($e) || count($e) < 1 || !is_string($e[0])) continue;
        $kind = $e[0];
        $item = isset($e[1]) && is_string($e[1]) ? $e[1] : '';
        if (!isset($kinds[$kind]) || strlen($item) > 40 || !preg_match($kinds[$kind], $item)) continue;
        $out[] = [$kind, $item];
    }
    return $out;
}

function stats_is_bot(string $ua): bool
{
    return $ua === '' || (bool)preg_match('/bot|crawl|spider|slurp|headless|lighthouse|pingdom|monitor|preview|curl|wget|python|node-fetch|phantom/i', $ua);
}

/** حدّ المعدّل: بصمة IP مشفّرة بالملح + دقيقة. true = مسموح. */
function stats_rate_ok(PDO $pdo, string $ipHash, int $now, int $count): bool
{
    $bucket = intdiv($now, 60);
    $st = $pdo->prepare('SELECT n FROM stats_rl WHERE ip_hash = ? AND bucket = ?');
    $st->execute([$ipHash, $bucket]);
    $cur = $st->fetchColumn();
    if ($cur !== false && (int)$cur + $count > STATS_RATE_PER_MINUTE) return false;
    if ($cur === false) {
        try {
            $pdo->prepare('INSERT INTO stats_rl (ip_hash, bucket, n) VALUES (?,?,?)')->execute([$ipHash, $bucket, $count]);
        } catch (Throwable $e) {
            $pdo->prepare('UPDATE stats_rl SET n = n + ? WHERE ip_hash = ? AND bucket = ?')->execute([$count, $ipHash, $bucket]);
        }
    } else {
        $pdo->prepare('UPDATE stats_rl SET n = n + ? WHERE ip_hash = ? AND bucket = ?')->execute([$count, $ipHash, $bucket]);
    }
    if (random_int(1, 40) === 1) {                                                  // تنظيف: لا نحتفظ بالبصمات أكثر من ساعتين
        $pdo->prepare('DELETE FROM stats_rl WHERE bucket < ?')->execute([$bucket - 120]);
    }
    return true;
}

/** يزيد عدّاد (يوم، نوع، عنصر). يعمل على MySQL وSQLite: UPDATE أولاً ثم INSERT. */
function stats_bump(PDO $pdo, string $day, string $kind, string $item): bool
{
    $up = $pdo->prepare('UPDATE stats_daily SET n = n + 1 WHERE day = ? AND kind = ? AND item = ?');
    $up->execute([$day, $kind, $item]);
    if ($up->rowCount() > 0) return true;
    $cnt = $pdo->prepare('SELECT COUNT(*) FROM stats_daily WHERE day = ? AND kind = ?');
    $cnt->execute([$day, $kind]);
    if ((int)$cnt->fetchColumn() >= STATS_MAX_ITEMS_PER_KIND_DAY) return false;      // عنصر جديد فوق الحدّ: يُهمل
    try {
        $pdo->prepare('INSERT INTO stats_daily (day, kind, item, n) VALUES (?,?,?,1)')->execute([$day, $kind, $item]);
    } catch (Throwable $e) {                                                         // سباق مع طلب آخر: الصف صار موجوداً
        $up->execute([$day, $kind, $item]);
    }
    return true;
}

/**
 * يعالج طلباً واحداً. يرجع [status, payload].
 * $server: مصفوفة $_SERVER؛ $body: جسم الطلب؛ $now: وقت يونكس (للاختبار).
 */
function handle_hit(array $cfg, array $server, string $body, PDO $pdo, ?int $now = null): array
{
    $now = $now ?? time();
    if (($server['REQUEST_METHOD'] ?? '') !== 'POST') return [405, ['ok' => false, 'error' => 'method_not_allowed']];
    $origin = $server['HTTP_ORIGIN'] ?? '';
    if ($origin === '' || !in_array($origin, $cfg['origins'], true)) return [403, ['ok' => false, 'error' => 'forbidden']];
    if (stats_is_bot($server['HTTP_USER_AGENT'] ?? '')) return [200, ['ok' => true, 'n' => 0]];
    $events = stats_parse($body);
    if (!$events) return [200, ['ok' => true, 'n' => 0]];
    $ipHash = hash('sha256', ($cfg['ip_salt'] ?? '') . '|stats|' . ($server['REMOTE_ADDR'] ?? '0.0.0.0'));
    if (!stats_rate_ok($pdo, $ipHash, $now, count($events))) return [429, ['ok' => false, 'error' => 'too_many_requests']];
    $tz = new DateTimeZone($cfg['stats_tz'] ?? 'UTC');
    $day = (new DateTimeImmutable('@' . $now))->setTimezone($tz)->format('Y-m-d');
    $n = 0;
    foreach ($events as [$kind, $item]) {
        if (stats_bump($pdo, $day, $kind, $item)) $n++;
    }
    return [200, ['ok' => true, 'n' => $n]];
}

/** تجميع للوحة العرض: [kind => [item => n]] لفترة أيام. */
function stats_totals(PDO $pdo, string $fromDay): array
{
    $st = $pdo->prepare('SELECT kind, item, SUM(n) AS n FROM stats_daily WHERE day >= ? GROUP BY kind, item');
    $st->execute([$fromDay]);
    $out = [];
    foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $r) $out[$r['kind']][$r['item']] = (int)$r['n'];
    return $out;
}

function stats_series(PDO $pdo, string $fromDay): array
{
    $st = $pdo->prepare("SELECT day, kind, SUM(n) AS n FROM stats_daily WHERE day >= ? AND kind IN ('visit','device') GROUP BY day, kind ORDER BY day");
    $st->execute([$fromDay]);
    $out = [];
    foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $r) $out[$r['day']][$r['kind']] = (int)$r['n'];
    return $out;
}
