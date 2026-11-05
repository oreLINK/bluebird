#!/usr/bin/env bash
# Rebuild web/public/apple-touch-icon.png (180 × 180) from
# web/scripts/apple-touch-icon.svg: headless Chrome renders it at 540 px,
# then sips (macOS) scales it down. Run it after changing the logo mark.
#   CHROME=/path/to/chrome web/scripts/make-apple-icon.sh
set -euo pipefail
cd "$(dirname "$0")/.."

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cp scripts/apple-touch-icon.svg "$tmp/icon.svg"
cat > "$tmp/icon.html" <<'HTML'
<!doctype html>
<html><body style="margin:0"><img src="icon.svg" width="540" height="540" style="display:block"></body></html>
HTML

"$CHROME" --headless --disable-gpu --hide-scrollbars --window-size=540,540 \
  --screenshot="$tmp/icon.png" "file://$tmp/icon.html" >/dev/null 2>&1
sips -z 180 180 "$tmp/icon.png" --out public/apple-touch-icon.png >/dev/null
echo "Wrote web/public/apple-touch-icon.png"
