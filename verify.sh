#!/usr/bin/env bash
# Verifica o que está publicado de fato, consultando resolvers externos com cross-check —
# não a tela do painel do Registro.br, que mostra intenção, não realidade.
set -uo pipefail
DOM="trackstation.com.br"
falhas=0

CF="https://cloudflare-dns.com/dns-query"
GOOGLE="https://dns.google/resolve"

consulta() {  # consulta <nome> <tipo> <resolver_url>
  curl -s -m 15 -H "accept: application/dns-json" \
    "${3}?name=$1&type=$2"
}

obter_dados() {  # obter_dados <nome> <tipo> <resolver_url> -> "val1 | val2 | ..." ou __ERRO__
  local resposta
  resposta=$(consulta "$1" "$2" "$3")
  # captura a resposta antes de repassar ao Python: se o curl falhar (host
  # inalcançável), seu código de saída não pode entrar no pipe abaixo — sob
  # "pipefail" isso disparava o "|| echo" mesmo quando o Python já tinha
  # tratado o erro sozinho, duplicando a saída "__ERRO__"
  printf '%s' "$resposta" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(' | '.join(a.get('data','') for a in (d.get('Answer') or [])))
except Exception:
    print('__ERRO__')
" 2>/dev/null || echo "__ERRO__"
}

avalia_padrao() {  # avalia_padrao <dados> <padrão-esperado> -> OK|FALHA|ERRO
  local dados="$1" pattern="$2"

  if [ "$dados" = "__ERRO__" ]; then
    echo "ERRO"
    return
  fi

  if [[ "$pattern" == SET:* ]]; then
    local required_items="${pattern#SET:}" resultado
    # required_items vai como argv, não splicado no literal Python — evita
    # qualquer risco de injeção mesmo que deixe de ser um literal estático.
    resultado=$(printf '%s' "$dados" | python3 -c "
import sys
try:
    data = sys.stdin.read()
    entradas = [e.strip() for e in data.split('|') if e.strip()]
    exigidos = [r.strip() for r in sys.argv[1].split('|') if r.strip()]

    def normaliza(token):
        return token.rstrip('.')

    def bate(entrada, exigido):
        alvo = normaliza(exigido)
        if normaliza(entrada) == alvo:
            return True
        # registros com prioridade (ex.: MX '10 mx1.improvmx.com.') —
        # compara só o último campo, não a entrada inteira
        campos = entrada.split()
        return bool(campos) and normaliza(campos[-1]) == alvo

    ok = all(any(bate(e, r) for e in entradas) for r in exigidos)
    print('OK' if ok else 'FALHA')
except Exception:
    print('FALHA')
" "$required_items" 2>/dev/null || echo 'FALHA')
    [ "$resultado" = "OK" ] && echo "OK" || echo "FALHA"
  else
    if [ -z "$dados" ]; then
      echo "FALHA"
    elif printf '%s' "$dados" | grep -qi -- "$pattern"; then
      echo "OK"
    else
      echo "FALHA"
    fi
  fi
}

checa() {  # checa <rótulo> <nome> <tipo> <padrão-esperado>
  local rotulo="$1" nome="$2" tipo="$3" pattern="$4"
  local dados dados2 veredito veredito2

  dados=$(obter_dados "$nome" "$tipo" "$CF")
  veredito=$(avalia_padrao "$dados" "$pattern")

  if [ "$veredito" != "OK" ]; then
    # Uma falha aparente no primário nunca é definitiva por si só — pode ser
    # cache negativo desatualizado ou resposta parcial de round-robin ainda
    # em rotação. Recruza com o segundo resolver antes de alarmar; só falha
    # de verdade se os dois concordarem.
    dados2=$(obter_dados "$nome" "$tipo" "$GOOGLE")
    veredito2=$(avalia_padrao "$dados2" "$pattern")

    if [ "$veredito2" = "OK" ]; then
      dados="$dados2"
      veredito="OK"
    elif [ "$veredito" = "ERRO" ] && [ "$veredito2" = "ERRO" ]; then
      veredito="ERRO"
    elif [ "$veredito" = "ERRO" ] || [ "$veredito2" = "ERRO" ]; then
      # só um dos dois resolvers respondeu de verdade — não dá pra confirmar
      # que os dois concordam na falha, então não alarma como FALHA
      veredito="ERRO"
      [ "$dados2" != "__ERRO__" ] && dados="$dados2"
    else
      veredito="FALHA"
      dados="$dados2"
    fi
  fi

  case "$veredito" in
    OK)
      printf '  OK    %-18s %s\n' "$rotulo" "$dados"
      ;;
    ERRO)
      printf '  ERRO  %-18s consulta DNS falhou\n' "$rotulo"
      falhas=$((falhas + 1))
      ;;
    FALHA)
      local esperado="$pattern"
      [[ "$pattern" == SET:* ]] && esperado="${pattern#SET:}"
      printf '  FALHA %-18s esperado ~%s, veio: %s\n' "$rotulo" "$esperado" "${dados:-<vazio>}"
      falhas=$((falhas + 1))
      ;;
  esac
}

consulta_dnssec() {  # consulta_dnssec <nome> <resolver_url> -> "sim|nao AD|sem-AD" ou __ERRO__
  local resposta
  resposta=$(consulta "$1" DS "$2")
  printf '%s' "$resposta" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    tem_ds = 'sim' if (d.get('Answer') or []) else 'nao'
    tem_ad = 'AD' if d.get('AD') else 'sem-AD'
    print(tem_ds + ' ' + tem_ad)
except Exception:
    print('__ERRO__')
" 2>/dev/null || echo "__ERRO__"
}

checa_dnssec() {  # checa_dnssec <rótulo> <nome>
  local rotulo="$1" nome="$2"
  local dados dados2

  dados=$(consulta_dnssec "$nome" "$CF")

  if [[ "$dados" == sim* ]]; then
    printf '  OK    %-18s %s\n' "$rotulo" "$dados"
    return
  fi

  # Primário não confirmou DS presente (ausente ou erro de consulta) — antes
  # de alarmar "DNSSEC caiu", recruza com o segundo resolver. Um "ausente"
  # isolado é exatamente a assinatura de um cache negativo desatualizado (já
  # aconteceu neste projeto com o _dmarc); um erro isolado é problema de
  # rede, não de DNSSEC. Só reporta falha real se os dois concordarem que o
  # DS está ausente.
  dados2=$(consulta_dnssec "$nome" "$GOOGLE")

  if [[ "$dados2" == sim* ]]; then
    printf '  OK    %-18s %s\n' "$rotulo" "$dados2"
  elif [[ "$dados" == nao* ]] && [[ "$dados2" == nao* ]]; then
    printf '  FALHA %-18s DS ausente — DNSSEC caiu\n' "$rotulo"
    falhas=$((falhas + 1))
  else
    # ao menos um dos dois não conseguiu responder — não dá pra confirmar
    # que os dois concordam que o DS está ausente
    printf '  ERRO  %-18s consulta DNS falhou\n' "$rotulo"
    falhas=$((falhas + 1))
  fi
}

echo "== e-mail =="
checa "MX"     "$DOM"          MX   "SET:mx1.improvmx.com|mx2.improvmx.com"
checa "SPF"    "$DOM"          TXT  "include:spf\.improvmx\.com"
checa "DMARC"  "_dmarc.$DOM"   TXT  "p=reject"

echo "== página =="
checa "A apex" "$DOM"          A    "SET:185.199.108.153|185.199.109.153|185.199.110.153|185.199.111.153"
checa "CNAME"  "www.$DOM"      CNAME "SET:dougvoss.github.io"

echo "== DNSSEC =="
checa_dnssec "DS publicado" "$DOM"

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
