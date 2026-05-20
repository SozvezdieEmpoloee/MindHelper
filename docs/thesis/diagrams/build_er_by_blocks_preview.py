from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).with_name("11_er_entities_by_blocks_preview.png")

W, H = 1920, 1080
BG = "#FFFFFF"
INK = "#0F172A"
LINE = "#334155"
BLUE = "#EAF3FF"
GREEN = "#EAFBF1"
ORANGE = "#FFF4E6"
PURPLE = "#F3ECFF"
GRAY = "#F8FAFC"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    if Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


TITLE = font(34, True)
BOX_FONT = font(16)
LABEL_FONT = font(13, True)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def center(text: str, rect: tuple[int, int, int, int]) -> None:
    bb = d.textbbox((0, 0), text, font=BOX_FONT)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x1, y1, x2, y2 = rect
    d.text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - th) / 2 - 1), text, fill=INK, font=BOX_FONT)


def box(name: str, rect: tuple[int, int, int, int], fill: str) -> None:
    d.rounded_rectangle(rect, radius=11, fill=fill, outline=LINE, width=2)
    center(name, rect)


def p(rect: tuple[int, int, int, int], side: str) -> tuple[int, int]:
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


def label(text: str, x: int, y: int) -> None:
    bb = d.textbbox((0, 0), text, font=LABEL_FONT)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.rounded_rectangle((x - 5, y - 13, x + tw + 5, y + th - 8), radius=4, fill=BG, outline="#E2E8F0")
    d.text((x, y - 13), text, fill=LINE, font=LABEL_FONT)


def one_marker(x: int, y: int, side: str) -> None:
    if side in {"l", "r"}:
        off = -7 if side == "l" else 7
        d.line((x + off, y - 10, x + off, y + 10), fill=LINE, width=2)
    else:
        off = -7 if side == "t" else 7
        d.line((x - 10, y + off, x + 10, y + off), fill=LINE, width=2)


def many_marker(x: int, y: int, side: str) -> None:
    if side == "l":
        end = (x - 13, y)
        d.line((end[0], end[1], x, y - 8), fill=LINE, width=2)
        d.line((end[0], end[1], x, y), fill=LINE, width=2)
        d.line((end[0], end[1], x, y + 8), fill=LINE, width=2)
    elif side == "r":
        end = (x + 13, y)
        d.line((end[0], end[1], x, y - 8), fill=LINE, width=2)
        d.line((end[0], end[1], x, y), fill=LINE, width=2)
        d.line((end[0], end[1], x, y + 8), fill=LINE, width=2)
    elif side == "t":
        end = (x, y - 13)
        d.line((end[0], end[1], x - 8, y), fill=LINE, width=2)
        d.line((end[0], end[1], x, y), fill=LINE, width=2)
        d.line((end[0], end[1], x + 8, y), fill=LINE, width=2)
    elif side == "b":
        end = (x, y + 13)
        d.line((end[0], end[1], x - 8, y), fill=LINE, width=2)
        d.line((end[0], end[1], x, y), fill=LINE, width=2)
        d.line((end[0], end[1], x + 8, y), fill=LINE, width=2)


RELATIONS: list[tuple[str, str, str, str, list[tuple[int, int]], str, tuple[int, int]]] = []


def rel(a_name: str, a_side: str, b_name: str, b_side: str, points: list[tuple[int, int]], card: str, label_xy: tuple[int, int]) -> None:
    RELATIONS.append((a_name, a_side, b_name, b_side, points, card, label_xy))


NODES: dict[str, tuple[tuple[int, int, int, int], str]] = {
    "user_account": ((80, 455, 245, 505), BLUE),
    "user_chat": ((420, 455, 585, 505), BLUE),
    "chat_message": ((750, 455, 940, 505), BLUE),
    "neural_model_version": ((377, 235, 627, 285), PURPLE),
    "channel_account": ((70, 215, 255, 265), BLUE),
    "role": ((80, 730, 190, 780), GRAY),
    "user_role": ((310, 730, 475, 780), GRAY),
    "assessment_template": ((720, 145, 960, 195), GREEN),
    "assessment_question": ((1050, 145, 1290, 195), GREEN),
    "assessment_session": ((720, 275, 945, 325), GREEN),
    "assessment_answer": ((1050, 275, 1275, 325), GREEN),
    "emergency_resource": ((1178, 390, 1408, 440), GRAY),
    "crisis_event": ((1210, 500, 1375, 550), ORANGE),
    "safety_audit_log": ((1210, 620, 1400, 670), ORANGE),
    "specialist": ((650, 805, 810, 855), GRAY),
    "specialist_location": ((905, 805, 1140, 855), GRAY),
    "appointment": ((1240, 805, 1405, 855), GRAY),
    "moderation_case": ((1560, 455, 1760, 505), PURPLE),
    "site_content": ((1560, 620, 1750, 670), PURPLE),
}

d.text((60, 28), "ER-model MindHelper: entities and relationships", fill=INK, font=TITLE)
d.line((60, 78, 760, 78), fill="#22B8D6", width=5)

# User and access.
rel("user_account", "t", "channel_account", "b", [], "1:N", (176, 350))
rel("user_account", "b", "user_role", "t", [(162, 685), (392, 685)], "1:N", (260, 685))
rel("role", "r", "user_role", "l", [], "1:N", (245, 755))

# Core chat.
rel("user_account", "r", "user_chat", "l", [], "1:1", (315, 480))
rel("user_chat", "r", "chat_message", "l", [], "1:N", (650, 480))
rel("neural_model_version", "b", "user_chat", "t", [], "1:N", (520, 365))

# Assessments.
rel("assessment_template", "r", "assessment_question", "l", [], "1:N", (985, 170))
rel("assessment_template", "b", "assessment_session", "t", [], "1:N", (830, 235))
rel("assessment_question", "b", "assessment_answer", "t", [], "1:N", (1165, 235))
rel("assessment_session", "r", "assessment_answer", "l", [], "1:N", (985, 300))
rel("user_account", "r", "assessment_session", "l", [(330, 480), (330, 300)], "1:N", (355, 300))
rel("user_chat", "r", "assessment_session", "l", [(665, 480), (665, 365), (695, 365), (695, 300)], "1:N", (650, 365))

# Safety.
rel("user_chat", "r", "crisis_event", "l", [(650, 480), (650, 525)], "1:N", (690, 525))
rel("chat_message", "r", "crisis_event", "l", [(1030, 480), (1030, 525)], "1:N", (1040, 525))
rel("emergency_resource", "b", "crisis_event", "t", [], "1:N", (1300, 470))
rel("crisis_event", "b", "safety_audit_log", "t", [], "1:N", (1300, 585))
rel("chat_message", "b", "safety_audit_log", "l", [(845, 645), (1185, 645)], "1:N", (1000, 645))
rel("user_chat", "b", "safety_audit_log", "l", [(502, 705), (1185, 705), (1185, 645)], "1:N", (760, 705))
rel("neural_model_version", "r", "safety_audit_log", "t", [(1450, 260), (1450, 610), (1305, 610)], "1:N", (1455, 440))

# Directory.
rel("user_account", "l", "appointment", "l", [(35, 480), (35, 970), (1215, 970), (1215, 830)], "1:N", (620, 970))
rel("specialist", "r", "specialist_location", "l", [], "1:N", (850, 830))
rel("specialist_location", "r", "appointment", "l", [], "1:N", (1180, 830))
rel("specialist", "r", "appointment", "l", [(850, 755), (1215, 755), (1215, 830)], "1:N", (1000, 755))

# Administration.
rel("user_account", "r", "moderation_case", "l", [(1475, 480)], "1:N", (1475, 480))
rel("user_chat", "r", "moderation_case", "l", [(1475, 480)], "1:N", (1060, 480))
rel("chat_message", "r", "moderation_case", "l", [], "1:N", (1240, 480))
rel("user_account", "b", "site_content", "l", [(162, 915), (1480, 915), (1480, 645)], "1:N", (760, 915))

for left, left_side, right, right_side, pts, card, label_xy in RELATIONS:
    d.line([p(NODES[left][0], left_side), *pts, p(NODES[right][0], right_side)], fill=LINE, width=2)

for name, (rect, fill) in NODES.items():
    box(name, rect, fill)

for left, left_side, right, right_side, pts, card, label_xy in RELATIONS:
    left_xy = p(NODES[left][0], left_side)
    right_xy = p(NODES[right][0], right_side)
    left_card, right_card = card.split(":")
    (one_marker if left_card == "1" else many_marker)(*left_xy, left_side)
    (one_marker if right_card == "1" else many_marker)(*right_xy, right_side)
    label(card, *label_xy)

img.save(OUT)
print(OUT)
