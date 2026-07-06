"""
Draws the notes text onto a lined-notebook-style background with the
**highlighted** section rendered as marker-highlighted text — done with PIL
so the words are always rendered correctly (AI image models often garble text).
"""
import os
import re
from PIL import Image, ImageDraw, ImageFont
from config import FONT_DIR, BG_DIR

CANVAS_SIZE = (1080, 1350)
MARGIN = 90
LINE_HEIGHT = 46

HANDWRITING_FONT_CANDIDATES = ["Caveat-Regular.ttf", "PatrickHand-Regular.ttf"]
TITLE_FONT_CANDIDATES = ["PatrickHand-Regular.ttf", "Caveat-Bold.ttf"]

HIGHLIGHT_COLOR = (255, 235, 90, 160)
INK_COLOR = (35, 40, 90)
RULE_LINE_COLOR = (200, 210, 230)
MARGIN_LINE_COLOR = (230, 120, 120)


def _load_font(candidates, size):
    for name in candidates:
        path = os.path.join(FONT_DIR, name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_notebook_background(draw, size):
    w, h = size
    draw.rectangle([0, 0, w, h], fill=(255, 253, 245))
    y = 160
    while y < h - 40:
        draw.line([(MARGIN - 20, y), (w - 40, y)], fill=RULE_LINE_COLOR, width=2)
        y += LINE_HEIGHT
    draw.line([(MARGIN - 45, 40), (MARGIN - 45, h - 40)], fill=MARGIN_LINE_COLOR, width=3)


def _get_background(size):
    bg_path = os.path.join(BG_DIR, "notebook_bg.png")
    if os.path.exists(bg_path):
        return Image.open(bg_path).convert("RGB").resize(size)
    img = Image.new("RGB", size, (255, 253, 245))
    draw = ImageDraw.Draw(img)
    _draw_notebook_background(draw, size)
    return img


def _wrap(text, font, draw, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_notebook_image(topic, notes_markdown, out_path):
    img = _get_background(CANVAS_SIZE).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    title_font = _load_font(TITLE_FONT_CANDIDATES, 62)
    body_font = _load_font(HANDWRITING_FONT_CANDIDATES, 40)

    x, y = MARGIN, 70
    draw.text((x, y), topic, font=title_font, fill=INK_COLOR)
    y += 100
    draw.line([(x, y), (CANVAS_SIZE[0] - MARGIN, y)], fill=INK_COLOR, width=3)
    y += 50

    max_width = CANVAS_SIZE[0] - MARGIN - 60

    segments = re.split(r"(\*\*.*?\*\*)", notes_markdown)
    for seg in segments:
        if not seg.strip():
            continue
        highlighted = seg.startswith("**") and seg.endswith("**")
        clean = seg.strip("*")
        lines = _wrap(clean, body_font, draw, max_width)
        for line in lines:
            if highlighted:
                text_w = draw.textlength(line, font=body_font)
                draw.rectangle(
                    [x - 4, y + 6, x + text_w + 4, y + LINE_HEIGHT - 4],
                    fill=HIGHLIGHT_COLOR,
                )
            draw.text((x, y), line, font=body_font, fill=INK_COLOR)
            y += LINE_HEIGHT

    combined = Image.alpha_composite(img, overlay).convert("RGB")
    combined.save(out_path, "PNG")
    return out_path
