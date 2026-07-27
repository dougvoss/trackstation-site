# Site em quatro idiomas — design

Data: 2026-07-27
Branch: `feat/i18n-4-idiomas`

## Objetivo

Publicar a vitrine do TrackStation em pt-BR (já existe), en-US, es (neutro/LatAm)
e fr-FR, servida por GitHub Pages, sem introduzir passo de build.

## Estrutura de URLs

```
index.html        → pt-BR   https://trackstation.com.br/
en/index.html     → en-US   https://trackstation.com.br/en/
es/index.html     → es      https://trackstation.com.br/es/
fr/index.html     → fr-FR   https://trackstation.com.br/fr/
```

A raiz fica em pt-BR: o produto é brasileiro e é o idioma do público primário.
`x-default` aponta para a raiz.

`style.css` e `assets/` continuam únicos, na raiz. As páginas de idioma os
referenciam com `../` (`../style.css`, `../assets/palco.png`). Nada é duplicado
além do HTML.

Quatro arquivos completos servidos direto, em vez de gerador com template. O
README promete "sem build: os arquivos deste repositório são os arquivos
servidos", e essa promessa é o que torna o repositório auditável — o que se lê
é o que o navegador recebe. O custo dessa escolha é drift entre as versões, e
ele é contido pela suíte de testes (seção "Testes"), não por disciplina.

**Fora de escopo:** redirecionamento automático por `Accept-Language` (GitHub
Pages não faz, e JS está travado por teste ao único `<script>` do mailto);
`sitemap.xml` (as tags `hreflang` recíprocas já cobrem a descoberta).

## Política de tradução

Transcriação, não tradução literal: cada idioma usa o jargão que o músico
daquele mercado usa de fato ao vivo.

| Conceito | pt-BR | en-US | es | fr-FR |
|---|---|---|---|---|
| Canal de música | VS | tracks | pistas | la bande |
| Canal de tempo | click | click | click | le clic |
| Destino do primeiro | PA | the PA | el PA | la façade |
| Destino do segundo | fone | your ears / in-ears | in-ears | oreillettes |

Três decisões que sustentam a tabela:

1. **Em inglês o termo é `tracks`, não `sampler`.** "Sampler" nomeia o aparelho
   (MPC, Kontakt), não o conteúdo do canal. O par canônico do mercado é "click
   and tracks", e quem toca assim diz "playing to tracks".
2. **Em francês, `playback` é proibido no texto.** A palavra carrega a
   conotação de dublar, cantar de mentira ("chanter en playback") — o oposto do
   que o produto serve. Usar `la bande` e, quando couber, `les séquences`.
3. **`VS` sobrevive onde o texto descreve a tela.** A legenda do print e o `alt`
   citam o fader `VS` nas quatro línguas, porque é o rótulo que a pessoa vai
   ver na interface. Na prosa, vale o termo local.

A semântica de cor não se traduz: ciano é o canal de música e âmbar é o click
nas quatro versões. É ela que faz o site e o app serem lidos como o mesmo
produto, e ela já é travada por teste (`test_ciano_e_exclusivo_do_vs`).

Registro de voz: leve, direto, concreto — o tom que o pt-BR tem hoje. Francês
em `vous` (neutro respeitoso); espanhol neutro/LatAm, sem voseo e sem
`vosotros`, o que o torna aceitável na Espanha e natural de Argentina ao México.

## Strings por idioma

### pt-BR (estado atual, referência)

Sem alteração de conteúdo. Ganha só o seletor de idioma, as tags `hreflang` e
`og:locale:alternate`.

### en-US

| Slot | Texto |
|---|---|
| `<title>` | TrackStation — live playback, under your foot |
| `description` | Playback for people who play live: tracks in one channel, click in the other. Pick a song, play, duck, mute — it's all on the footswitch, so your hands stay on your instrument. |
| `og:description` | Tracks in one channel, click in the other. The whole show under your foot. |
| estado (barra) | In development |
| eyebrow | Stage tool |
| h1 | Tracks in one channel. / Click in the other. / The whole show under your foot. |
| sub | Not a music player — it's what runs your tracks while you play. Pick the next song, hit the switch, and your hands stay where they belong. |
| destino 1 | Goes to the PA |
| destino 2 | Stays in your ears |
| nota | Nothing to set up: the app knows which side is which |
| h2 palco | Stage mode |
| legenda | Setlist in blocks · both channels on one waveform · master, VS and click faders |
| `alt` | TrackStation's Stage Mode screen: multi-column setlist, both channels on a single waveform with the click in amber and the tracks in cyan, and MASTER, VS and CLICK faders. |
| bloco 1 | Channels / Two channels, two faders / Tracks in one channel, click in the other, each with its own fader. And when you need to talk to the room, duck pulls the music down — the click stays in your ears. |
| bloco 2 | Footswitch / All on your foot, none in your hands / Pick a song, play, pause, duck, mute, fade — all from the footswitch. And if you hit it wrong mid-song, the command is ignored: nobody kills the music in the chorus. |
| bloco 3 | Files / Your setlist won't walk out on you / On import, the app keeps its own copy of the song and recognizes the file by its contents. If someone reshuffled the music folder last night, the show doesn't notice. |
| estágio | Stage / In active development. No public release yet. |
| contato | Contact / Playing to tracks and a click? Write to me — I'd like to hear how your stage is set up. |
| botão | Send an email |
| `<noscript>` | write to contact at trackstation.com.br |

### es (neutro/LatAm)

| Slot | Texto |
|---|---|
| `<title>` | TrackStation — playback en vivo, a tus pies |
| `description` | Playback para quien toca en vivo: pistas en un canal, click en el otro. Elegir, tocar, duck y mute sale todo del pedal — las manos siguen en el instrumento. |
| `og:description` | Pistas en un canal, click en el otro. Todo el show a tus pies. |
| estado (barra) | En desarrollo |
| eyebrow | Herramienta de escenario |
| h1 | Pistas en un canal. / Click en el otro. / Todo el show a tus pies. |
| sub | No es un reproductor de música: es quien se encarga de las pistas mientras tocas. Basta elegir la próxima y pisar; las manos quedan donde tienen que estar. |
| destino 1 | Va al PA |
| destino 2 | Queda en los in-ears |
| nota | No hay nada que configurar: la app sabe cuál lado es cuál |
| h2 palco | Modo escenario |
| legenda | Setlist en bloques · los dos canales en la misma waveform · faders de master, VS y click |
| `alt` | Pantalla del Modo Escenario de TrackStation: setlist en varias columnas, los dos canales en la misma waveform con el click en ámbar y las pistas en cian, y faders de MASTER, VS y CLICK. |
| bloco 1 | Canales / Dos canales, dos faders / Pistas en un canal, click en el otro, cada uno con su fader. Y cuando necesitas hablarle al público, el duck baja la música — el click sigue en tus oídos. |
| bloco 2 | Pedal / Todo en el pie, nada en la mano / Elegir la canción, tocar, pausar, duck, mute, fade — todo con el pedal. Y si pisas mal en el apuro, el comando se ignora: nadie corta la música en el estribillo. |
| bloco 3 | Archivos / Tu setlist no te deja solo / Al importar, la app guarda su propia copia de la canción y reconoce el archivo por su contenido. Si alguien movió la carpeta de música anoche, el show no se entera. |
| estágio | Etapa / En desarrollo activo. Sin versión pública por ahora. |
| contato | Contacto / ¿Tocas con pistas y click? Escríbeme — quiero saber cómo es tu escenario. |
| botão | Enviar un correo |
| `<noscript>` | escribe a contact arroba trackstation.com.br |

### fr-FR

| Slot | Texto |
|---|---|
| `<title>` | TrackStation — la bande en live, sous votre pied |
| `description` | Pour ceux qui jouent en live : la bande dans une voie, le clic dans l'autre. Choisir, lancer, duck et mute passent tous par la pédale — les mains restent sur l'instrument. |
| `og:description` | La bande dans une voie, le clic dans l'autre. Tout le concert sous votre pied. |
| estado (barra) | En développement |
| eyebrow | Outil de scène |
| h1 | La bande dans une voie. / Le clic dans l'autre. / Tout le concert sous votre pied. |
| sub | Ce n'est pas un lecteur de musique — c'est ce qui gère la bande pendant que vous jouez. Vous choisissez le titre suivant, vous appuyez du pied, et les mains restent là où elles doivent être. |
| destino 1 | Part vers la façade |
| destino 2 | Reste dans vos oreillettes |
| nota | Rien à configurer : l'app reconnaît toute seule quel côté est lequel |
| h2 palco | Mode scène |
| legenda | Setlist en blocs · les deux voies sur la même waveform · faders master, VS et clic |
| `alt` | Écran du Mode Scène de TrackStation : setlist sur plusieurs colonnes, les deux voies sur la même waveform avec le clic en ambre et la bande en cyan, et les faders MASTER, VS et CLICK. |
| bloco 1 | Voies / Deux voies, deux faders / La bande dans une voie, le clic dans l'autre, chacun avec son fader. Et quand vous devez parler au public, le duck baisse la musique — le clic reste dans vos oreilles. |
| bloco 2 | Pédale / Tout au pied, rien à la main / Choisir le titre, lancer, mettre en pause, duck, mute, fade — tout à la pédale. Et si vous appuyez à côté dans le feu de l'action, la commande est ignorée : personne ne coupe la musique en plein refrain. |
| bloco 3 | Fichiers / Votre setlist ne vous laisse pas tomber / À l'import, l'app garde sa propre copie du morceau et reconnaît le fichier par son contenu. Si quelqu'un a déplacé le dossier de musique la veille, le concert ne s'en aperçoit pas. |
| estágio | Étape / En développement actif. Pas encore de version publique. |
| contato | Contact / Vous jouez avec bande et clic ? Écrivez-moi — j'aimerais savoir comment votre scène est montée. |
| botão | Envoyer un e-mail |
| `<noscript>` | écrivez à contact arobase trackstation.com.br |

O `<noscript>` usa a ponte de cada idioma (`arroba`, `at`, `arobase`) para não
servir o endereço em texto plano ao scraper — mesma razão do pt-BR, e o teste
que exige a palavra passa a ser por idioma.

A assinatura `TrackStation · by Douglas Voss` é igual nas quatro.

## Metadados por página

Cada uma das quatro páginas carrega:

- `<html lang="…">`: `pt-BR`, `en-US`, `es`, `fr-FR`;
- `canonical` da própria URL;
- o conjunto completo de cinco `hreflang` — os quatro idiomas mais
  `x-default` → raiz — **idêntico nas quatro páginas** (recíproco, exigência do
  Google para o sinal ser aceito);
- `og:url` própria, `og:locale` própria (`pt_BR`, `en_US`, `es_ES`, `fr_FR`) e
  `og:locale:alternate` com as outras três — o `es_ES` é território obrigatório
  no formato do Open Graph, e não contradiz o `hreflang="es"` sem território: um
  é exigência de formato do Facebook, o outro é sinal de alcance para o Google;
- `og:image` do próprio idioma;
- `theme-color` `#0E1116` e o `favicon`, iguais nas quatro.

## Seletor de idioma

Na barra superior, à direita, antes do chip de estado: quatro rótulos
serigrafados (`.rot`), o do idioma corrente como `<span>` marcado com
`aria-current="page"` e os outros três como `<a>`.

```
┌──────────────────────────────────────────────────────────┐
│ ▮ TrackStation®     PT EN ES FR   ● EM DESENVOLVIMENTO   │
└──────────────────────────────────────────────────────────┘
```

Quatro links de HTML puro — nenhum JavaScript novo, a regra do `<script>` único
continua intacta. `<nav>` com `aria-label` no idioma da página. O corrente em
`--text`, os outros em `--muted`, sublinhado no hover e `:focus-visible` já
herdado do global. A barra já tem `flex-wrap`, então em tela estreita o grupo
desce em vez de apertar.

Links relativos: da raiz, `en/`, `es/`, `fr/`; de dentro de um idioma, `../`
para o pt-BR e `../en/` para os irmãos. Assim o site continua funcionando
aberto por `file://`, como o README promete.

## Cartão de compartilhamento por idioma

Texto em português num link compartilhado em inglês é a desconexão que o site
acabou de corrigir no corpo do texto. Então: `assets/og.png` (pt-BR),
`og-en.png`, `og-es.png`, `og-fr.png`.

Para não multiplicar por quatro o CSS do cartão, o estilo sai de dentro do
`tools/og.html` e vai para `tools/og.css`; ficam quatro HTMLs finos, só com o
texto, e `tools/make_og.sh` passa a iterar sobre eles. O `@font-face` das duas
fontes locais mora em `tools/og.css`.

## Testes

`tests/test_page.py` hoje afirma o contrato de uma página. Passa a afirmar o
contrato **das quatro**, mais a paridade entre elas.

Refatoração: as checagens existentes viram parametrizadas por locale
(`pytest.mark.parametrize`) sobre uma tabela que declara, por idioma, o caminho
do arquivo, o `lang` esperado, o `og:locale`, a URL canônica, a palavra-ponte do
`<noscript>` e o prefixo relativo dos assets (`""` na raiz, `"../"` nos
idiomas).

Herdadas, agora por idioma: `lang` correto, `<title>` com conteúdo, `description`
com conteúdo, um único `<h1>`, `theme-color`, `alt` descritivo, zero requisição
externa, `<script>` único inline só para o mailto, e-mail fora do texto plano,
`<noscript>` com a ponte do idioma, assets referenciados existindo no disco
(resolvendo o `../`).

Novas, de paridade e de i18n:

- os cinco `hreflang` presentes e **idênticos** nas quatro páginas, e cada
  `href` de idioma resolvendo para um arquivo que existe no disco;
- `canonical` de cada página apontando para a própria URL, nunca para outra;
- `og:locale` correto e as três `og:locale:alternate` completas;
- as quatro páginas com o mesmo número de `.bloco` (3) e apontando para o mesmo
  `palco.png` e o mesmo `style.css` — drift estrutural falha;
- cada página linkando as outras três e marcando a própria com `aria-current`;
- `og:image` de cada página existindo no disco e sendo distinta das outras;
- os quatro cartões de `tools/` sem requisição externa e usando as fontes
  locais via `tools/og.css`.

Os testes de contraste e de exclusividade do ciano leem `style.css`, que é
único: seguem como estão.

## verify.sh

Ganha `HTTP 200` em `/en/`, `/es/` e `/fr/`, na mesma forma dos checks atuais
(duas tentativas, distinguindo `000` de resposta errada). O bloco de e-mail,
nameservers e DNSSEC não muda — é um domínio só.

## README

Documenta a estrutura de pastas, a política de tradução (a tabela de jargão, o
veto ao `playback` em francês, `tracks` e não `sampler` em inglês), o passo a
passo para acrescentar um idioma novo e o `make_og.sh` agora gerando quatro
cartões.

## Ordem de implementação

1. `style.css`: o seletor de idioma na barra (afeta as quatro páginas).
2. `index.html`: seletor, `hreflang`, `og:locale:alternate` no pt-BR.
3. Refatoração de `tests/` para parametrização por locale, ainda com um locale
   só — a suíte tem de ficar verde antes de as traduções entrarem.
4. `en/index.html`, depois `es/`, depois `fr/`.
5. Testes de paridade e de i18n.
6. `tools/og.css` + quatro cartões + `make_og.sh` iterando; gerar os PNGs.
7. `verify.sh` e `README.md`.
8. Capturas em 360/768/1440 de cada idioma, para conferir quebra de linha —
   alemão não entra aqui, mas francês é ~15% mais longo que português e o h1 é
   o lugar onde isso aparece.
