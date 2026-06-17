"""生成应用图标 app.ico

深色圆角底 + 蓝色表头日历，配色对齐应用主题（accent #5e8cf0）。
重新生成：python tools/make_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

ACCENT = (94, 140, 240, 255)      # #5e8cf0
DARK_BG = (20, 21, 26, 255)
CARD = (245, 246, 250, 255)
RING = (36, 38, 46, 255)
CELL = (210, 216, 230, 255)

S = 256
OUT = Path(__file__).resolve().parent.parent / "src" / "assets" / "app.ico"


def build() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 深色圆角底
    d.rounded_rectangle([8, 8, 248, 248], radius=56, fill=DARK_BG)

    # 白色日历卡片
    d.rounded_rectangle([52, 72, 204, 200], radius=22, fill=CARD)
    # 蓝色表头（上圆角，下方补成直角与卡片衔接）
    d.rounded_rectangle([52, 72, 204, 126], radius=22, fill=ACCENT)
    d.rectangle([52, 104, 204, 126], fill=ACCENT)

    # 两个挂环
    d.rounded_rectangle([86, 58, 102, 86], radius=8, fill=RING)
    d.rounded_rectangle([154, 58, 170, 86], radius=8, fill=RING)

    # 日期格子：3 列 x 2 行，左上角高亮为 accent
    x0, y0, gap, sz = 70, 142, 16, 28
    for r in range(2):
        for c in range(3):
            x = x0 + c * (sz + gap)
            y = y0 + r * (sz + gap)
            fill = ACCENT if (r == 0 and c == 0) else CELL
            d.rounded_rectangle([x, y, x + sz, y + sz], radius=7, fill=fill)

    return img


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = build()
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(OUT, format="ICO", sizes=sizes)
    print("icon written:", OUT)


if __name__ == "__main__":
    main()
