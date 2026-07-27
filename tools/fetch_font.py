#!/usr/bin/env python3
"""Baixa os subsets latin das fontes do site para assets/fonts/.

Space Grotesk é a voz do produto; Space Mono é a origem tipográfica dela e
carrega os rótulos serigrafados da página.

O subset latin cobre o português (Ã, Ç, É, Õ estão em U+00C0–U+00FF).
Extrai a URL do CSS em vez de fixá-la, porque os hashes do gstatic rotacionam.
"""
import pathlib
import re
import subprocess
import sys

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
FONTES = pathlib.Path(__file__).resolve().parent.parent / "assets/fonts"

# (arquivo de destino, URL do CSS do Google Fonts). Space Grotesk é variável no
# eixo de peso; Space Mono é estática, e o site só usa o peso 400 dela.
ALVOS = (
    ("space-grotesk-latin.woff2",
     "https://fonts.googleapis.com/css2"
     "?family=Space+Grotesk:wght@300..700&display=swap"),
    ("space-mono-latin.woff2",
     "https://fonts.googleapis.com/css2"
     "?family=Space+Mono:wght@400&display=swap"),
)


def baixar(url, args=()):
    try:
        return subprocess.run(
            # -f faz o curl sair com erro em resposta não-2xx. Sem ele, um 404
            # do gstatic voltava como "sucesso" com corpo de HTML de erro e o
            # except abaixo era código morto.
            ["curl", "-sS", "-f", "-m", "30", "-A", UA, *args, url],
            capture_output=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        sys.exit(f"curl falhou: {e.stderr.decode(errors='replace')}")


def url_do_subset_latin(css_url):
    css = baixar(css_url).decode("utf-8")
    blocos = re.findall(r"/\*\s*([a-z-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", css, re.S)
    latin = [corpo for nome, corpo in blocos if nome == "latin"]
    if not latin:
        sys.exit(f"subset latin não encontrado no CSS de {css_url}")
    m = re.search(r"url\((https://[^)]+)\)", latin[0])
    if not m:
        sys.exit(f"URL da fonte não encontrada no bloco latin de {css_url}")
    return m.group(1)


def main():
    FONTES.mkdir(parents=True, exist_ok=True)
    for nome, css_url in ALVOS:
        dados = baixar(url_do_subset_latin(css_url))
        if dados[:4] != b"wOF2":
            sys.exit(f"{nome}: resposta não é woff2 (começa com {dados[:4]!r})")
        (FONTES / nome).write_bytes(dados)
        print(f"{nome}: {len(dados)} bytes ({len(dados) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
