# tajalliyat backend

Deployed to `/backend` on the hosting. `_private/config.php` is created on the server only and never committed.

## الإحصاء المجهول (`api/hit.php` و`api/stats.php`)
- `hit.php`: يستقبل أحداثاً رقمية فقط من الموقع (نوع + عنصر من قوائم مسموحة)؛ لا يحفظ IP ولا نصاً حراً. يحتاج جدولي `stats_daily` و`stats_rl` (ملف SQL يُشغَّل يدوياً في phpMyAdmin ولا يُحفظ في الريبو). قبل وجود الجداول يرد `503 not_ready` ولا يؤثر على الموقع.
- `stats.php`: لوحة عرض محمية بـ `stats_token` (16 حرفاً على الأقل) في `config.php` على الخادم فقط. بدونه ترد اللوحة بأنها غير مفعّلة.
- مفاتيح `config.php` الاختيارية: `stats_token` و`stats_tz`. راجع `_private/config.sample.php`.
- `_private/labels.json`: أسماء عربية للمعرّفات في اللوحة؛ يُعاد توليده عند إضافة أسماء جديدة.
- الاختبار: `php tests/stats_test.php` (SQLite في الذاكرة).
