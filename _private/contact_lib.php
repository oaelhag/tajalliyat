<?php
declare(strict_types=1);

/**
 * Handles one contact-form submission.
 * Returns [httpStatus, payload]. No output, no exit: easy to test.
 */
function handle_contact(array $cfg, array $server, array $post, PDO $pdo, callable $mailer): array
{
    if (($server['REQUEST_METHOD'] ?? '') !== 'POST') {
        return [405, ['ok' => false, 'error' => 'method_not_allowed']];
    }

    // Same-origin check (browsers always send Origin on fetch POST)
    $origin = $server['HTTP_ORIGIN'] ?? '';
    if ($origin === '' || !in_array($origin, $cfg['origins'], true)) {
        return [403, ['ok' => false, 'error' => 'forbidden']];
    }

    // Honeypot: real visitors never fill this hidden field
    if (trim((string)($post['website'] ?? '')) !== '') {
        return [200, ['ok' => true]]; // pretend success to bots
    }

    $name    = trim((string)($post['name'] ?? ''));
    $email   = trim((string)($post['email'] ?? ''));
    $message = trim((string)($post['message'] ?? ''));

    $len = static fn(string $s): int => function_exists('mb_strlen') ? mb_strlen($s, 'UTF-8') : strlen($s);

    if ($len($name) < 2 || $len($name) > 100
        || $len($email) > 190 || !filter_var($email, FILTER_VALIDATE_EMAIL)
        || $len($message) < 5 || $len($message) > 4000) {
        return [422, ['ok' => false, 'error' => 'invalid_input']];
    }

    // Rate limit by salted hash of the IP (raw IPs are never stored)
    $ip     = $server['REMOTE_ADDR'] ?? '0.0.0.0';
    $ipHash = hash('sha256', $cfg['ip_salt'] . '|' . $ip);

    $since = date('Y-m-d H:i:s', time() - 3600);
    $st = $pdo->prepare('SELECT COUNT(*) FROM contact_messages WHERE ip_hash = ? AND created_at >= ?');
    $st->execute([$ipHash, $since]);
    if ((int)$st->fetchColumn() >= (int)$cfg['rate_limit']) {
        return [429, ['ok' => false, 'error' => 'too_many_requests']];
    }

    $ins = $pdo->prepare(
        'INSERT INTO contact_messages (created_at, name, email, message, ip_hash, mail_sent) VALUES (?,?,?,?,?,0)'
    );
    $ins->execute([date('Y-m-d H:i:s'), $name, $email, $message, $ipHash]);
    $id = (int)$pdo->lastInsertId();

    // Notification is best-effort: the message is already saved
    $sent = false;
    try {
        $sent = (bool)$mailer($cfg, $name, $email, $message);
    } catch (Throwable $e) {
        $sent = false;
    }
    if ($sent) {
        $pdo->prepare('UPDATE contact_messages SET mail_sent = 1 WHERE id = ?')->execute([$id]);
    }

    return [200, ['ok' => true]];
}

/** Default mailer using PHP mail(); header injection is prevented by stripping CR/LF. */
function send_mail_via_php(array $cfg, string $name, string $email, string $message): bool
{
    $clean   = static fn(string $s): string => trim(preg_replace('/[\r\n]+/', ' ', $s));
    $subject = '=?UTF-8?B?' . base64_encode('رسالة جديدة من موقع تجليات الأسماء') . '?=';
    $body    = "الاسم: " . $clean($name) . "\nالبريد: " . $clean($email) . "\n\n" . $message;
    $headers = [
        'From: ' . $cfg['mail_from'],
        'Reply-To: ' . $clean($email),
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
    ];
    return mail($cfg['mail_to'], $subject, $body, implode("\r\n", $headers));
}
