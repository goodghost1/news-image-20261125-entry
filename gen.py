"""Build the news-image-20261125 front page: The World Today.

Reads stories-20261125.json (48 verified stories for Wednesday
25 November 2026, plus timeline, numbers, regions and a DATE CHECK
list) and draws one 1024x1024 newspaper page with PIL. Every
drawing is an original vector-style pictogram drawn from primitives;
no photographs, no copied artwork. Output is deterministic: same
input bytes give the same entry.png bytes on every run.
"""

import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "stories-20261125.json")
OUT_PATH = os.path.join(HERE, "entry.png")

W = 1024
H = 1024
MARGIN = 24
CW = W - 2 * MARGIN  # 976 content width

PAPER = (247, 243, 234)
PANEL = (255, 253, 246)
INK = (22, 21, 19)
MUTED = (87, 83, 78)
LINE = (214, 208, 194)
RED = (180, 35, 24)
DARKRED = (127, 29, 29)
GREEN = (21, 128, 61)
BLUE = (29, 78, 216)
AMBER = (180, 83, 9)
TINT_BLUE = (219, 234, 254)
TINT_AMBER = (254, 243, 199)
TINT_RED = (254, 226, 226)
TINT_GREEN = (220, 252, 231)
MAP_FILL = (231, 224, 208)
MAP_LINE = (168, 160, 144)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
SANS_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")


def font(bold, size):
    return ImageFont.truetype(SANS_BOLD if bold else SANS, size)


def text_w(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def wrap_lines(draw, text, fnt, width, max_lines):
    """Greedy word wrap; truncates with an ellipsis past max_lines."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_w(draw, trial, fnt) <= width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines:
                break
    if len(lines) < max_lines and current:
        lines.append(current)
    elif len(lines) == max_lines and current:
        last = lines[-1]
        while last and text_w(draw, last + " …", fnt) > width:
            last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
        lines[-1] = last + " …"
    return lines


def one_line(draw, text, fnt, width):
    """Fit text on one line, truncating with an ellipsis if needed."""
    if text_w(draw, text, fnt) <= width:
        return text
    cut = text
    while cut and text_w(draw, cut + " …", fnt) > width:
        cut = cut.rsplit(" ", 1)[0] if " " in cut else cut[:-1]
    return cut + " …"


def badge_color(badge):
    if badge == "CONFIRMED":
        return GREEN
    if badge == "OFFICIAL":
        return BLUE
    return AMBER


def draw_badge(draw, x, y, badge, fnt):
    draw.text((x, y), badge, font=fnt, fill=badge_color(badge))
    return x + text_w(draw, badge, fnt)


# ---------------------------------------------------------------- icons
# Each icon draws inside the box (x, y, s x s) with PIL primitives.

def icon_chart(d, x, y, s, ink, accent):
    d.line([(x + 2, y + s - 4), (x + s - 2, y + s - 4)], fill=ink, width=2)
    d.line([(x + 2, y + s - 4), (x + 2, y + 4)], fill=ink, width=2)
    bars = [0.45, 0.75, 0.55, 0.9]
    bw = s / 6.0
    for i, h in enumerate(bars):
        bx = x + 6 + i * (bw + 2)
        d.rectangle([bx, y + s - 4 - h * (s - 12), bx + bw, y + s - 4],
                    fill=accent)
    pts = [(x + 6, y + s * 0.30), (x + s * 0.38, y + s * 0.55),
           (x + s * 0.62, y + s * 0.35), (x + s - 6, y + s * 0.62)]
    d.line(pts, fill=RED, width=3)


def icon_refinery(d, x, y, s, ink, accent):
    d.rectangle([x + s * 0.14, y + s * 0.42, x + s * 0.38, y + s - 4],
                fill=ink)
    d.rectangle([x + s * 0.48, y + s * 0.24, x + s * 0.72, y + s - 4],
                fill=accent)
    d.polygon([(x + s * 0.56, y + s * 0.24), (x + s * 0.64, y + 2),
               (x + s * 0.72, y + s * 0.24)], fill=RED)
    d.ellipse([x + s * 0.78, y + s * 0.30, x + s * 0.92, y + s * 0.44],
              fill=MUTED)
    d.ellipse([x + s * 0.82, y + s * 0.16, x + s * 0.94, y + s * 0.28],
              fill=MUTED)


def icon_rocket(d, x, y, s, ink, accent):
    body = [(x + s * 0.42, y + s * 0.06), (x + s * 0.58, y + s * 0.06),
            (x + s * 0.62, y + s * 0.55), (x + s * 0.38, y + s * 0.55)]
    d.polygon(body, fill=ink)
    d.ellipse([x + s * 0.42, y + s * 0.20, x + s * 0.58, y + s * 0.36],
              fill=TINT_BLUE, outline=PANEL)
    d.polygon([(x + s * 0.38, y + s * 0.48), (x + s * 0.22, y + s * 0.72),
               (x + s * 0.38, y + s * 0.62)], fill=accent)
    d.polygon([(x + s * 0.62, y + s * 0.48), (x + s * 0.78, y + s * 0.72),
               (x + s * 0.62, y + s * 0.62)], fill=accent)
    d.polygon([(x + s * 0.44, y + s * 0.55), (x + s * 0.56, y + s * 0.55),
               (x + s * 0.50, y + s * 0.86)], fill=RED)


def icon_scale(d, x, y, s, ink, accent):
    d.line([(x + s / 2, y + 4), (x + s / 2, y + s - 6)], fill=ink, width=2)
    d.line([(x + 4, y + s * 0.30), (x + s - 4, y + s * 0.30)], fill=ink,
           width=2)
    for cx in (x + s * 0.18, x + s * 0.82):
        d.line([(cx, y + s * 0.30), (cx, y + s * 0.52)], fill=ink, width=1)
        d.arc([cx - s * 0.16, y + s * 0.42, cx + s * 0.16, y + s * 0.74],
              0, 180, fill=accent, width=2)
    d.line([(x + s * 0.30, y + s - 6), (x + s * 0.70, y + s - 6)], fill=ink,
           width=2)


def icon_flag(d, x, y, s, ink, accent):
    d.line([(x + s * 0.22, y + 4), (x + s * 0.22, y + s - 4)], fill=ink,
           width=2)
    d.polygon([(x + s * 0.22, y + 6), (x + s * 0.88, y + s * 0.18),
               (x + s * 0.72, y + s * 0.38), (x + s * 0.88, y + s * 0.52),
               (x + s * 0.22, y + s * 0.52)], fill=accent)


def icon_helmet(d, x, y, s, ink, accent):
    d.pieslice([x + 4, y + s * 0.18, x + s - 4, y + s * 0.82], 180, 360,
               fill=accent)
    d.rectangle([x + 2, y + s * 0.52, x + s - 2, y + s * 0.62], fill=ink)
    d.ellipse([x + s * 0.42, y + s * 0.26, x + s * 0.58, y + s * 0.42],
              fill=PANEL)


def icon_shield(d, x, y, s, ink, accent):
    pts = [(x + s / 2, y + 2), (x + s - 4, y + s * 0.18),
           (x + s - 4, y + s * 0.55), (x + s / 2, y + s - 2),
           (x + 4, y + s * 0.55), (x + 4, y + s * 0.18)]
    d.polygon(pts, fill=accent)
    d.line([(x + s * 0.30, y + s * 0.48), (x + s * 0.45, y + s * 0.66),
            (x + s * 0.74, y + s * 0.32)], fill=PANEL, width=3)


def icon_ball(d, x, y, s, ink, accent):
    d.ellipse([x + 2, y + 2, x + s - 2, y + s - 2], outline=ink, width=2)
    cx, cy, r = x + s / 2, y + s / 2, s * 0.16
    pts = []
    for i in range(5):
        a = math.pi / 2 + i * 2 * math.pi / 5
        pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    d.polygon(pts, fill=accent)
    for a in (math.pi / 2, math.pi / 2 + 2 * math.pi / 5,
              math.pi / 2 + 4 * math.pi / 5):
        d.line([(cx + r * math.cos(a), cy - r * math.sin(a)),
                (cx + (s / 2 - 2) * math.cos(a),
                 cy - (s / 2 - 2) * math.sin(a))], fill=ink, width=1)


def icon_chess(d, x, y, s, ink, accent):
    cell = s / 4.0
    for r in range(4):
        for c in range(4):
            if (r + c) % 2 == 0:
                d.rectangle([x + c * cell, y + r * cell,
                             x + (c + 1) * cell, y + (r + 1) * cell],
                            fill=ink)
    d.ellipse([x + s * 0.58, y + s * 0.06, x + s * 0.92, y + s * 0.40],
              fill=accent, outline=PANEL)


def icon_building(d, x, y, s, ink, accent):
    d.polygon([(x + 2, y + s * 0.26), (x + s / 2, y + 2),
               (x + s - 2, y + s * 0.26)], fill=accent)
    d.rectangle([x + 4, y + s * 0.28, x + s - 4, y + s - 4], fill=ink)
    for i in range(3):
        cx = x + s * (0.25 + 0.25 * i)
        d.rectangle([cx - 2, y + s * 0.36, cx + 2, y + s - 10], fill=PANEL)
    d.rectangle([x + 2, y + s - 10, x + s - 2, y + s - 4], fill=accent)


def icon_gavel(d, x, y, s, ink, accent):
    d.line([(x + s * 0.24, y + s * 0.78), (x + s * 0.78, y + s * 0.24)],
           fill=ink, width=4)
    d.rectangle([x + s * 0.52, y + s * 0.06, x + s * 0.94, y + s * 0.30],
                fill=accent)
    d.rectangle([x + s * 0.46, y + s * 0.12, x + s * 0.58, y + s * 0.36],
                fill=ink)


def icon_bolt(d, x, y, s, ink, accent):
    pts = [(x + s * 0.58, y + 2), (x + s * 0.28, y + s * 0.55),
           (x + s * 0.48, y + s * 0.55), (x + s * 0.40, y + s - 2),
           (x + s * 0.74, y + s * 0.42), (x + s * 0.54, y + s * 0.42)]
    d.polygon(pts, fill=accent)


def icon_coin(d, x, y, s, ink, accent):
    d.ellipse([x + 2, y + 2, x + s - 2, y + s - 2], fill=accent,
              outline=ink, width=2)
    f = font(True, max(10, int(s * 0.52)))
    d.text((x + s / 2, y + s / 2), "$", font=f, fill=PANEL, anchor="mm")


def icon_ship(d, x, y, s, ink, accent):
    d.rectangle([x + s * 0.30, y + s * 0.22, x + s * 0.48, y + s * 0.52],
                fill=accent)
    d.rectangle([x + s * 0.52, y + s * 0.30, x + s * 0.68, y + s * 0.52],
                fill=ink)
    d.polygon([(x + 2, y + s * 0.52), (x + s - 2, y + s * 0.52),
               (x + s * 0.82, y + s * 0.74), (x + s * 0.18, y + s * 0.74)],
              fill=ink)
    d.line([(x + 4, y + s * 0.86), (x + s * 0.45, y + s * 0.86)], fill=BLUE,
           width=2)
    d.line([(x + s * 0.55, y + s * 0.86), (x + s - 4, y + s * 0.86)],
           fill=BLUE, width=2)


def icon_star(d, x, y, s, ink, accent):
    cx, cy = x + s / 2, y + s / 2
    outer, inner = s / 2 - 2, s * 0.22
    pts = []
    for i in range(10):
        r = outer if i % 2 == 0 else inner
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=accent)


def icon_cross(d, x, y, s, ink, accent):
    d.rounded_rectangle([x + 2, y + 2, x + s - 2, y + s - 2], radius=4,
                        fill=accent)
    d.rectangle([x + s * 0.42, y + s * 0.20, x + s * 0.58, y + s * 0.80],
                fill=PANEL)
    d.rectangle([x + s * 0.20, y + s * 0.42, x + s * 0.80, y + s * 0.58],
                fill=PANEL)


def icon_flame(d, x, y, s, ink, accent):
    pts = [(x + s / 2, y + 2), (x + s * 0.78, y + s * 0.45),
           (x + s * 0.62, y + s * 0.45), (x + s * 0.72, y + s * 0.68),
           (x + s * 0.28, y + s * 0.68), (x + s * 0.38, y + s * 0.45),
           (x + s * 0.22, y + s * 0.45)]
    d.polygon(pts, fill=accent)
    d.rectangle([x + s * 0.24, y + s * 0.72, x + s * 0.76, y + s * 0.82],
                fill=ink)


ICONS = {
    "chart": icon_chart, "refinery": icon_refinery, "rocket": icon_rocket,
    "scale": icon_scale, "flag": icon_flag, "helmet": icon_helmet,
    "shield": icon_shield, "ball": icon_ball, "chess": icon_chess,
    "building": icon_building, "gavel": icon_gavel, "bolt": icon_bolt,
    "coin": icon_coin, "ship": icon_ship, "star": icon_star,
    "cross": icon_cross, "flame": icon_flame,
}


def draw_icon(d, name, x, y, s, ink=INK, accent=RED):
    fn = ICONS.get(name, icon_star)
    fn(d, x, y, s, ink, accent)


# ---------------------------------------------------------------- sections

def draw_masthead(d, y):
    title = "THE WORLD TODAY"
    date = "WEDNESDAY 25 NOVEMBER 2026"
    f_title = font(True, 36)
    f_date = font(True, 44)
    tw = text_w(d, title, f_title)
    d.text(((W - tw) / 2, y), title, font=f_title, fill=INK)
    y += 46
    dw = text_w(d, date, f_date)
    d.text(((W - dw) / 2, y), date, font=f_date, fill=INK)
    y += 56
    d.line([(MARGIN, y), (W - MARGIN, y)], fill=INK, width=2)
    return y + 4


def draw_band(d, y):
    d.rectangle([MARGIN, y, W - MARGIN, y + 30], fill=RED)
    f = font(True, 20)
    text = "48 STORIES  ·  EVERY ONE DATED WEDNESDAY 25 NOVEMBER 2026"
    tw = text_w(d, text, f)
    d.text(((W - tw) / 2, y + 5), text, font=f, fill=PANEL)
    return y + 30


def draw_subhead(d, y):
    f = font(False, 19)
    text = ("Asian chips rout: Kospi -6.2%, Nikkei -2.8%, a day after the "
            "surge — Houthis strike Saudi refinery — Shenzhou-24 carries "
            "the first foreign astronaut to Tiangong.")
    lines = wrap_lines(d, text, f, CW, 2)
    for line in lines:
        d.text((MARGIN, y), line, font=f, fill=INK)
        y += 22
    return y + 2


def draw_heroes(d, y, heroes):
    col_w = (CW - 16) // 3
    f_head = font(True, 20)
    f_sum = font(False, 14)
    f_out = font(True, 12)
    tints = [TINT_BLUE, TINT_AMBER, TINT_RED]
    for i, hero in enumerate(heroes):
        x = MARGIN + i * (col_w + 8)
        d.rectangle([x, y, x + col_w, y + 92], fill=tints[i],
                    outline=LINE)
        draw_icon(d, hero["icon"], x + col_w // 2 - 44, y + 6, 88,
                  ink=INK, accent=RED)
        ty = y + 98
        for line in wrap_lines(d, hero["headline"], f_head, col_w, 2):
            d.text((x, ty), line, font=f_head, fill=INK)
            ty += 24
        for line in wrap_lines(d, hero["summary"], f_sum, col_w, 2):
            d.text((x, ty), line, font=f_sum, fill=MUTED)
            ty += 18
        d.text((x, ty + 2), hero["outlet"], font=f_out, fill=INK)
        bx = x + text_w(d, hero["outlet"], f_out) + 8
        draw_badge(d, bx, ty + 2, hero["badge"], f_out)
    return y + 200


def draw_timeline(d, y, timeline):
    f_h = font(True, 14)
    d.text((MARGIN, y), "THE DAY IN UTC", font=f_h, fill=INK)
    y += 20
    slot = (CW - 12) // 7
    f_t = font(True, 13)
    f_l = font(False, 11)
    for i, item in enumerate(timeline):
        x = MARGIN + i * (slot + 2)
        d.text((x, y), item["utc"], font=f_t, fill=RED)
        ly = y + 16
        for line in wrap_lines(d, item["label"], f_l, slot, 3):
            d.text((x, ly), line, font=f_l, fill=INK)
            ly += 13
    return y + 36


def draw_numbered(d, y, numbered):
    col_w = (CW - 16) // 2
    f_n = font(True, 17)
    f_h = font(True, 15)
    f_s = font(False, 12)
    f_o = font(True, 11)
    row_h = 36
    for idx, story in enumerate(numbered):
        col = idx // 5
        row = idx % 5
        x = MARGIN + col * (col_w + 16)
        ry = y + row * row_h
        d.text((x, ry + 8), "%d." % (idx + 1), font=f_n, fill=RED)
        ix = x + 26
        d.rectangle([ix, ry + 2, ix + 34, ry + 36], fill=PANEL,
                    outline=LINE)
        draw_icon(d, story["icon"], ix + 3, ry + 5, 28, ink=INK,
                  accent=RED)
        tx = ix + 42
        tw = col_w - 26 - 42 - 6
        out = story["outlet"]
        badge = story["badge"]
        tail_w = (text_w(d, out, f_o) + 6 + text_w(d, badge, f_o) + 4)
        head = one_line(d, story["headline"], f_h, tw - tail_w)
        d.text((tx, ry + 2), head, font=f_h, fill=INK)
        hx = tx + text_w(d, head, f_h) + 6
        d.text((hx, ry + 3), out, font=f_o, fill=MUTED)
        draw_badge(d, hx + text_w(d, out, f_o) + 6, ry + 3, badge, f_o)
        summ = one_line(d, story["summary"], f_s, tw)
        d.text((tx, ry + 20), summ, font=f_s, fill=MUTED)
    return y + 181


def draw_map_numbers(d, y, regions, numbers):
    f_h = font(True, 14)
    map_w = 336
    d.text((MARGIN, y), "WHERE IT HAPPENED", font=f_h, fill=INK)
    d.text((MARGIN + map_w + 16, y), "THE DAY IN NUMBERS", font=f_h,
           fill=INK)
    my = y + 20
    mh = 76
    d.rectangle([MARGIN, my, MARGIN + map_w, my + mh], fill=PANEL,
                outline=LINE)
    continents = [
        [(16, 8), (70, 5), (90, 15), (82, 33), (54, 40), (26, 31),
         (12, 18)],
        [(76, 43), (96, 41), (104, 53), (90, 71), (78, 61)],
        [(148, 7), (172, 5), (180, 13), (168, 23), (150, 20)],
        [(152, 28), (180, 26), (188, 43), (174, 63), (156, 53),
         (146, 38)],
        [(184, 5), (268, 3), (288, 13), (276, 31), (238, 38), (202, 31),
         (186, 18)],
        [(264, 50), (288, 48), (294, 56), (280, 63), (264, 60)],
    ]
    for poly in continents:
        pts = [(MARGIN + px, my + py) for px, py in poly]
        d.polygon(pts, fill=MAP_FILL, outline=MAP_LINE)
    dots = [(272, 17), (262, 15), (205, 35), (186, 30), (288, 58),
            (228, 28), (152, 10), (148, 17), (66, 53), (162, 15),
            (246, 47), (258, 13)]
    for dx, dy in dots:
        d.ellipse([MARGIN + dx - 3, my + dy - 3, MARGIN + dx + 3,
                   my + dy + 3], fill=RED)
    nx = MARGIN + map_w + 16
    nw = W - MARGIN - nx
    cell_w = nw // 5
    f_v = font(True, 23)
    f_l = font(False, 10)
    for i, item in enumerate(numbers):
        cx = nx + (i % 5) * cell_w
        cy = my + (i // 5) * 38
        d.text((cx, cy), item["value"], font=f_v, fill=INK)
        d.text((cx, cy + 26), item["label"], font=f_l, fill=MUTED)
    return y + 96


def draw_also(d, y, also):
    f_h = font(True, 14)
    d.text((MARGIN, y), "ALSO TODAY", font=f_h, fill=INK)
    y += 18
    col_w = (CW - 16) // 3
    f_t = font(False, 12)
    f_o = font(True, 11)
    for i, story in enumerate(also):
        col = i // 12
        row = i % 12
        x = MARGIN + col * (col_w + 8)
        ry = y + row * 13
        bullet = "• "
        head = one_line(d, story["headline"], f_t, col_w - 110)
        d.text((x, ry), bullet + head, font=f_t, fill=INK)
        ox = x + text_w(d, bullet + head, f_t) + 4
        out = one_line(d, story["outlet"], f_o, col_w - (ox - x) - 2)
        d.text((ox, ry), out, font=f_o, fill=MUTED)
    return y + 12 * 13


def draw_date_check(d, y, date_check):
    f_h = font(True, 14)
    d.text((MARGIN, y), "DATE CHECK — NOT TODAY", font=f_h, fill=DARKRED)
    y += 18
    col_w = (CW - 16) // 2
    f_t = font(False, 12)
    for i, item in enumerate(date_check):
        col = i // 5
        row = i % 5
        x = MARGIN + col * (col_w + 16)
        ry = y + row * 13
        text = "• %s — %s" % (item["item"], item["day"])
        d.text((x, ry), one_line(d, text, f_t, col_w), font=f_t,
               fill=MUTED)
    return y + 5 * 13


def draw_footer(d, y, anchor_round):
    f = font(False, 11)
    text = ("HOW SURE: CONFIRMED = outlet confirms · OFFICIAL = official "
            "source · REPORTED = single-source. Drawn illustrations, not "
            "photos. Anchor: drand-quicknet round %d." % anchor_round)
    tw = text_w(d, text, f)
    d.text(((W - tw) / 2, y), text, font=f, fill=MUTED)
    return y + 14


# ---------------------------------------------------------------- build

def main():
    with open(DATA_PATH, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    assert len(data["heroes"]) == 3, "need 3 heroes"
    assert len(data["numbered"]) == 10, "need 10 numbered stories"
    assert len(data["also"]) == 35, "need 35 ALSO stories"
    assert len(data["date_check"]) == 10, "need 10 DATE CHECK items"
    assert len(data["timeline"]) == 7, "need 7 timeline slots"
    assert len(data["numbers"]) == 10, "need 10 numbers"
    total_regions = sum(data["regions"].values())
    assert total_regions == 48, "region counts must sum to 48"
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    y = MARGIN
    y = draw_masthead(d, y)
    y = draw_band(d, y)
    y = draw_subhead(d, y)
    y = draw_heroes(d, y, data["heroes"])
    y = draw_timeline(d, y, data["timeline"])
    y = draw_numbered(d, y, data["numbered"])
    y = draw_map_numbers(d, y, data["regions"], data["numbers"])
    y = draw_also(d, y, data["also"])
    y = draw_date_check(d, y, data["date_check"])
    y = draw_footer(d, y, data["anchor"]["round"])
    if y > 1016:
        raise SystemExit("layout overflow: bottom y=%d" % y)
    img.save(OUT_PATH, format="PNG")
    size = os.path.getsize(OUT_PATH)
    print("entry.png: %d bytes, bottom y=%d" % (size, y))
    if size > 1048576:
        raise SystemExit("entry.png over the 1 MiB limit")


if __name__ == "__main__":
    main()
