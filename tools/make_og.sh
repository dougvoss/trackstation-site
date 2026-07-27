#!/usr/bin/env bash
# Captura tools/og.html com o Chrome headless e gera assets/og.png (1200x630).
#
# Chrome headless não precisa de servidor X — a mensagem "Authorization
# required" no stderr é ruído e não impede a captura.
set -euo pipefail
cd "$(dirname "$0")/.."

# Sem esta guarda, um google-chrome ausente cai no "set -e" com o stderr da
# captura mandado para /dev/null: o script morre em silêncio absoluto (código
# 127, saída vazia, nem "command not found").
if ! command -v google-chrome >/dev/null 2>&1; then
  echo "erro: google-chrome não encontrado no PATH — necessário para a captura headless" >&2
  exit 1
fi

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
