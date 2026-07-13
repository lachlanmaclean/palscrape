#!/usr/bin/env python3
"""
Recreate the Palworld OFFICIAL CARD GAME's physical accessories as a
print-and-cut PDF: the Life Counter dial, the Material & Ingredient
Counter dial, and small round marker chips (as seen in the trial deck
box contents).

These aren't official source files -- they're a close visual replica
built from a reference unboxing photo, sized to print at roughly the
same physical dimensions as the originals (~3.3in x 2.2in per card).

Usage:
    python export_counters_pdf.py
"""

import math
import os

from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas

PT_PER_INCH = 72.0
PAGE_WIDTH_PT = 612.0   # Letter
PAGE_HEIGHT_PT = 792.0

CARD_W = 3.3 * PT_PER_INCH
CARD_H = 2.3 * PT_PER_INCH

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accessories", "counters.pdf")

LIFE_BG = HexColor("#2b2b2b")
LIFE_ACCENT = HexColor("#c9a24b")
MATERIAL_BG = HexColor("#1f4d3d")
MATERIAL_ACCENT = HexColor("#c9a24b")
CIRCLE_FILL = HexColor("#e8dfc0")
CIRCLE_STROKE = HexColor("#8a7b4f")
HIGHLIGHT = HexColor("#c0392b")
TEXT_DARK = HexColor("#2b2b2b")

# Numbers laid out clockwise starting at top (0), matching the reference photo:
# top=0, right column going down 1-5, bottom row 6-10 (right to left), left column going up 11-15.
DIAL_ORDER = [0, 1, 2, 3, 4, 5, 10, 9, 8, 7, 6, 11, 12, 13, 14, 15]


def draw_dial_positions(cx, cy, radius_x, radius_y):
    """16 positions in a rounded-rectangle-ish ring (approximated as an ellipse)."""
    positions = []
    n = len(DIAL_ORDER)
    # Start at top (90deg) and go clockwise.
    start_angle = math.pi / 2
    for i in range(n):
        angle = start_angle - (2 * math.pi * i / n)
        x = cx + radius_x * math.cos(angle)
        y = cy + radius_y * math.sin(angle)
        positions.append((x, y))
    return positions


def draw_counter_card(c, x0, y0, title_lines, bg_color, highlight_index=0):
    # Card background
    c.setFillColor(bg_color)
    c.roundRect(x0, y0, CARD_W, CARD_H, 8, stroke=0, fill=1)

    # Border
    c.setStrokeColor(LIFE_ACCENT)
    c.setLineWidth(1.5)
    c.roundRect(x0 + 3, y0 + 3, CARD_W - 6, CARD_H - 6, 6, stroke=1, fill=0)

    # Title block (top-left, stacked lines)
    text_x = x0 + 14
    text_y = y0 + CARD_H - 20
    c.setFillColor(white)
    c.setFont("Helvetica", 6)
    c.drawString(text_x, text_y + 12, "Palworld OFFICIAL CARD GAME")
    c.setFont("Helvetica-Bold", 11)
    ty = text_y
    for line in title_lines:
        c.drawString(text_x, ty, line)
        ty -= 12

    # Dial ring centered in right-middle area
    cx = x0 + CARD_W * 0.65
    cy = y0 + CARD_H * 0.36
    radius_x = CARD_W * 0.30
    radius_y = CARD_H * 0.34
    positions = draw_dial_positions(cx, cy, radius_x, radius_y)

    circle_r = 10.5
    for i, num in enumerate(DIAL_ORDER):
        px, py = positions[i]
        is_highlight = (num == highlight_index)
        c.setFillColor(HIGHLIGHT if is_highlight else CIRCLE_FILL)
        c.setStrokeColor(CIRCLE_STROKE)
        c.setLineWidth(1)
        c.circle(px, py, circle_r, stroke=1, fill=1)
        c.setFillColor(white if is_highlight else TEXT_DARK)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(px, py - 3, str(num))


def draw_marker_chip(c, cx, cy, r, fill_color, label):
    c.setFillColor(fill_color)
    c.setStrokeColor(black)
    c.setLineWidth(1)
    c.circle(cx, cy, r, stroke=1, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(cx, cy - 3, label)


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    c = canvas.Canvas(OUT_PATH, pagesize=(PAGE_WIDTH_PT, PAGE_HEIGHT_PT))

    margin_x = (PAGE_WIDTH_PT - CARD_W) / 2
    top_y = PAGE_HEIGHT_PT - 100 - CARD_H

    draw_counter_card(c, margin_x, top_y, ["LIFE COUNTER"], LIFE_BG, highlight_index=0)

    bottom_y = top_y - 40 - CARD_H
    draw_counter_card(c, margin_x, bottom_y, ["MATERIAL &", "INGREDIENT COUNTER"], MATERIAL_BG, highlight_index=0)

    # Marker chips row below both cards
    chip_r = 16
    chip_y = bottom_y - 50
    chip_colors = [
        (HexColor("#1a1a1a"), "PAL"),
        (HexColor("#c0522d"), "WOOD"),
        (HexColor("#4a9c3f"), "PASTE"),
    ]
    spacing = 60
    start_x = PAGE_WIDTH_PT / 2 - spacing
    for i, (color, label) in enumerate(chip_colors):
        draw_marker_chip(c, start_x + i * spacing, chip_y, chip_r, color, label)

    c.setFillColor(black)
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(PAGE_WIDTH_PT / 2, chip_y - 35,
                         "Fan-made replica for proxy play -- not official Palworld OFFICIAL CARD GAME components.")

    c.showPage()
    c.save()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
