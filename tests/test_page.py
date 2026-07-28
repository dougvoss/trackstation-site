"""Verificação estrutural da landing page.

Não testa aparência — testa o que dá para afirmar sem olhar: estrutura,
metadados, ausência de requisição externa e contraste WCAG.
"""
import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Toda página HTML servida. O 404 é servido pelo GitHub Pages em qualquer
# caminho inexistente, então ele carrega o mesmo contrato de isolamento de rede
# e de assets existentes que a home.
PAGINAS = ("index.html", "404.html")

# Space Grotesk é a voz do produto; Space Mono carrega os rótulos serigrafados.
# Ambas auto-hospedadas: uma delas virando link do gstatic é requisição externa.
FONTES = ("space-grotesk-latin.woff2", "space-mono-latin.woff2")


def _read(nome):
    caminho = ROOT / nome
    assert caminho.exists(), f"{nome} não existe"
    return caminho.read_text(encoding="utf-8")


def _html():
    return _read("index.html")


def _css():
    return _read("style.css")


def _og_html():
    return _read("tools/og.html")


def _paleta():
    """Lê as custom properties de cor do :root do style.css.

    Medir contraste sobre literais hex repetidos no teste não prova nada sobre
    a página: trocar --muted na folha de estilo por qualquer cor reprovada
    deixaria a suíte verde. O número tem de sair do arquivo que é servido.
    """
    m = re.search(r":root\s*\{(.*?)\}", _css(), re.S)
    assert m, "bloco :root não encontrado em style.css"
    pares = re.findall(r"--([\w-]+)\s*:\s*(#[0-9A-Fa-f]{6})\b", m.group(1))
    assert pares, "nenhuma cor encontrada no :root de style.css"
    return {nome: valor.upper() for nome, valor in pares}


# Casa URL absoluta (https://…) e também protocolo-relativa (//cdn.exemplo.com).
# A protocolo-relativa é o vazamento mais plausível e escapava do padrão antigo.
# O look-behind exige delimitador de atributo ou de url() antes do "//", para
# não confundir com comentário de linha "// …" do JavaScript.
_EXTERNA = re.compile(r"""(?:https?://|(?<=["'(=])//)[^\s"')]+""")

_LD_JSON = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)


def _urls_externas(*textos):
    return [u for u in _EXTERNA.findall("\n".join(textos))
            if "trackstation.com.br" not in u]


def _sem_ld_json(html):
    """Remove os blocos de dados estruturados antes de varrer por URL externa.

    O `@context` do JSON-LD é `https://schema.org` e não é uma requisição: o
    navegador não busca aquela URL, ela é só o identificador do vocabulário. Mas
    ela casa com _EXTERNA como qualquer outra, e abrir exceção pelo domínio
    deixaria passar um `<img src="https://schema.org/…">` de verdade. Então o
    bloco sai da varredura geral e é auditado por test_json_ld_*, que afirma que
    a única URL externa dentro dele é exatamente aquele contexto.
    """
    return _LD_JSON.sub("", html)


def _luminancia(cor_hex):
    r, g, b = (int(cor_hex[i:i + 2], 16) / 255 for i in (1, 3, 5))
    def linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = linear(r), linear(g), linear(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    a, b = _luminancia(fg), _luminancia(bg)
    claro, escuro = max(a, b), min(a, b)
    return (claro + 0.05) / (escuro + 0.05)


# --- estrutura e metadados ---

def test_lang_pt_br():
    assert re.search(r'<html[^>]+lang="pt-BR"', _html())


def test_tem_titulo_com_conteudo():
    m = re.search(r"<title>(.+?)</title>", _html(), re.S)
    assert m and len(m.group(1).strip()) >= 20


def test_tem_meta_description_com_conteudo():
    m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', _html())
    assert m and len(m.group(1).strip()) >= 60


def test_um_unico_h1():
    assert len(re.findall(r"<h1[\s>]", _html())) == 1


def test_theme_color_e_o_ground():
    assert re.search(r'name="theme-color"[^>]+content="#0E1116"', _html(), re.I)


def test_imagem_do_palco_tem_alt_descritivo():
    m = re.search(r'<img[^>]+src="assets/palco\.png"[^>]*>', _html())
    assert m, "a imagem do Modo Palco não está na página"
    alt = re.search(r'alt="([^"]*)"', m.group(0))
    assert alt and len(alt.group(1)) >= 40, "alt ausente ou raso demais"


# --- isolamento de rede ---

@pytest.mark.parametrize("pagina", PAGINAS)
def test_nenhuma_requisicao_externa(pagina):
    externas = _urls_externas(_sem_ld_json(_read(pagina)), _css())
    assert not externas, f"URLs externas em {pagina}: {externas}"


def test_fontes_sao_locais():
    css = _css()
    for nome in FONTES:
        caminho = f"assets/fonts/{nome}"
        assert caminho in css, f"{nome} não é usada pela folha de estilo"
        woff2 = ROOT / caminho
        assert woff2.exists(), f"arquivo de {nome} não existe"
        assert woff2.stat().st_size < 60 * 1024, \
            f"{nome} grande demais para inline crítico"


def test_og_html_nenhuma_requisicao_externa():
    externas = _urls_externas(_og_html())
    assert not externas, f"URLs externas encontradas em tools/og.html: {externas}"


def test_og_html_fontes_sao_locais():
    html = _og_html()
    for nome in FONTES:
        assert f"assets/fonts/{nome}" in html, \
            f"o cartão não usa {nome} — divergiria da página"
        assert (ROOT / f"assets/fonts/{nome}").exists(), \
            f"arquivo de {nome} não existe"


def _assets_referenciados(html):
    """Todo caminho de asset citado num HTML, relativo à raiz do repositório.

    Cobre três formas, porque cada uma já foi ou pode ser a única referência a um
    arquivo: atributo direto (`src`/`href`), URL absoluta em qualquer contexto de
    aspas (`og:image` e o `image` do JSON-LD) e candidatos de `srcset`, onde o
    caminho vem seguido de um descritor de largura e não casaria com os outros
    dois padrões.
    """
    refs = set(re.findall(r'(?:src|href)="(assets/[^"]+)"', html))
    refs |= set(re.findall(
        r'"https://trackstation\.com\.br/(assets/[^"]+)"', html))
    for srcset in re.findall(r'srcset="([^"]+)"', html):
        for candidato in srcset.split(","):
            caminho = candidato.strip().split()[0]
            if caminho.startswith("assets/"):
                refs.add(caminho)
    return refs


@pytest.mark.parametrize("pagina", PAGINAS)
def test_imagens_referenciadas_existem_no_disco(pagina):
    """Todo asset citado na página existe de fato no repositório.

    Apagar assets/og.png quebra silenciosamente todo preview de link: o
    og:image é a única referência e nada mais no repositório aponta para ele.
    """
    refs = _assets_referenciados(_read(pagina))
    assert refs, f"nenhum asset referenciado em {pagina} — a extração quebrou"
    faltando = sorted(r for r in refs if not (ROOT / r).exists())
    assert not faltando, f"assets citados em {pagina} que não existem: {faltando}"


# --- proteção do e-mail ---

def test_email_nao_aparece_em_texto_plano():
    assert "contact@trackstation.com.br" not in _html()


def test_tem_fallback_sem_javascript():
    html = _html()
    assert "<noscript>" in html
    assert "arroba" in html, "o fallback precisa do endereço legível a humano"


# --- configuração do GitHub Pages ---

def test_cname_exato():
    assert _read("CNAME").strip() == "trackstation.com.br"


def test_nojekyll_existe():
    assert (ROOT / ".nojekyll").exists()


# --- restrições globais ---

def test_javascript_apenas_para_o_mailto():
    """Um único <script> executável, inline, e só para montar o mailto.

    Um snippet de analytics embutido, sem nenhuma URL absoluta, passaria por
    toda a suíte de "zero requisição externa" — que existe para barrá-lo.

    O bloco de dados estruturados é um <script> para o parser de HTML, mas não é
    código: `type="application/ld+json"` não é executado por navegador nenhum.
    Ele é contado à parte, e continua sendo exatamente um.
    """
    html = _html()
    blocos = re.findall(r"<script([^>]*)>(.*?)</script>", html, re.S)
    assert len(blocos) == html.count("<script"), "algum <script> não fecha"
    dados = [b for b in blocos if "application/ld+json" in b[0]]
    executaveis = [b for b in blocos if "application/ld+json" not in b[0]]
    assert len(dados) == 1, f"esperado 1 bloco ld+json, achei {len(dados)}"
    assert len(executaveis) == 1, \
        f"esperado exatamente 1 <script> executável, achei {len(executaveis)}"
    atributos, corpo = executaveis[0]
    assert "src" not in atributos, "o único <script> deve ser inline, sem src"
    assert "mailto:" in corpo, "o único <script> existe para montar o mailto"


def test_404_nao_tem_javascript():
    """A página de erro não monta contato, então não tem por que ter script.

    Comentário que documenta a ausência não conta como uso — mesma regra de
    test_faint_nao_e_usado_em_texto.
    """
    sem_comentarios = re.sub(r"<!--.*?-->", "", _read("404.html"), flags=re.S)
    assert "<script" not in sem_comentarios


# --- dados estruturados ---

def test_json_ld_descreve_o_aplicativo():
    m = _LD_JSON.search(_html())
    assert m, "bloco application/ld+json ausente"
    dados = json.loads(m.group(1))
    assert dados["@type"] == "SoftwareApplication"
    assert dados["name"] == "TrackStation"
    assert dados["url"] == "https://trackstation.com.br/"
    # A pergunta "roda no meu setup?" é a razão de o bloco existir: sem
    # operatingSystem, o resultado de busca não diz em que máquina o app roda.
    sistemas = dados["operatingSystem"]
    for sistema in ("macOS", "Windows", "Linux"):
        assert sistema in sistemas, f"{sistema} ausente em operatingSystem"
    # Aqui o campo é factual e não tem onde pendurar ressalva: o resultado de
    # busca mostraria "Android" sem o "em desenvolvimento" que a página diz.
    # Entra quando existir app de verdade.
    for pendente in ("iOS", "Android"):
        assert pendente not in sistemas, \
            (f"{pendente} não roda ainda — o dado estruturado não tem como "
             f"dizer 'em desenvolvimento', então não deve prometer")


def test_json_ld_nao_carrega_url_externa_alguma():
    """Dentro do bloco, a única URL externa admitida é o vocabulário.

    É o contrapeso de _sem_ld_json: o bloco sai da varredura geral, então a
    garantia de zero requisição externa dele tem de vir daqui.
    """
    m = _LD_JSON.search(_html())
    assert m, "bloco application/ld+json ausente"
    externas = set(_urls_externas(m.group(1)))
    assert externas == {"https://schema.org"}, \
        f"URL inesperada no bloco de dados estruturados: {externas}"


# --- cartão de compartilhamento ---

def test_og_image_declara_dimensoes_e_alt():
    html = _html()
    for prop, valor in (("og:image:width", "1200"), ("og:image:height", "630")):
        assert re.search(
            rf'property="{prop}"[^>]+content="{valor}"', html), f"{prop} ausente"
    alt = re.search(r'property="og:image:alt"[^>]+content="([^"]+)"', html)
    assert alt and len(alt.group(1).strip()) >= 20, "og:image:alt ausente ou raso"


def test_og_image_tem_as_dimensoes_que_declara():
    """As dimensões declaradas são as do arquivo, não um número copiado.

    Declarar 1200x630 e servir outro tamanho é pior que não declarar: o scraper
    reserva o espaço errado e o card sai distorcido.
    """
    from PIL import Image
    with Image.open(ROOT / "assets/og.png") as img:
        assert img.size == (1200, 630), f"assets/og.png está em {img.size}"


def test_twitter_card_grande():
    assert re.search(r'name="twitter:card"[^>]+content="summary_large_image"',
                     _html()), "sem esta linha o X renderiza o card pequeno"


# --- peso da página ---

def test_apple_touch_icon_usa_o_icone_grande():
    """O ícone de 512px serve o atalho de tela inicial, não a barra de marca."""
    m = re.search(r'rel="apple-touch-icon"[^>]+href="([^"]+)"', _html())
    assert m, "apple-touch-icon ausente"
    assert m.group(1) == "assets/icon.png"


def test_marca_nao_serve_o_icone_de_512():
    """A barra exibe a marca a 40px; servir 512px ali custava 41 KB.

    Já era o segundo maior asset da página, atrás só do print do palco.
    """
    m = re.search(r'<span class="marca">.*?</span>', _html(), re.S)
    assert m, "barra de marca não encontrada"
    assert 'src="assets/icon.png"' not in m.group(0), \
        "a barra voltou a servir o ícone de 512px"


def test_fonte_do_titulo_tem_preload():
    m = re.search(r'<link[^>]+rel="preload"[^>]+>', _html())
    assert m, "sem preload, o h1 aparece na fonte de sistema antes de trocar"
    tag = m.group(0)
    assert "space-grotesk" in tag, "a fonte pré-carregada é a do título"
    assert 'as="font"' in tag and "crossorigin" in tag, \
        "preload de fonte sem as=font e crossorigin é baixado duas vezes"


def test_palco_tem_variantes_e_todas_sao_mais_leves_que_o_png():
    """O <picture> existe para economizar bytes; se não economiza, é só peso.

    Uma variante maior que o PNG original significaria encode errado — e o
    navegador prefere o WebP, então a página ficaria mais pesada que antes.
    """
    html = _html()
    variantes = sorted(v for v in _assets_referenciados(html)
                       if v.startswith("assets/palco-"))
    assert len(variantes) >= 3, \
        f"esperadas ao menos 3 larguras no srcset, achei {variantes}"
    png = (ROOT / "assets/palco.png").stat().st_size
    pesadas = [v for v in variantes if (ROOT / v).stat().st_size >= png]
    assert not pesadas, f"variantes não mais leves que o PNG: {pesadas}"


def test_variante_nativa_do_palco_esta_sincronizada_com_o_png():
    """A variante de 1920 é pixel-idêntica ao PNG — e é por isso que ela é lossless.

    Este é o teste que a nota do README não consegue ser: trocar `palco.png` sem
    rodar `tools/make_variants.py` deixaria todo navegador com WebP (ou seja,
    todos) vendo a tela antiga, enquanto a suíte seguia verde e a captura do
    `shots.sh` mostrava a nova. Comparar sem perda é possível justamente porque a
    largura nativa não reamostra; as reduzidas não podem ser conferidas assim.
    """
    from PIL import Image
    with Image.open(ROOT / "assets/palco.png") as png, \
         Image.open(ROOT / "assets/palco-1920.webp") as webp:
        assert webp.size == png.size, \
            f"variante nativa em {webp.size}, PNG em {png.size} — regenerar"
        assert webp.convert("RGB").tobytes() == png.convert("RGB").tobytes(), \
            ("assets/palco-1920.webp não corresponde ao PNG atual — "
             "rode ./tools/make_variants.py")


def test_picture_do_palco_mantem_o_png_como_fallback():
    """O <img> continua apontando para o PNG.

    É ele que carrega o alt, o og aponta para o mesmo produto e é o único
    caminho para quem não recebe WebP.
    """
    assert re.search(r'<img[^>]+src="assets/palco\.png"', _html())


# --- descoberta ---

def test_robots_aponta_para_o_sitemap():
    robots = _read("robots.txt")
    assert "Sitemap: https://trackstation.com.br/sitemap.xml" in robots
    assert not re.search(r"^Disallow:\s*/\s*$", robots, re.M), \
        "Disallow: / esconderia o site inteiro dos buscadores"


def test_sitemap_lista_a_home_e_so_urls_do_dominio():
    sitemap = _read("sitemap.xml")
    locs = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    assert "https://trackstation.com.br/" in locs, "a home não está no sitemap"
    fora = [u for u in locs if not u.startswith("https://trackstation.com.br/")]
    assert not fora, f"URLs de outro domínio no sitemap: {fora}"
    assert re.search(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", sitemap), \
        "lastmod é a única informação que o sitemap acrescenta ao hreflang"


def test_404_e_da_mesma_identidade_e_nao_indexavel():
    html = _read("404.html")
    assert 'href="style.css"' in html, \
        "o 404 sem a folha de estilo é a página branca do GitHub com outro texto"
    assert re.search(r'name="robots"[^>]+content="[^"]*noindex', html), \
        "página de erro indexada entra no resultado de busca"
    assert 'href="/"' in html, "o 404 precisa de caminho de volta"
    assert "og:" not in html, "página de erro não deve gerar card de compartilhamento"


# --- ficha técnica ---

def _ficha():
    m = re.search(r'<section class="ficha".*?</section>', _html(), re.S)
    assert m, "seção de ficha técnica ausente"
    return m.group(0)


def test_ficha_responde_onde_roda():
    """As plataformas na página, não só no JSON-LD.

    O dado estruturado serve o buscador; quem está decidindo se instala precisa
    ler na tela.
    """
    ficha = _ficha()
    for sistema in ("macOS", "Windows", "Linux", "iOS", "Android"):
        assert sistema in ficha, f"{sistema} ausente na ficha técnica"


def test_ficha_nao_promete_mobile_como_pronto():
    """iOS e Android aparecem, mas nunca sem a ressalva ao lado.

    O risco que este teste cobre é de edição, não de código: alguém consolida as
    duas linhas numa só — "macOS · Windows · Linux · iOS · Android" — porque fica
    mais limpo, e a página passa a prometer dois apps que não existem. Enquanto o
    mobile não sair, a linha que cita iOS/Android tem de carregar a ressalva.
    """
    ficha = _ficha()
    linhas = re.findall(r'<div class="ficha-linha">(.*?)</div>', ficha, re.S)
    assert linhas, "nenhuma linha encontrada na ficha"
    for linha in linhas:
        if "iOS" in linha or "Android" in linha:
            assert "em desenvolvimento" in linha, \
                ("a linha que cita iOS/Android precisa da ressalva: "
                 f"{' '.join(linha.split())}")
            break
    else:
        raise AssertionError("nenhuma linha da ficha cita iOS ou Android")


def test_tema_escuro_fixo_sem_prefers_color_scheme():
    """Tema escuro fixo: a página não segue a preferência de tema do sistema.

    prefers-reduced-motion é outra media query e continua permitida, e
    `color-scheme: dark` também — aquela declara o tema fixo, não lê
    preferência. Comentário que cita a proibição não conta como uso, mesma
    regra de test_faint_nao_e_usado_em_texto.
    """
    sem_comentarios = re.sub(r"/\*.*?\*/", "", _css(), flags=re.S)
    assert "prefers-color-scheme" not in sem_comentarios, \
        "o tema é escuro fixo — não seguir prefers-color-scheme"


def test_ciano_e_exclusivo_do_vs():
    """Ciano é o VS e nada mais. A declaração em :root é definição, não uso.

    Já regrediu uma vez neste repositório: um commit levou
    `color: var(--cyan)` para `.contato a` e outro precisou removê-lo.
    """
    css = re.sub(r"/\*.*?\*/", "", _css(), flags=re.S)
    css = re.sub(r":root\s*\{.*?\}", "", css, flags=re.S)
    usos = [sel.strip()
            for sel, corpo in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
            if "--cyan" in corpo or "#35C6D6" in corpo.upper()]
    assert usos == [".vs"], f"ciano pertence ao VS; apareceu também em: {usos}"


def test_frase_de_servico_nao_e_caixa_alta():
    """A serigrafia é para rótulo curto, não para frase.

    `.canal-nota` e `.legenda` usam a classe .rot pela fonte mono, e .rot traz
    `text-transform: uppercase` junto. Em 360px as duas viravam bloco de
    maiúsculas espaçadas de duas e três linhas — o ponto mais difícil de ler da
    página. Cada uma tem de desligar a caixa alta explicitamente.
    """
    css = re.sub(r"/\*.*?\*/", "", _css(), flags=re.S)
    for seletor in (".canal-nota", ".legenda"):
        m = re.search(rf"{re.escape(seletor)}\s*\{{([^}}]*)\}}", css)
        assert m, f"regra de {seletor} não encontrada"
        assert "text-transform: none" in m.group(1), \
            f"{seletor} é frase: precisa desligar a caixa alta herdada de .rot"


# --- contraste (medido na paleta que a folha de estilo declara de fato) ---

def test_paleta_do_css_esta_completa():
    p = _paleta()
    faltando = [n for n in ("ground", "surface", "text", "muted", "amber", "cyan")
                if n not in p]
    assert not faltando, f"cores ausentes no :root de style.css: {faltando}"


def test_corpo_atinge_aaa():
    p = _paleta()
    assert ratio(p["text"], p["ground"]) >= 7.0


def test_texto_secundario_atinge_aa():
    p = _paleta()
    assert ratio(p["muted"], p["ground"]) >= 4.5
    assert ratio(p["muted"], p["surface"]) >= 4.5


def test_acentos_atingem_aa():
    p = _paleta()
    assert ratio(p["amber"], p["ground"]) >= 4.5   # click
    assert ratio(p["cyan"], p["ground"]) >= 4.5    # VS


def test_faint_nao_e_usado_em_texto():
    # Comentário que documenta a proibição não conta como uso.
    sem_comentarios = re.sub(r"/\*.*?\*/", "", _css(), flags=re.S)
    assert "#5C6675" not in sem_comentarios, "faint reprova AA (3,25:1) — não usar"
