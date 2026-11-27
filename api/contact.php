<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

$base = dirname(__DIR__) . '/_private';
$cfgFile = $base . '/config.php';
if (!is_file($cfgFile)) {
    http_response_code(503);
    echo json_encode(['ok' => false, 'error' => 'not_configured']);
    exit;
}

require_once $base . '/contact_lib.php';
$cfg = require $cfgFile;

try {
    $pdo = new PDO($cfg['dsn'], $cfg['db_user'], $cfg['db_pass'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    [$status, $payload] = handle_contact($cfg, $_SERVER, $_POST, $pdo, 'send_mail_via_php');
} catch (Throwable $e) {
    error_log('contact.php: ' . $e->getMessage());
    $status = 500;
    $payload = ['ok' => false, 'error' => 'server_error'];
}

http_response_code($status);
echo json_encode($payload, JSON_UNESCAPED_UNICODE);
