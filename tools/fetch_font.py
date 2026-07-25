#!/usr/bin/env python3
"""Baixa o subset latin da Space Grotesk para assets/fonts/.

O subset latin cobre o português (Ã, Ç, É, Õ estão em U+00C0–U+00FF).
Extrai a URL do CSS em vez de fixá-la, porque os hashes do gstatic rotacionam.
"""
import pathlib
import re
import subprocess
import sys

CSS_URL = ("https://fonts.googleapis.com/css2"
           "?family=Space+Grotesk:wght@300..700&display=swap")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
DESTINO = (pathlib.Path(__file__).resolve().parent.parent
           / "assets/fonts/space-grotesk-latin.woff2")


def baixar(url, args=()):
    return subprocess.run(
        ["curl", "-sS", "-m", "30", "-A", UA, *args, url],
        capture_output=True, check=True).stdout


def main():
    css = baixar(CSS_URL).decode("utf-8")
    blocos = re.findall(r"/\*\s*([a-z-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", css, re.S)
    latin = [corpo for nome, corpo in blocos if nome == "latin"]
    if not latin:
        sys.exit("subset latin não encontrado no CSS do Google Fonts")
    url = re.search(r"url\((https://[^)]+)\)", latin[0]).group(1)

    dados = baixar(url)
    if dados[:4] != b"wOF2":
        sys.exit(f"resposta não é woff2 (começa com {dados[:4]!r})")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_bytes(dados)
    print(f"{DESTINO.name}: {len(dados)} bytes ({len(dados) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
