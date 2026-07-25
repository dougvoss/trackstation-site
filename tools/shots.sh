#!/usr/bin/env bash
# Captura a página em três larguras para inspeção visual.
#
# Sem argumento, captura o arquivo local (shots/360.png etc.).
# Com um argumento, captura a URL informada e prefixa a saída com "prod-",
# que é como a Task 13 verifica o site publicado.
#
# Chrome headless não precisa de servidor X — a mensagem "Authorization
# required" no stderr é ruído e não impede a captura.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p shots

if [ $# -gt 0 ]; then
  alvo="$1"
  prefixo="prod-"
else
  alvo="file://$PWD/index.html"
  prefixo=""
fi

for largura in 360 768 1440; do
  saida="shots/${prefixo}${largura}.png"
  google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --window-size="${largura},2400" \
    --screenshot="$saida" \
    "$alvo" 2>/dev/null
  printf '%s\n' "$saida"
done
