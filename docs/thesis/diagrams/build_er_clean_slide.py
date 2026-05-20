from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).with_name("10_er_clean_slide_preview.png")

W, H = 1920, 1080
BG = "white"
INK = "#0F172A"
LINE = "#334155"
MUTED = "#64748B"
BLUE = "#EAF3FF"
GREEN = "#EAFBF1"
ORANGE = "#FFF4E6"
PURPLE = "#F3ECFF"
GRAY = "#F8FAFC"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    if Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


TITLE = load_font(34, True)
BOX = load_font(20)
SMALL = load_font(15)
GROUP = load_font(21, True)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def text_center(text: str, rect: tuple[int, int, int, int], font: ImageFont.FreeTypeFont, fill=INK):
    x1, y1, x2, y2 = rect
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - th) / 2 - 2), text, fill=fill, font=font)


def box(name: str, rect: tuple[int, int, int, int], fill: str):
    d.rounded_rectangle(rect, radius=14, fill=fill, outline=LINE, width=2)
    text_center(name, rect, BOX)


def group(title: str, rect: tuple[int, int, int, int]):
    d.rounded_rectangle(rect, radius=18, outline="#CBD5E1", width=3)
    d.text((rect[0] + 16, rect[1] + 8), title, fill=MUTED, font=GROUP)


def side(rect: tuple[int, int, int, int], s: str) -> tuple[int, int]:
    x1, y1, x2, y2 = rect
    if s == "l":
        return x1, (y1 + y2) // 2
    if s == "r":
        return x2, (y1 + y2) // 2
    if s == "t":
        return (x1 + x2) // 2, y1
    if s == "b":
        return (x1 + x2) // 2, y2
    raise ValueError(s)


def line(points: list[tuple[int, int]], label: str, label_pos: float = 0.5):
    d.line(points, fill=LINE, width=2)
    # Arrowhead at the last segment.
    (x1, y1), (x2, y2) = points[-2], points[-1]
    if abs(x2 - x1) >= abs(y2 - y1):
        if x2 >= x1:
            head = [(x2, y2), (x2 - 10, y2 - 6), (x2 - 10, y2 + 6)]
        else:
            head = [(x2, y2), (x2 + 10, y2 - 6), (x2 + 10, y2 + 6)]
    else:
        if y2 >= y1:
            head = [(x2, y2), (x2 - 6, y2 - 10), (x2 + 6, y2 - 10)]
        else:
            head = [(x2, y2), (x2 - 6, y2 + 10), (x2 + 6, y2 + 10)]
    d.polygon(head, fill=LINE)

    # Label near the longest segment.
    segments = []
    total = 0
    for a, b in zip(points, points[1:]):
        length = abs(b[0] - a[0]) + abs(b[1] - a[1])
        segments.append((a, b, length))
        total += length
    target = total * label_pos
    acc = 0
    lx, ly = points[0]
    for a, b, length in segments:
        if acc + length >= target:
            t = 0 if length == 0 else (target - acc) / length
            lx = int(a[0] + (b[0] - a[0]) * t)
            ly = int(a[1] + (b[1] - a[1]) * t)
            break
        acc += length
    bb = d.textbbox((0, 0), label, font=SMALL)
    pad = 3
    d.rectangle((lx - 4, ly - 13, lx + (bb[2] - bb[0]) + 4, ly + 7), fill=BG)
    d.text((lx, ly - 12), label, fill=LINE, font=SMALL)


d.text((60, 30), "ER-модель MindHelper: сущности и связи", fill=INK, font=TITLE)
d.line((60, 82, 650, 82), fill="#22B8D6", width=5)

# Groups
group("Identity", (55, 125, 440, 355))
group("Chat", (520, 125, 875, 355))
group("Safety", (960, 125, 1515, 355))
group("Model", (1545, 125, 1845, 260))
group("Assessments", (515, 470, 1035, 820))
group("Directory", (60, 500, 430, 865))
group("Administration", (1175, 505, 1700, 765))

R = {
    "user_account": (85, 195, 245, 250),
    "channel_account": (260, 195, 415, 250),
    "role": (95, 285, 205, 335),
    "user_role": (260, 285, 400, 335),
    "user_chat": (560, 190, 720, 245),
    "chat_message": (675, 285, 850, 340),
    "emergency_resource": (990, 190, 1210, 245),
    "crisis_event": (1215, 285, 1380, 340),
    "safety_audit_log": (1325, 190, 1490, 245),
    "neural_model_version": (1575, 180, 1815, 235),
    "assessment_template": (555, 545, 785, 600),
    "assessment_question": (555, 705, 785, 760),
    "assessment_session": (805, 545, 1000, 600),
    "assessment_answer": (805, 705, 1000, 760),
    "specialist": (95, 595, 245, 650),
    "specialist_location": (95, 740, 315, 795),
    "appointment": (255, 595, 400, 650),
    "moderation_case": (1220, 585, 1440, 640),
    "site_content": (1470, 585, 1665, 640),
}

fills = {
    "user_account": BLUE,
    "channel_account": BLUE,
    "user_chat": BLUE,
    "chat_message": BLUE,
    "crisis_event": ORANGE,
    "safety_audit_log": ORANGE,
    "neural_model_version": PURPLE,
    "assessment_template": GREEN,
    "assessment_question": GREEN,
    "assessment_session": GREEN,
    "assessment_answer": GREEN,
    "moderation_case": PURPLE,
    "site_content": PURPLE,
}

# Draw local connections first.
line([side(R["user_account"], "r"), side(R["channel_account"], "l")], "1:N")
line([side(R["role"], "r"), side(R["user_role"], "l")], "1:N")
line([side(R["user_account"], "b"), (165, 285), side(R["role"], "t")], "1:N")

line([side(R["user_account"], "r"), (490, 222), side(R["user_chat"], "l")], "1:1")
line([side(R["user_chat"], "r"), (760, 222), (760, 312), side(R["chat_message"], "l")], "1:N")

line([side(R["emergency_resource"], "r"), side(R["crisis_event"], "l")], "1:N")
line([side(R["crisis_event"], "t"), (1298, 220), side(R["safety_audit_log"], "l")], "1:N")
line([side(R["chat_message"], "r"), (930, 312), side(R["crisis_event"], "l")], "1:N")
line([side(R["chat_message"], "r"), (930, 330), (930, 220), side(R["safety_audit_log"], "l")], "1:N")

line([side(R["neural_model_version"], "l"), side(R["safety_audit_log"], "r")], "1:N")
line([side(R["neural_model_version"], "l"), (1530, 250), (720, 250), side(R["user_chat"], "r")], "1:N", 0.35)

line([side(R["assessment_template"], "r"), side(R["assessment_session"], "l")], "1:N")
line([side(R["assessment_template"], "b"), side(R["assessment_question"], "t")], "1:N")
line([side(R["assessment_question"], "r"), side(R["assessment_answer"], "l")], "1:N")
line([side(R["assessment_session"], "b"), side(R["assessment_answer"], "t")], "1:N")

line([side(R["specialist"], "b"), side(R["specialist_location"], "t")], "1:N")
line([side(R["specialist"], "r"), side(R["appointment"], "l")], "1:N")
line([side(R["specialist_location"], "r"), (335, 768), (335, 650), side(R["appointment"], "b")], "1:N")

line([side(R["moderation_case"], "r"), side(R["site_content"], "l")], "1:N")

# Cross-module links routed through outer corridors.
line([side(R["user_account"], "b"), (165, 430), (850, 430), side(R["assessment_session"], "t")], "1:N", 0.78)
line([side(R["user_chat"], "b"), (640, 455), (900, 455), side(R["assessment_session"], "t")], "1:N", 0.75)
line([side(R["user_account"], "l"), (35, 222), (35, 622), side(R["specialist"], "l")], "1:N", 0.75)
line([side(R["user_account"], "b"), (165, 890), (330, 890), side(R["appointment"], "b")], "1:N", 0.7)
line([side(R["user_account"], "r"), (450, 240), (450, 900), (1300, 900), side(R["moderation_case"], "b")], "1:N", 0.82)
line([side(R["user_chat"], "b"), (640, 410), (1240, 410), side(R["moderation_case"], "t")], "1:N", 0.78)
line([side(R["chat_message"], "b"), (765, 440), (1370, 440), side(R["moderation_case"], "t")], "1:N", 0.7)
line([side(R["user_account"], "r"), (450, 260), (450, 940), (1560, 940), side(R["site_content"], "b")], "1:N", 0.86)
line([side(R["user_account"], "r"), (500, 205), (500, 120), (1695, 120), side(R["neural_model_version"], "t")], "1:N", 0.72)
line([side(R["user_chat"], "r"), (900, 205), (900, 330), side(R["crisis_event"], "l")], "1:N", 0.45)
line([side(R["user_chat"], "r"), (900, 225), (900, 200), side(R["safety_audit_log"], "l")], "1:N", 0.42)

# Draw boxes last so lines never cover labels.
for name, rect in R.items():
    box(name, rect, fills.get(name, GRAY))

img.save(OUT)
print(OUT)
