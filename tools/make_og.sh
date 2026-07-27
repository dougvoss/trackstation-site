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

esperado="1200x630"
dimensoes=$(python3 -c "from PIL import Image; im = Image.open('$saida'); print(f'{im.width}x{im.height}')")

if [ "$dimensoes" != "$esperado" ]; then
  echo "erro: $saida saiu com $dimensoes, esperado $esperado — não faça commit deste arquivo; verifique --window-size e a versão do Chrome" >&2
  exit 1
fi

printf '%s %s\n' "$saida" "$dimensoes"
