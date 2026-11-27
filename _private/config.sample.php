<?php
// Copy to config.php and fill in. config.php must NEVER be committed to Git.
return [
    'dsn'        => 'mysql:host=127.0.0.1;port=3306;dbname=u639708989_tajalliyat;charset=utf8mb4',
    'db_user'    => 'u639708989_tajalliyat',
    'db_pass'    => 'CHANGE_ME',
    'ip_salt'    => 'CHANGE_ME_RANDOM_LONG_STRING',   // used to hash visitor IPs
    'mail_to'    => 'info@tajalliyat.com',            // where notifications go
    'mail_from'  => 'info@tajalliyat.com',            // must be a mailbox on the domain
    'origins'    => ['https://tajalliyat.com', 'https://www.tajalliyat.com'],
    'rate_limit' => 5,                                // messages per IP per hour
];
