"""Verificação estrutural da landing page.

Não testa aparência — testa o que dá para afirmar sem olhar: estrutura,
metadados, ausência de requisição externa e contraste WCAG.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _read(nome):
    caminho = ROOT / nome
    assert caminho.exists(), f"{nome} não existe"
    return caminho.read_text(encoding="utf-8")


def _html():
    return _read("index.html")


def _css():
    return _read("style.css")


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
    urls = re.findall(r"https?://[^\s\"')]+", _html() + _css())
    externas = [u for u in urls if "trackstation.com.br" not in u]
    assert not externas, f"URLs externas encontradas: {externas}"


def test_fonte_e_local():
    css = _css()
    assert "assets/fonts/space-grotesk-latin.woff2" in css
    woff2 = ROOT / "assets/fonts/space-grotesk-latin.woff2"
    assert woff2.exists(), "arquivo da fonte não existe"
    assert woff2.stat().st_size < 60 * 1024, "fonte grande demais para inline crítico"


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


# --- contraste (valores medidos, não estimados) ---

GROUND = "#0E1116"
SURFACE = "#161B22"

def test_corpo_atinge_aaa():
    assert ratio("#EAEEF3", GROUND) >= 7.0


def test_texto_secundario_atinge_aa():
    assert ratio("#8A94A3", GROUND) >= 4.5
    assert ratio("#8A94A3", SURFACE) >= 4.5


def test_acentos_atingem_aa():
    assert ratio("#F5B841", GROUND) >= 4.5   # click
    assert ratio("#35C6D6", GROUND) >= 4.5   # VS


def test_faint_nao_e_usado_em_texto():
    # Comentário que documenta a proibição não conta como uso.
    sem_comentarios = re.sub(r"/\*.*?\*/", "", _css(), flags=re.S)
    assert "#5C6675" not in sem_comentarios, "faint reprova AA (3,25:1) — não usar"
