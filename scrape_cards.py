#!/usr/bin/env python3
"""
Scrape Palworld Official Card Game card art images, organized by expansion.

Uses the site's internal JSON API (the same one the card list page calls)
rather than scraping rendered HTML, since the card list is populated by JS.

Usage:
    python scrape_cards.py                  # scrape all expansions
    python scrape_cards.py ETD01 ETD02       # scrape specific expansions only
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse

BASE = "https://en.palworld-official-cardgame.com"
API_BASE = f"{BASE}/manage"
CARD_IMAGE_BASE = f"{BASE}/wordpress/wp-content/images/cardlist"
PRODUCTS_ENDPOINT = f"{API_BASE}/card-list-user/products"
LIST_ENDPOINT = f"{API_BASE}/card-list-user/list"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "card_images")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": f"{BASE}/cardlist",
}


def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def get_expansion_codes():
    data = json.loads(http_get(PRODUCTS_ENDPOINT))
    codes = []
    for group in data.get("products", []):
        for item in group.get("items", []):
            code = item.get("code")
            if code:
                codes.append(code)
    return codes


def get_cards_for_expansion(expansion, per_page=200):
    all_items = []
    page = 1
    while True:
        params = {
            "expansion": expansion,
            "title": expansion,
            "page": page,
            "per_page": per_page,
            "sort": "no",
        }
        url = f"{LIST_ENDPOINT}?{urllib.parse.urlencode(params)}"
        data = json.loads(http_get(url))
        items = data.get("items", [])
        all_items.extend(items)
        if len(items) < per_page:
            break
        page += 1
    return all_items


def download_card_image(card, dest_dir, delay=0.2):
    picture = card.get("picture")
    if not picture:
        return None
    picture = picture.replace("\\/", "/")
    img_url = f"{CARD_IMAGE_BASE}/{picture}"
    filename = os.path.basename(picture)
    dest_path = os.path.join(dest_dir, filename)

    if os.path.exists(dest_path):
        return dest_path

    try:
        img_data = http_get(img_url)
    except Exception as e:
        print(f"    FAILED: {img_url} ({e})")
        return None

    with open(dest_path, "wb") as f:
        f.write(img_data)

    time.sleep(delay)
    return dest_path


def scrape_expansion(expansion):
    print(f"Fetching card list for {expansion} ...")
    cards = get_cards_for_expansion(expansion)
    print(f"  {len(cards)} cards found")

    dest_dir = os.path.join(OUTPUT_DIR, expansion)
    os.makedirs(dest_dir, exist_ok=True)

    manifest = []
    for card in cards:
        path = download_card_image(card, dest_dir)
        status = "ok" if path else "MISSING"
        print(f"    [{status}] {card.get('card_number')} - {card.get('card_name')}")
        manifest.append({
            "id": card.get("id"),
            "card_number": card.get("card_number"),
            "card_name": card.get("card_name"),
            "rare": card.get("rare"),
            "picture": card.get("picture"),
            "downloaded": bool(path),
        })

    with open(os.path.join(dest_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def main():
    requested = sys.argv[1:]
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if requested:
        expansions = requested
    else:
        print("Fetching expansion list ...")
        expansions = get_expansion_codes()
        print(f"Found expansions: {', '.join(expansions)}")

    for expansion in expansions:
        scrape_expansion(expansion)

    print("Done.")


if __name__ == "__main__":
    main()
