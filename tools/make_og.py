#!/usr/bin/env python3
"""Compõe assets/og.png (1200x630) a partir do print e do ícone.

Recorta a faixa superior do print, escurece, e sobrepõe ícone e nome.
1200x630 é a proporção que WhatsApp, Telegram e redes sociais esperam.
"""
import pathlib

from PIL import Image

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GROUND = (0x0E, 0x11, 0x16)
L, A = 1200, 630

tela = Image.new("RGB", (L, A), GROUND)

print_palco = Image.open(RAIZ / "assets/palco.png").convert("RGB")
escala = L / print_palco.width
redimensionado = print_palco.resize(
    (L, round(print_palco.height * escala)), Image.LANCZOS)
faixa = redimensionado.crop((0, 0, L, min(A, redimensionado.height)))

# Escurece o print para o texto sobreposto ficar legível.
escuro = Image.blend(faixa, Image.new("RGB", faixa.size, GROUND), 0.62)
tela.paste(escuro, (0, 0))

icone = Image.open(RAIZ / "assets/icon.png").convert("RGBA")
icone = icone.resize((128, 128), Image.LANCZOS)
tela.paste(icone, (72, A - 128 - 72), icone)

destino = RAIZ / "assets/og.png"
tela.save(destino, optimize=True)
print(f"og.png {tela.size[0]}x{tela.size[1]} — {destino.stat().st_size} bytes")
