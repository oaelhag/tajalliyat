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
cp "$(dirname "$0")/htaccess" "$OUT/.htaccess"
echo "built $REF -> $OUT ($(git rev-parse --short "$REF"))"
