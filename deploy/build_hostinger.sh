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
python3 -I "$(dirname "$0")/patch_index.py" "$OUT" "$(dirname "$0")/contact-form-snippet.html"
# SEO: صفحات «قلبي الآن» + روابط قابلة للزحف + أوسمة ناقصة، ثم رسم صور المعاينة والأيقونات
python3 -I "$(dirname "$0")/gen_seo.py" "$OUT" gen
if node -e "require('playwright')" 2>/dev/null; then
  node "$(dirname "$0")/gen_images.js" "$OUT"
else
  echo "WARNING: playwright غير متاح: لن تُرسم صور المعاينة الجديدة (يُستعمل og/default.jpg)" >&2
fi
rm -f "$OUT/_img_jobs.json"
python3 -I "$(dirname "$0")/gen_seo.py" "$OUT" check
# ملفات pdf/ لكل اسم: إعادة توليدها من print/*.html بعنوان الموقع الجديد
if node -e "require('playwright')" 2>/dev/null; then node "$(dirname "$0")/gen_pdfs.js" "$OUT"; else echo "ERROR: playwright مطلوب لتوليد PDF" >&2; exit 1; fi
# إزالة اسم المطوّر من كل الملفات (نصوص وPDF) مع التحقق
python3 "$(dirname "$0")/scrub_developer.py" "$OUT"
# 404 حقيقية: صفحة بمحتوى وروابط و noindex بدل التحويل التلقائي (يعدّه جوجل soft-404)
cat > "$OUT/404.html" <<'EOT'
<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>الصفحة غير موجودة | تجليات الأسماء</title><style>body{font-family:system-ui,sans-serif;text-align:center;padding:4rem 1rem;line-height:2}a{color:#0b6b5c}</style></head><body><h1>الصفحة غير موجودة</h1><p>ربما تغيّر الرابط أو كُتب خطأ.</p><p><a href="/">الصفحة الرئيسية</a> · <a href="/guide.html">اسم يناسب حالك</a> · <a href="/books/">الكتب المجانية</a></p></body></html>
EOT
cp "$(dirname "$0")/htaccess" "$OUT/.htaccess"
echo "built $REF -> $OUT ($(git rev-parse --short "$REF"))"
# PWA (اختياري): PWA=1  [PWA_BASE=/pwa-preview/]  [PWA_PREVIEW=1 لمنع الفهرسة]
if [ "${PWA:-0}" = 1 ]; then
  python3 "$(dirname "$0")/pwa.py" "$OUT" "${PWA_BASE:-/}" ${PWA_PREVIEW:+preview}
fi
