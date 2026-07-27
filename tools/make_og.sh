#!/usr/bin/env bash
# Captura tools/og.html com o Chrome headless e gera assets/og.png (1200x630).
#
# Chrome headless não precisa de servidor X — a mensagem "Authorization
# required" no stderr é ruído e não impede a captura.
set -euo pipefail
cd "$(dirname "$0")/.."

saida="assets/og.png"

google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=1200,630 \
  --screenshot="$saida" \
  "file://$PWD/tools/og.html" 2>/dev/null

dimensoes=$(python3 -c "from PIL import Image; im = Image.open('$saida'); print(f'{im.width}x{im.height}')")
printf '%s %s\n' "$saida" "$dimensoes"
