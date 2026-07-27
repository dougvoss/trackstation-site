#!/usr/bin/env bash
# Verifica o que está publicado de fato, consultando resolvers externos com cross-check —
# não a tela do painel do Registro.br, que mostra intenção, não realidade.
set -uo pipefail
DOM="trackstation.com.br"
falhas=0

consulta() {  # consulta <nome> <tipo> [resolver_url]
  local resolver="${3:-https://cloudflare-dns.com/dns-query}"
  curl -s -m 15 -H "accept: application/dns-json" \
    "${resolver}?name=$1&type=$2"
}

checa() {  # checa <rótulo> <nome> <tipo> <padrão-esperado>
  local dados resposta

  # Tentar com Cloudflare primeiro
  resposta=$(consulta "$2" "$3" "https://cloudflare-dns.com/dns-query")
  dados=$(echo "$resposta" | python3 -c "
import sys, json
try:
  d = json.load(sys.stdin)
  result = ' | '.join(a.get('data','') for a in (d.get('Answer') or []))
  print(result)
except Exception:
  print('__ERRO__')
" 2>/dev/null || echo "__ERRO__")

  # Se dados vazio ou erro, tentar com Google
  if [ -z "$dados" ] || [ "$dados" = "__ERRO__" ]; then
    resposta=$(consulta "$2" "$3" "https://dns.google/resolve")
    dados=$(echo "$resposta" | python3 -c "
import sys, json
try:
  d = json.load(sys.stdin)
  result = ' | '.join(a.get('data','') for a in (d.get('Answer') or []))
  print(result)
except Exception:
  print('__ERRO__')
" 2>/dev/null || echo "__ERRO__")
  fi

  # Se ainda erro, reportar
  if [ "$dados" = "__ERRO__" ]; then
    printf '  ERRO  %-18s consulta DNS falhou\n' "$1"
    falhas=$((falhas + 1))
    return
  fi

  # Fazer o matching
  if [ -z "$dados" ]; then
    printf '  FALHA %-18s esperado ~%s, veio: %s\n' "$1" "$4" "<vazio>"
    falhas=$((falhas + 1))
  elif printf '%s' "$dados" | grep -qi -- "$4"; then
    printf '  OK    %-18s %s\n' "$1" "$dados"
  else
    printf '  FALHA %-18s esperado ~%s, veio: %s\n' "$1" "$4" "$dados"
    falhas=$((falhas + 1))
  fi
}

echo "== e-mail =="
checa "MX"     "$DOM"          MX   "mx1\.improvmx\.com.*mx2\.improvmx\.com"
checa "SPF"    "$DOM"          TXT  "include:spf\.improvmx\.com"
checa "DMARC"  "_dmarc.$DOM"   TXT  "p=reject"

echo "== página =="
checa "A apex" "$DOM"          A    "185\.199\.108\.153.*185\.199\.109\.153.*185\.199\.110\.153.*185\.199\.111\.153"
checa "CNAME"  "www.$DOM"      CNAME "dougvoss\.github\.io"

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
