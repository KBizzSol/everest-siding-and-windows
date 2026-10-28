#!/usr/bin/env bash
# Mirrors the live WordPress site into ./mirror with identical URL paths.
# Runs on GitHub Actions (the build sandbox can't reach the live domain).
set -euo pipefail
ROOT="$(pwd)"
HOST="everestsidingandwindows.com"
BASE="https://$HOST"
rm -rf "$ROOT/mirror" && mkdir -p "$ROOT/mirror" && cd "$ROOT/mirror"
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36'

# 1) every URL the sitemaps know about (Yoast / Rank Math / core WP)
: > /tmp/urls.txt
for idx in sitemap_index.xml wp-sitemap.xml sitemap.xml; do
  curl -sL -A "$UA" "$BASE/$idx" -o /tmp/si.xml || continue
  grep -q '<loc>' /tmp/si.xml || continue
  for s in $(grep -oE '<loc>[^<]+\.xml[^<]*</loc>' /tmp/si.xml | sed 's/<\/\?loc>//g'); do curl -sL -A "$UA" "$s"; done \
    | grep -oE '<loc>[^<]+</loc>' | sed 's/<\/\?loc>//g' >> /tmp/urls.txt
  grep -oE '<loc>[^<]+</loc>' /tmp/si.xml | sed 's/<\/\?loc>//g' | grep -v '\.xml' >> /tmp/urls.txt || true
done
echo "$BASE/" >> /tmp/urls.txt
grep -v -iE '\.(jpg|jpeg|png|webp|gif|xml)$' /tmp/urls.txt | sed 's#^http://#https://#; s#//www\.#//#' | sort -u > /tmp/urls.sorted
mv /tmp/urls.sorted /tmp/urls.txt
echo "sitemap urls: $(wc -l < /tmp/urls.txt)"

# 2) pages + their CSS/JS/images
wget -q -e robots=off -U "$UA" -i /tmp/urls.txt -p -E -nH -H \
  --domains="$HOST,www.$HOST" --tries=3 --timeout=60 || true

# 3) recursive crawl to catch pages missing from the sitemaps (e.g. /es/ pages, anchors in menus)
wget -q -e robots=off -U "$UA" -r -l 6 -p -E -nH -H -nc \
  --domains="$HOST,www.$HOST" --reject-regex='(/wp-json/|/feed/|/wp-admin/|/wp-login|xmlrpc|\?replytocom=|/comments/|\?s=|/page/[0-9]+/\?|add-to-cart)' \
  --tries=3 --timeout=60 "$BASE/" || true

cp /tmp/urls.txt "$ROOT/mirror/_urls.txt"
echo "files: $(find "$ROOT/mirror" -type f | wc -l)  size: $(du -sh "$ROOT/mirror" | cut -f1)"
