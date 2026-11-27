#!/usr/bin/env bash
# يبني نسخة الموقع المنشورة على Hostinger من فرع main دون تعديله.
# الاستخدام: deploy/build_hostinger.sh <مجلد-الإخراج> [المرجع، افتراضياً origin/main]
set -euo pipefail
OUT=${1:?output dir}; REF=${2:-origin/main}
OLD='oaelhag.github.io/tajalliyat'; NEW='tajalliyat.com'
rm -rf "$OUT"; mkdir -p "$OUT"
git archive "$REF" | tar -x -C "$OUT"
# ملفات التطوير لا تُنشر
rm -rf "$OUT/source" "$OUT/docs" "$OUT/README.md" "$OUT/.gitignore" "$OUT/.nojekyll"
# تحويل الروابط المطلقة إلى الدومين الجديد (الملفات النصية فقط)
find "$OUT" -type f \( -name '*.html' -o -name '*.js' -o -name '*.json' -o -name '*.xml' -o -name '*.txt' -o -name '*.css' -o -name '*.ics' \) \
  -exec sed -i "s#https://$OLD/#https://$NEW/#g; s#https://$OLD#https://$NEW#g; s#$OLD#$NEW#g" {} +
# 404 حقيقية: صفحة بمحتوى وروابط و noindex بدل التحويل التلقائي (يعدّه جوجل soft-404)
cat > "$OUT/404.html" <<'EOT'
<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>الصفحة غير موجودة | تجليات الأسماء</title><style>body{font-family:system-ui,sans-serif;text-align:center;padding:4rem 1rem;line-height:2}a{color:#0b6b5c}</style></head><body><h1>الصفحة غير موجودة</h1><p>ربما تغيّر الرابط أو كُتب خطأ.</p><p><a href="/">الصفحة الرئيسية</a> · <a href="/guide.html">اسم يناسب حالك</a> · <a href="/books/">الكتب المجانية</a></p></body></html>
EOT
cp "$(dirname "$0")/htaccess" "$OUT/.htaccess"
echo "built $REF -> $OUT ($(git rev-parse --short "$REF"))"
