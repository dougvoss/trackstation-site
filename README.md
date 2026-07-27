# trackstation-site

Vitrine institucional do TrackStation, servida em https://trackstation.com.br
por GitHub Pages.

Sem build: os arquivos deste repositório são os arquivos servidos.

## Ver localmente

    xdg-open index.html             # abre o arquivo direto no navegador
    python3 -m http.server 8000     # ou sirva em http://localhost:8000

As duas funcionam: a página não faz nenhuma requisição de rede e todos os
caminhos são relativos. O `mailto` do contato é montado por JavaScript e
funciona igual em `file://`.

## Verificação

    python3 -m pytest tests/ -v      # contrato da página (ver abaixo)
    ./verify.sh                      # o que está publicado de fato no DNS e no HTTP

### `python3 -m pytest tests/`

Lê `index.html`, `style.css` e `tools/og.html` do disco e afirma o que dá para
afirmar sem olhar a página:

- estrutura e metadados (`lang`, `<title>`, `description`, um único `<h1>`,
  `theme-color`, `alt` da imagem do palco);
- zero requisição externa — URLs absolutas **e** protocolo-relativas
  (`//cdn…`), na página e no cartão de compartilhamento;
- fontes auto-hospedadas (Space Grotesk e Space Mono), na página e no cartão,
  e todo asset citado existindo no disco;
- e-mail fora do HTML em texto plano, com fallback `<noscript>`;
- restrições globais: um único `<script>` (inline, só para o `mailto`) e
  ausência de `prefers-color-scheme`;
- semântica de cor: ciano é exclusivo de `.vs`;
- contraste WCAG, medido sobre as custom properties lidas de `style.css` —
  não sobre literais copiados para o teste.

Não abre navegador e não faz rede.

### `./verify.sh`

Consulta dois resolvers DoH independentes (Cloudflare e Google) e recruza antes
de alarmar, porque uma falha aparente numa única consulta não é definitiva.
Verifica:

- **e-mail:** MX do ImprovMX, SPF **com o qualificador** (`~all`) e DMARC
  `p=reject`;
- **página:** os quatro A do GitHub Pages e o CNAME do `www`
  (ambos sem depender da ordem — DNS rotaciona resposta multivalorada);
- **nameservers:** `a.sec.dns.br` / `b.sec.dns.br`, cuja troca levaria o
  DNSSEC junto;
- **DNSSEC:** DS publicado, distinguindo três desfechos — presente, ausente de
  verdade e "não foi possível determinar";
- **HTTP:** apex em 200, `http://` redirecionando 301 para `https://`, e o
  `www` redirecionando 301 e chegando ao apex quando seguido. Cada checagem
  tenta duas vezes e separa `000` (não conectou — problema de rede) de uma
  resposta genuinamente errada.

Não há checagem de certificado: um 200 em HTTPS implica cadeia TLS válida para
o `curl`, mas **validade, emissor e data de expiração não são verificados**.

Só precisa de `curl` e `python3`. Sai com 0 se tudo passar, 1 caso contrário, e
roda todas as checagens antes de somar — não aborta na primeira falha.

## Geração de assets

Rodados à mão, quando a fonte ou o cartão de compartilhamento mudam:

    ./tools/fetch_font.py            # rebaixa os subsets latin das duas fontes
    ./tools/make_og.sh               # regenera assets/og.png (1200x630)
    ./tools/shots.sh                 # captura em 360, 768 e 1440 px
    ./tools/shots.sh <url>           # o mesmo, contra o site publicado

- `fetch_font.py` extrai a URL do CSS do Google Fonts (os hashes do gstatic
  rotacionam) e grava `space-grotesk-latin.woff2` e `space-mono-latin.woff2`
  em `assets/fonts/`.
- `make_og.sh` e `shots.sh` precisam do **`google-chrome`** no PATH.
- `shots.sh` captura com movimento reduzido forçado: a animação de entrada do
  hero termina no estado padrão do CSS, então é o mesmo quadro final que o
  usuário vê — e sem isso a captura sai no meio da animação.
- `make_og.sh` também precisa do **Pillow** (`pip install Pillow`), que usa só
  para conferir que a captura saiu em 1200x630.

O `shots/` fica fora do git — é saída de verificação, não conteúdo.
