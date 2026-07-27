#!/usr/bin/env bash
# Verifica o que está publicado de fato, consultando resolver externo —
# não a tela do painel do Registro.br, que mostra intenção, não realidade.
set -uo pipefail
DOM="trackstation.com.br"
falhas=0

consulta() {  # consulta <nome> <tipo>
  curl -s -m 15 -H "accept: application/dns-json" \
    "https://cloudflare-dns.com/dns-query?name=$1&type=$2"
}

checa() {  # checa <rótulo> <nome> <tipo> <padrão-esperado>
  local dados
  dados=$(consulta "$2" "$3" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(' | '.join(a.get('data','') for a in (d.get('Answer') or [])))
")
  if printf '%s' "$dados" | grep -qi -- "$4"; then
    printf '  OK    %-18s %s\n' "$1" "$dados"
  else
    printf '  FALHA %-18s esperado ~%s, veio: %s\n' "$1" "$4" "${dados:-<vazio>}"
    falhas=$((falhas + 1))
  fi
}

echo "== e-mail =="
checa "MX"     "$DOM"          MX   "improvmx"
checa "SPF"    "$DOM"          TXT  "v=spf1"
checa "DMARC"  "_dmarc.$DOM"   TXT  "v=DMARC1"

echo "== página =="
checa "A apex" "$DOM"          A    "185.199.1"
checa "CNAME"  "www.$DOM"      CNAME "github.io"

echo "== DNSSEC =="
ds=$(consulta "$DOM" DS | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('sim' if (d.get('Answer') or []) else 'nao', 'AD' if d.get('AD') else 'sem-AD')
")
if printf '%s' "$ds" | grep -q "^sim"; then
  printf '  OK    %-18s %s\n' "DS publicado" "$ds"
else
  printf '  FALHA %-18s DS ausente — DNSSEC caiu\n' "DS publicado"
  falhas=$((falhas + 1))
fi

echo "== HTTPS =="
codigo=$(curl -s -o /dev/null -m 20 -w '%{http_code}' "https://$DOM/")
if [ "$codigo" = "200" ]; then
  printf '  OK    %-18s HTTP %s\n' "apex responde" "$codigo"
else
  printf '  FALHA %-18s HTTP %s\n' "apex responde" "$codigo"
  falhas=$((falhas + 1))
fi

echo
if [ "$falhas" -eq 0 ]; then
  echo "tudo verde"
else
  echo "$falhas checagem(ns) falhando"
  exit 1
fi
