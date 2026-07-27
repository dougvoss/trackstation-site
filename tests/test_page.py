"""Verificação estrutural da landing page.

Não testa aparência — testa o que dá para afirmar sem olhar: estrutura,
metadados, ausência de requisição externa e contraste WCAG.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

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


def _urls_externas(*textos):
    return [u for u in _EXTERNA.findall("\n".join(textos))
            if "trackstation.com.br" not in u]


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

def test_nenhuma_requisicao_externa():
    externas = _urls_externas(_html(), _css())
    assert not externas, f"URLs externas encontradas: {externas}"


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


def test_imagens_referenciadas_existem_no_disco():
    """Todo asset citado na página existe de fato no repositório.

    Apagar assets/og.png quebra silenciosamente todo preview de link: o
    og:image é a única referência e nada mais no repositório aponta para ele.
    """
    html = _html()
    refs = set(re.findall(r'(?:src|href)="(assets/[^"]+)"', html))
    refs |= set(re.findall(
        r'content="https://trackstation\.com\.br/(assets/[^"]+)"', html))
    assert refs, "nenhum asset referenciado encontrado — a extração quebrou"
    faltando = sorted(r for r in refs if not (ROOT / r).exists())
    assert not faltando, f"assets referenciados que não existem: {faltando}"


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
    """Um único <script>, inline, e só para montar o mailto.

    Um snippet de analytics embutido, sem nenhuma URL absoluta, passaria por
    toda a suíte de "zero requisição externa" — que existe para barrá-lo.
    """
    html = _html()
    assert html.count("<script") == 1, \
        f"esperado exatamente 1 <script>, achei {html.count('<script')}"
    m = re.search(r"<script([^>]*)>(.*?)</script>", html, re.S)
    assert m, "o <script> não fecha"
    atributos, corpo = m.group(1), m.group(2)
    assert "src" not in atributos, "o único <script> deve ser inline, sem src"
    assert "mailto:" in corpo, "o único <script> existe para montar o mailto"


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
