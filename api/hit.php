<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex');

$base = dirname(__DIR__) . '/_private';
$cfgFile = $base . '/config.php';
if (!is_file($cfgFile)) {
    http_response_code(503);
    echo json_encode(['ok' => false, 'error' => 'not_configured']);
    exit;
}

require_once $base . '/stats_lib.php';
$cfg = require $cfgFile;

try {
    $pdo = new PDO($cfg['dsn'], $cfg['db_user'], $cfg['db_pass'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    [$status, $payload] = handle_hit($cfg, $_SERVER, (string)file_get_contents('php://input', false, null, 0, STATS_MAX_BODY + 1), $pdo);
} catch (Throwable $e) {
    error_log('hit.php: ' . $e->getMessage());
    $status = 503;                                   // الجداول غير موجودة بعد أو خطأ في القاعدة: لا يؤثر على الموقع
    $payload = ['ok' => false, 'error' => 'not_ready', 'code' => stats_error_code($e)];   // رمز فقط (بلا رسالة) لتشخيص الإعداد
}

http_response_code($status);
echo json_encode($payload);
