"""Wrap dist/index.html (authored for the Claude artifact host, which adds the <head> skeleton)
into a complete standalone page for GitHub Pages."""
import sys, pathlib
src = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
head = '''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>تجليات الأسماء | تأمّل أسماء الله الحسنى</title>
<meta name="description" content="تجلٍّ يومي وأسئلة تأمّل ورحلة ١٤٠ يوماً مع أسماء الله الحسنى، لست فئات: طفل، طفلة، شاب، شابة، أب، أم.">
<link rel="canonical" href="https://oaelhag.github.io/tajalliyat/">
<meta property="og:type" content="website"><meta property="og:locale" content="ar_AR">
<meta property="og:site_name" content="تجليات الأسماء">
<meta property="og:title" content="تجليات الأسماء">
<meta property="og:description" content="تأمّل أسماء الله الحسنى: تجلٍّ يومي، أسئلة، ورحلة ١٤٠ يوماً.">
<meta property="og:url" content="https://oaelhag.github.io/tajalliyat/">
<meta property="og:image" content="https://oaelhag.github.io/tajalliyat/og/default.jpg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://oaelhag.github.io/tajalliyat/og/default.jpg">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
html{-webkit-text-size-adjust:100%;text-size-adjust:100%}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
'''
pathlib.Path(sys.argv[2]).write_text(head + src + '\n</html>\n', encoding='utf-8')
