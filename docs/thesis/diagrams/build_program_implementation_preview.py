from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).with_name("12_program_implementation_preview.png")

W, H = 1920, 1080
BG = "#F3F5FA"
INK = "#111111"
LINE = "#111111"
BOX_FILL = "#F7F8FC"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    if Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


TITLE = font(36, True)
LABEL = font(30, True)
BOX = font(28)
EDGE = font(24)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def tabbed_rect(rect: tuple[int, int, int, int], title: str, tab_width: int = 330) -> None:
    x1, y1, x2, y2 = rect
    tab_h = 54
    d.polygon(
        [
            (x1, y1 + tab_h),
            (x1, y1),
            (x1 + tab_width, y1),
            (x1 + tab_width + 26, y1 + tab_h),
            (x2, y1 + tab_h),
            (x2, y2),
            (x1, y2),
        ],
        fill=BOX_FILL,
        outline=LINE,
    )
    d.line((x1, y1 + tab_h, x2, y1 + tab_h), fill=LINE, width=3)
    d.line((x1, y1, x1 + tab_width, y1), fill=LINE, width=3)
    d.line((x1 + tab_width, y1, x1 + tab_width + 26, y1 + tab_h), fill=LINE, width=3)
    d.line((x1 + tab_width + 26, y1 + tab_h, x2, y1 + tab_h), fill=LINE, width=3)
    d.line((x2, y1 + tab_h, x2, y2), fill=LINE, width=3)
    d.line((x2, y2, x1, y2), fill=LINE, width=3)
    d.line((x1, y2, x1, y1), fill=LINE, width=3)
    d.text((x1 + 14, y1 + 8), title, fill=INK, font=LABEL)


def component_icon(x: int, y: int) -> None:
    d.rectangle((x, y, x + 42, y + 30), outline=LINE, width=2)
    d.rectangle((x - 10, y + 7, x + 6, y + 14), outline=LINE, width=2)
    d.rectangle((x - 10, y + 19, x + 6, y + 26), outline=LINE, width=2)


def component(rect: tuple[int, int, int, int], text: str, icon: bool = True) -> None:
    x1, y1, x2, y2 = rect
    d.rounded_rectangle(rect, radius=7, fill=BOX_FILL, outline=LINE, width=2)
    if icon:
        component_icon(x2 - 64, y1 + 18)
    lines = text.split("\n")
    total_h = len(lines) * 34
    yy = y1 + (y2 - y1 - total_h) / 2
    for line in lines:
        bb = d.textbbox((0, 0), line, font=BOX)
        d.text((x1 + (x2 - x1 - (bb[2] - bb[0])) / 2, yy), line, fill=INK, font=BOX)
        yy += 34


def anchor(rect: tuple[int, int, int, int], side: str) -> tuple[int, int]:
    x1, y1, x2, y2 = rect
    if side == "l":
        return x1, (y1 + y2) // 2
    if side == "r":
        return x2, (y1 + y2) // 2
    if side == "t":
        return (x1 + x2) // 2, y1
    if side == "b":
        return (x1 + x2) // 2, y2
    raise ValueError(side)


def arrow(points: list[tuple[int, int]], text: str = "", text_xy: tuple[int, int] | None = None) -> None:
    d.line(points, fill=LINE, width=3)
    a, b = points[-2], points[-1]
    if abs(b[0] - a[0]) >= abs(b[1] - a[1]):
        head = [(b[0], b[1]), (b[0] - 18, b[1] - 10), (b[0] - 18, b[1] + 10)] if b[0] >= a[0] else [(b[0], b[1]), (b[0] + 18, b[1] - 10), (b[0] + 18, b[1] + 10)]
    else:
        head = [(b[0], b[1]), (b[0] - 10, b[1] - 18), (b[0] + 10, b[1] - 18)] if b[1] >= a[1] else [(b[0], b[1]), (b[0] - 10, b[1] + 18), (b[0] + 10, b[1] + 18)]
    d.polygon(head, fill=LINE)
    if text and text_xy:
        d.text(text_xy, text, fill=INK, font=EDGE)


d.text((90, 35), "Программная реализация MindHelper", fill=INK, font=TITLE)

SERVER = (340, 105, 1685, 420)
CLIENT = (165, 520, 1735, 990)
WEB_PANEL = (985, 620, 1645, 840)
TG_PANEL = (265, 620, 855, 840)

tabbed_rect(SERVER, "Серверная часть", 390)
tabbed_rect(CLIENT, "Клиентская часть", 390)
tabbed_rect(WEB_PANEL, "Веб-страница", 330)
tabbed_rect(TG_PANEL, "Telegram-бот", 330)

API = (455, 205, 780, 310)
DB = (900, 205, 1225, 310)
SAFETY = (455, 335, 780, 390)
OLLAMA = (900, 335, 1225, 390)
WEB = (1045, 710, 1590, 805)
TG = (330, 710, 790, 805)

component(API, "Django REST API")
component(DB, "PostgreSQL")
component(SAFETY, "Safety-flow")
component(OLLAMA, "Ollama / Qwen3")
component(WEB, "React / Vite\nWeb-интерфейс")
component(TG, "python-telegram-bot\nLong polling")

arrow([anchor(API, "r"), anchor(DB, "l")])
arrow([(620, 310), (620, 335)])
arrow([anchor(SAFETY, "r"), anchor(OLLAMA, "l")])

arrow([anchor(TG, "t"), (560, 525), (430, 525), (430, 257), anchor(API, "l")], "Использует REST API", (625, 470))
arrow([anchor(WEB, "t"), (1318, 525), (710, 525), (710, 310)], "Использует REST API", (1110, 470))

img.save(OUT)
print(OUT)
