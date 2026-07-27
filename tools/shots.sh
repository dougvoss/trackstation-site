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

# Sem esta guarda, um google-chrome ausente cai no "set -e" com o stderr da
# captura mandado para /dev/null: o script morre em silêncio absoluto (código
# 127, saída vazia, nem "command not found").
if ! command -v google-chrome >/dev/null 2>&1; then
  echo "erro: google-chrome não encontrado no PATH — necessário para a captura headless" >&2
  exit 1
fi

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
  # --force-prefers-reduced-motion desliga a animação de entrada, senão a
  # captura sai no meio dela: metade do hero em opacity 0. O estado final da
  # animação é o estado padrão do CSS, então é o mesmo quadro que o usuário vê
  # ao fim — e de passagem verifica o caminho de movimento reduzido.
  google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --window-size="${largura},2400" \
    --force-prefers-reduced-motion \
    --screenshot="$saida" \
    "$alvo" 2>/dev/null
  printf '%s\n' "$saida"
done
