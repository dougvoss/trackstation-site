#!/usr/bin/env python3
"""Gera as variantes leves dos dois assets pesados da página.

Rodado à mão, quando `assets/palco.png` ou `assets/icon.png` mudam.

Duas escolhas medidas, não arbitradas:

- **O 1920 sai lossless.** É print de interface: áreas planas e texto de 1px.
  Nessa imagem o WebP sem perda dá 101 KB e o com perda em q92 dá 138 KB — sem
  perda é ao mesmo tempo menor e pixel-idêntico. A regra se inverte nas
  variantes reduzidas, porque o reamostrado cria gradiente onde não havia.
- **As reduzidas saem em q92.** O conteúdo é setlist em corpo 7; abaixo disso o
  texto começa a borrar, e a economia extra não paga a legibilidade.

A ladder é 640 / 1040 / 1920, derivada do layout: 1040 é a largura de exibição
em CSS px no desktop (`--largura` 72rem menos gutter e menos o filete da
moldura), 1920 cobre densidade 2x, e 640 é o celular.
"""
import pathlib
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("erro: Pillow não instalado — pip install Pillow")

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"

# (largura, opções de encode). O 1920 é a largura nativa: não reamostra.
PALCO = [
    (640, {"quality": 92, "method": 6}),
    (1040, {"quality": 92, "method": 6}),
    (1920, {"lossless": True, "method": 6}),
]

# A marca é exibida a no máximo 40px (`.marca img`); 80px cobre densidade 2x.
# A fonte de 512px continua no repositório para o apple-touch-icon.
ICONE = 80


def kb(caminho):
    return caminho.stat().st_size / 1024


def gera_palco():
    origem = ASSETS / "palco.png"
    src = Image.open(origem).convert("RGB")
    print(f"{origem.name}: {src.width}x{src.height}, {kb(origem):.1f} KB")
    for largura, opcoes in PALCO:
        if largura > src.width:
            sys.exit(f"erro: variante de {largura}px maior que a fonte "
                     f"({src.width}px) — ampliar degradaria o print")
        img = (src if largura == src.width
               else src.resize((largura, round(src.height * largura / src.width)),
                               Image.Resampling.LANCZOS))
        saida = ASSETS / f"palco-{largura}.webp"
        img.save(saida, "WEBP", **opcoes)
        if saida.stat().st_size >= origem.stat().st_size:
            sys.exit(f"erro: {saida.name} não ficou menor que o PNG — "
                     f"servir a variante não economizaria nada")
        print(f"  {saida.name}: {kb(saida):.1f} KB")


def gera_icone():
    origem = ASSETS / "icon.png"
    img = Image.open(origem)
    print(f"{origem.name}: {img.width}x{img.height}, {kb(origem):.1f} KB")
    saida = ASSETS / f"icon-{ICONE}.png"
    img.resize((ICONE, ICONE), Image.Resampling.LANCZOS).save(saida, "PNG", optimize=True)
    print(f"  {saida.name}: {kb(saida):.1f} KB")


if __name__ == "__main__":
    gera_palco()
    gera_icone()
