# trackstation-site

Vitrine institucional do TrackStation, servida em https://trackstation.com.br
por GitHub Pages.

Sem build: os arquivos deste repositório são os arquivos servidos.

## Verificação

    python3 -m pytest tests/ -v      # estrutura, ausência de rede externa, contraste
    ./tools/shots.sh                 # captura em 360, 768 e 1440 px
    ./tools/shots.sh <url>           # o mesmo, contra o site publicado
    ./verify.sh                      # DNS, TLS, DNSSEC e registros de e-mail

O `shots/` fica fora do git — é saída de verificação, não conteúdo.
