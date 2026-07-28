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

consulta_http() {  # consulta_http <url> <seguir:sim|nao> -> "<código> <destino>"
  # Com seguir=nao, o destino é o Location da resposta (vazio se não houver).
  # Com seguir=sim, o destino é a URL final depois de seguir os redirects.
  if [ "$2" = "sim" ]; then
    curl -sL -o /dev/null -m 20 -w '%{http_code} %{url_effective}' "$1"
  else
    curl -s -o /dev/null -m 20 -w '%{http_code} %{redirect_url}' "$1"
  fi
}

avalia_http() {  # avalia_http <código> <destino> <cód-esperado> <destino-esperado|-> -> OK|FALHA|ERRO
  local codigo="$1" destino="$2" cod_esp="$3" dest_esp="$4"

  # 000 é "o curl nunca conectou", não "o servidor respondeu errado" — são
  # diagnósticos diferentes e não podem sair com a mesma mensagem, do mesmo
  # jeito que o caminho de DNS separa ERRO de FALHA.
  if [ "$codigo" = "000" ]; then
    echo "ERRO"
  elif [ "$codigo" != "$cod_esp" ]; then
    echo "FALHA"
  elif [ "$dest_esp" != "-" ] && [ "$destino" != "$dest_esp" ]; then
    echo "FALHA"
  else
    echo "OK"
  fi
}

checa_http() {  # checa_http <rótulo> <url> <cód-esperado> <destino-esperado|-> <seguir:sim|nao>
  local rotulo="$1" url="$2" cod_esp="$3" dest_esp="$4" seguir="$5"
  local resposta codigo destino veredito

  resposta=$(consulta_http "$url" "$seguir")
  codigo=${resposta%% *}
  destino=${resposta#* }
  veredito=$(avalia_http "$codigo" "$destino" "$cod_esp" "$dest_esp")

  if [ "$veredito" != "OK" ]; then
    # Mesmo princípio das checagens de DNS: uma falha aparente numa única
    # tentativa nunca é definitiva por si só — pode ser oscilação de rede ou
    # do CDN. Tenta mais uma vez antes de alarmar.
    resposta=$(consulta_http "$url" "$seguir")
    codigo=${resposta%% *}
    destino=${resposta#* }
    veredito=$(avalia_http "$codigo" "$destino" "$cod_esp" "$dest_esp")
  fi

  case "$veredito" in
    OK)
      printf '  OK    %-18s HTTP %s%s\n' "$rotulo" "$codigo" "${destino:+ -> $destino}"
      ;;
    ERRO)
      printf '  ERRO  %-18s não conectou (curl 000) — rede, não o site\n' "$rotulo"
      falhas=$((falhas + 1))
      ;;
    FALHA)
      local esperado="HTTP $cod_esp"
      [ "$dest_esp" != "-" ] && esperado="$esperado -> $dest_esp"
      printf '  FALHA %-18s esperado %s, veio: HTTP %s%s\n' \
        "$rotulo" "$esperado" "$codigo" "${destino:+ -> $destino}"
      falhas=$((falhas + 1))
      ;;
  esac
}

checa_404_proprio() {  # checa_404_proprio <url>
  # O status 404 sozinho não distingue nada: o GitHub Pages devolve 404 tanto
  # servindo o nosso 404.html quanto servindo a página branca dele. O que separa
  # os dois é o corpo, então este check olha o corpo — e exige as duas coisas
  # juntas, porque um 200 com o nosso HTML seria igualmente errado (caminho
  # inexistente respondendo sucesso confunde buscador).
  local url="$1" codigo corpo tentativa
  for tentativa in 1 2; do
    corpo=$(curl -s -m 20 -w '\n%{http_code}' "$url" 2>/dev/null)
    codigo=${corpo##*$'\n'}
    if [ "$codigo" = "404" ] && printf '%s' "$corpo" | grep -q 'não está no setlist'; then
      printf '  OK    %-18s HTTP 404 com a nossa página\n' "404 personalizado"
      return
    fi
    [ "$tentativa" = 1 ] && continue
  done
  if [ "$codigo" = "000" ]; then
    printf '  ERRO  %-18s não conectou (curl 000) — rede, não o site\n' "404 personalizado"
  elif [ "$codigo" != "404" ]; then
    printf '  FALHA %-18s esperado HTTP 404, veio: HTTP %s\n' "404 personalizado" "$codigo"
  else
    printf '  FALHA %-18s HTTP 404, mas o corpo não é o nosso 404.html\n' "404 personalizado"
  fi
  falhas=$((falhas + 1))
}

echo "== e-mail =="
checa "MX"     "$DOM"          MX   "SET:mx1.improvmx.com|mx2.improvmx.com"
# O qualificador faz parte do contrato: sem ele na expressão, "~all" e "-all"
# ficariam indistinguíveis e uma troca silenciosa passaria verde. "~all" é o
# valor correto e fica — quem rejeita é o DMARC (p=reject com adkim=s/aspf=s),
# e é também o que o painel do ImprovMX recomenda e valida. Simétrico ao
# DMARC da linha abaixo, que já exigia "p=reject".
checa "SPF"    "$DOM"          TXT  "v=spf1 include:spf\.improvmx\.com ~all"
checa "DMARC"  "_dmarc.$DOM"   TXT  "p=reject"

echo "== página =="
checa "A apex" "$DOM"          A    "SET:185.199.108.153|185.199.109.153|185.199.110.153|185.199.111.153"
checa "CNAME"  "www.$DOM"      CNAME "SET:dougvoss.github.io"

echo "== nameservers =="
# Trocar nameserver é a operação mais perigosa neste domínio: levaria o DNSSEC
# junto. SET: porque a ordem das respostas multivaloradas rotaciona — os dois
# resolvers devolvem estes dois nomes em ordens diferentes.
checa "NS"     "$DOM"          NS   "SET:a.sec.dns.br|b.sec.dns.br"

echo "== DNSSEC =="
checa_dnssec "DS publicado" "$DOM"

echo "== HTTPS =="
checa_http "apex responde"     "https://$DOM/"      200 "-"               nao
checa_http "HTTP redireciona"  "http://$DOM/"       301 "https://$DOM/"   nao
checa_http "www redireciona"   "https://www.$DOM/"  301 "https://$DOM/"   nao
checa_http "www chega ao apex" "https://www.$DOM/"  200 "https://$DOM/"   sim

# Os três arquivos que existem no repositório mas ninguém abre no navegador, e
# por isso quebram em silêncio: um arquivo que não entrou no commit só aparece
# aqui. O 404 é o único caso em que a resposta certa é um código de erro, e o
# único que precisa olhar o corpo — ver checa_404_proprio.
echo "== descoberta =="
checa_http "robots.txt"   "https://$DOM/robots.txt"   200 "-" nao
checa_http "sitemap.xml"  "https://$DOM/sitemap.xml"  200 "-" nao
checa_404_proprio "https://$DOM/nao-existe"

echo
if [ "$falhas" -eq 0 ]; then
  echo "tudo verde"
else
  echo "$falhas checagem(ns) falhando"
  exit 1
fi
