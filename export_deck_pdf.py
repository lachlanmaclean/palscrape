#!/usr/bin/env python3
"""
Export a Palworld TCG starter deck (per deck_manifest.json) as a print-ready
proxy PDF, matching the layout conventions used by the michi project's
pdfExport.ts:

  - Standard TCG card size: 2.5in x 3.5in (180 x 252 pt)
  - Letter page (612 x 792 pt), 3x3 grid of true-size cards, centered
  - Black crop marks (L-shaped ticks) at each card corner
  - Green (#22c55e) card-edge outline, square corners
  - fitMode "fill": card art is stretched to exactly fill its card box
    (matches michi's handling of pre-framed card art)

Usage:
    python export_deck_pdf.py ETD01
    python export_deck_pdf.py ETD02
"""

import json
import os
import sys

from PIL import Image
from reportlab.lib.colors import HexColor, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

PT_PER_INCH = 72.0
CARD_WIDTH_PT = 2.5 * PT_PER_INCH   # 180
CARD_HEIGHT_PT = 3.5 * PT_PER_INCH  # 252
PAGE_WIDTH_PT = 612.0   # Letter
PAGE_HEIGHT_PT = 792.0  # Letter

PRINT_COLS = 3
PRINT_ROWS = 3

CROP_MARK_COLOR = black
CARD_EDGE_COLOR = HexColor("#22c55e")
CROP_MARK_LENGTH = 6
CROP_MARK_OFFSET = 2
CROP_MARK_THICKNESS = 1.25
CARD_EDGE_THICKNESS = 1

GRID_WIDTH_PT = PRINT_COLS * CARD_WIDTH_PT
GRID_HEIGHT_PT = PRINT_ROWS * CARD_HEIGHT_PT
MARGIN_LEFT = (PAGE_WIDTH_PT - GRID_WIDTH_PT) / 2
MARGIN_TOP = (PAGE_HEIGHT_PT - GRID_HEIGHT_PT) / 2


def cut_rect_for(row, col):
    """Bottom-left corner (in PDF coords, origin bottom-left) of the card at grid row/col."""
    cut_x = MARGIN_LEFT + col * CARD_WIDTH_PT
    cut_y = PAGE_HEIGHT_PT - MARGIN_TOP - row * CARD_HEIGHT_PT - CARD_HEIGHT_PT
    return cut_x, cut_y


def draw_crop_marks(c, row, col):
    cut_x, cut_y = cut_rect_for(row, col)
    corners = [
        (cut_x, cut_y, -1, -1),                                   # bottom-left
        (cut_x + CARD_WIDTH_PT, cut_y, 1, -1),                    # bottom-right
        (cut_x, cut_y + CARD_HEIGHT_PT, -1, 1),                   # top-left
        (cut_x + CARD_WIDTH_PT, cut_y + CARD_HEIGHT_PT, 1, 1),    # top-right
    ]
    c.setStrokeColor(CROP_MARK_COLOR)
    c.setLineWidth(CROP_MARK_THICKNESS)
    for cx, cy, dx, dy in corners:
        # horizontal tick
        c.line(cx + dx * CROP_MARK_OFFSET, cy,
               cx + dx * (CROP_MARK_OFFSET + CROP_MARK_LENGTH), cy)
        # vertical tick
        c.line(cx, cy + dy * CROP_MARK_OFFSET,
               cx, cy + dy * (CROP_MARK_OFFSET + CROP_MARK_LENGTH))


def draw_card_edge(c, row, col):
    cut_x, cut_y = cut_rect_for(row, col)
    c.setStrokeColor(CARD_EDGE_COLOR)
    c.setLineWidth(CARD_EDGE_THICKNESS)
    c.rect(cut_x, cut_y, CARD_WIDTH_PT, CARD_HEIGHT_PT, stroke=1, fill=0)


def load_card_image(image_path):
    """Some cards (Structure type) are printed landscape on the physical
    sheet. Rotate those 90deg so the art reads right-way-up once the
    portrait card box is cut out and turned sideways to read, matching how
    the physical card is actually printed/played."""
    im = Image.open(image_path)
    if im.width > im.height:
        im = im.rotate(-90, expand=True)
    return ImageReader(im)


def draw_card(c, row, col, image_path):
    cut_x, cut_y = cut_rect_for(row, col)
    img = load_card_image(image_path)
    # fitMode "fill": stretch to exactly the card box, matching michi's
    # handling of pre-framed card art (no cropping/letterboxing).
    c.drawImage(img, cut_x, cut_y, width=CARD_WIDTH_PT, height=CARD_HEIGHT_PT,
                preserveAspectRatio=False, mask='auto')
    draw_crop_marks(c, row, col)
    draw_card_edge(c, row, col)


def build_card_sequence(manifest_path, image_dir):
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    sequence = []
    for entry in manifest["main_deck"] + manifest["soul_deck"]:
        image_path = os.path.join(image_dir, f"{entry['card_number']}.png")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Missing card image: {image_path}")
        sequence.extend([image_path] * entry["count"])
    return sequence, manifest


def export_deck_pdf(expansion_dir, expansion_code):
    manifest_path = os.path.join(expansion_dir, "deck_manifest.json")
    sequence, manifest = build_card_sequence(manifest_path, expansion_dir)

    out_path = os.path.join(expansion_dir, f"{expansion_code}_proxy_deck.pdf")
    c = canvas.Canvas(out_path, pagesize=(PAGE_WIDTH_PT, PAGE_HEIGHT_PT))

    per_page = PRINT_COLS * PRINT_ROWS
    for i, image_path in enumerate(sequence):
        pos_in_page = i % per_page
        row = pos_in_page // PRINT_COLS
        col = pos_in_page % PRINT_COLS
        draw_card(c, row, col, image_path)
        if pos_in_page == per_page - 1:
            c.showPage()
    c.showPage()
    c.save()

    print(f"{expansion_code}: {len(sequence)} cards -> {out_path}")
    return out_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python export_deck_pdf.py <EXPANSION_CODE> [<EXPANSION_CODE> ...]")
        sys.exit(1)

    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "card_images")
    for expansion_code in sys.argv[1:]:
        expansion_dir = os.path.join(base_dir, expansion_code)
        export_deck_pdf(expansion_dir, expansion_code)


if __name__ == "__main__":
    main()
