from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).with_name("09_er_entities_compact_slide_preview.png")

W, H = 1920, 1080
BG = "white"
INK = "#0f172a"
MUTED = "#475569"
LINE = "#64748b"
GROUP = "#cbd5e1"
BLUE = "#eaf3ff"
GREEN = "#eafbf1"
ORANGE = "#fff4e6"
PURPLE = "#f3ecff"
GRAY = "#f8fafc"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


TITLE = font(30, True)
GROUP_FONT = font(22, True)
BOX_FONT = font(20, False)


def box(draw: ImageDraw.ImageDraw, name: str, xy: tuple[int, int, int, int], fill: str) -> None:
    draw.rounded_rectangle(xy, radius=16, fill=fill, outline="#334155", width=2)
    x1, y1, x2, y2 = xy
    bbox = draw.textbbox((0, 0), name, font=BOX_FONT)
    draw.text(
        (x1 + (x2 - x1 - (bbox[2] - bbox[0])) / 2, y1 + (y2 - y1 - (bbox[3] - bbox[1])) / 2 - 2),
        name,
        fill=INK,
        font=BOX_FONT,
    )


def group(draw: ImageDraw.ImageDraw, title: str, xy: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(xy, radius=20, outline=GROUP, width=3)
    x1, y1, x2, _ = xy
    draw.text((x1 + 18, y1 + 10), title, fill=MUTED, font=GROUP_FONT)


def center(xy: tuple[int, int, int, int]) -> tuple[int, int]:
    x1, y1, x2, y2 = xy
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def side(xy: tuple[int, int, int, int], where: str) -> tuple[int, int]:
    x1, y1, x2, y2 = xy
    if where == "r":
        return (x2, (y1 + y2) // 2)
    if where == "l":
        return (x1, (y1 + y2) // 2)
    if where == "t":
        return ((x1 + x2) // 2, y1)
    if where == "b":
        return ((x1 + x2) // 2, y2)
    raise ValueError(where)


def arrow(draw: ImageDraw.ImageDraw, a: tuple[int, int], b: tuple[int, int], color: str = LINE) -> None:
    ax, ay = a
    bx, by = b
    mx = (ax + bx) // 2
    points = [(ax, ay), (mx, ay), (mx, by), (bx, by)]
    draw.line(points, fill=color, width=2, joint="curve")
    # small arrowhead
    if bx >= mx:
        head = [(bx, by), (bx - 10, by - 6), (bx - 10, by + 6)]
    else:
        head = [(bx, by), (bx + 10, by - 6), (bx + 10, by + 6)]
    draw.polygon(head, fill=color)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

d.text((70, 32), "ER-модель MindHelper: сущности и связи", fill=INK, font=TITLE)
d.line((70, 78, 570, 78), fill="#22b8d6", width=5)

# Groups
group(d, "Identity", (60, 120, 405, 390))
group(d, "Chat", (525, 120, 825, 330))
group(d, "Safety", (995, 110, 1510, 385))
group(d, "Model", (610, 405, 910, 535))
group(d, "Assessments", (1035, 445, 1840, 700))
group(d, "Directory", (80, 560, 735, 830))
group(d, "Administration", (1180, 790, 1780, 1005))

nodes = {
    "user_account": (90, 190, 245, 250, BLUE),
    "role": (95, 290, 245, 350, GRAY),
    "user_role": (260, 290, 380, 350, GRAY),
    "channel_account": (240, 190, 395, 250, BLUE),
    "user_chat": (570, 180, 710, 240, BLUE),
    "chat_message": (650, 280, 810, 340, BLUE),
    "emergency_resource": (1030, 185, 1235, 245, GRAY),
    "crisis_event": (1260, 285, 1415, 345, ORANGE),
    "safety_audit_log": (1340, 155, 1510, 215, ORANGE),
    "neural_model_version": (640, 455, 880, 515, PURPLE),
    "assessment_template": (1070, 520, 1275, 580, GREEN),
    "assessment_question": (1265, 610, 1485, 670, GREEN),
    "assessment_session": (1395, 505, 1605, 565, GREEN),
    "assessment_answer": (1605, 610, 1815, 670, GREEN),
    "specialist": (115, 640, 275, 700, GRAY),
    "specialist_location": (325, 715, 545, 775, GRAY),
    "appointment": (560, 635, 705, 695, GRAY),
    "moderation_case": (1225, 875, 1425, 935, PURPLE),
    "site_content": (1515, 875, 1710, 935, PURPLE),
}

def n(name: str) -> tuple[int, int, int, int]:
    x1, y1, x2, y2, _ = nodes[name]
    return (x1, y1, x2, y2)

edges = [
    ("user_account", "user_role", "b", "l"),
    ("role", "user_role", "r", "l"),
    ("user_account", "channel_account", "r", "l"),
    ("user_account", "user_chat", "r", "l"),
    ("neural_model_version", "user_chat", "t", "b"),
    ("user_chat", "chat_message", "r", "l"),
    ("user_chat", "crisis_event", "r", "l"),
    ("chat_message", "crisis_event", "r", "l"),
    ("emergency_resource", "crisis_event", "r", "l"),
    ("user_chat", "safety_audit_log", "r", "l"),
    ("chat_message", "safety_audit_log", "r", "l"),
    ("crisis_event", "safety_audit_log", "t", "b"),
    ("neural_model_version", "safety_audit_log", "r", "l"),
    ("assessment_template", "assessment_question", "r", "l"),
    ("assessment_template", "assessment_session", "r", "l"),
    ("user_account", "assessment_session", "b", "l"),
    ("user_chat", "assessment_session", "b", "l"),
    ("assessment_session", "assessment_answer", "r", "l"),
    ("assessment_question", "assessment_answer", "r", "l"),
    ("specialist", "specialist_location", "r", "l"),
    ("user_account", "appointment", "b", "l"),
    ("specialist", "appointment", "r", "l"),
    ("specialist_location", "appointment", "r", "l"),
    ("user_account", "neural_model_version", "b", "l"),
    ("user_account", "moderation_case", "b", "l"),
    ("user_account", "site_content", "r", "l"),
    ("user_chat", "moderation_case", "b", "l"),
    ("chat_message", "moderation_case", "b", "l"),
]

for src, dst, ss, ds in edges:
    arrow(d, side(n(src), ss), side(n(dst), ds))

# Draw entity boxes after relationships so lines do not cover labels.
for name, (x1, y1, x2, y2, fill) in nodes.items():
    box(d, name, (x1, y1, x2, y2), fill)

d.text((70, 1015), "Примечание: показаны только сущности и связи; поля таблиц намеренно скрыты для читаемости на слайде.", fill=MUTED, font=font(18))

img.save(OUT)
print(OUT)
