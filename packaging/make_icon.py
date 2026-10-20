"""Genera el ícono de dsound (barras de ecualizador sobre un cuadrado verde).

    python packaging/make_icon.py

Escribe:
- frontend/public/favicon.png  (pestaña del navegador e ícono de la bandeja)
- packaging/dsound.ico         (ejecutable e instalador de Windows)
"""

import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCENT = (62, 214, 122, 255)  # --color-accent
DARK = (11, 15, 13, 255)  # --color-bg
SIZE = 1024  # se dibuja grande y se achica, para bordes suaves


def draw() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=SIZE * 0.22, fill=ACCENT)
    heights = (0.30, 0.56, 0.78, 0.48, 0.64)  # alto de cada barra (proporción)
    bar_w = SIZE * 0.10
    gap = SIZE * 0.055
    total = len(heights) * bar_w + (len(heights) - 1) * gap
    x = (SIZE - total) / 2
    base = SIZE * 0.80
    for h in heights:
        top = base - h * SIZE * 0.62
        d.rounded_rectangle((x, top, x + bar_w, base), radius=bar_w / 2, fill=DARK)
        x += bar_w + gap
    return img


def main():
    img = draw()
    png = os.path.join(ROOT, "frontend", "public", "favicon.png")
    os.makedirs(os.path.dirname(png), exist_ok=True)
    img.resize((256, 256), Image.LANCZOS).save(png)
    ico = os.path.join(ROOT, "packaging", "dsound.ico")
    img.save(ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("listo:", png, ico)


if __name__ == "__main__":
    main()
