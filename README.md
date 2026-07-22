# Palworld TCG Proxy Printer

A browser-based tool for browsing scraped Palworld OFFICIAL CARD GAME card
art and exporting print-ready proxy PDFs — pick individual cards and
quantities, or download a ready-made starter deck (ETD01/ETD02) in one
click. PDFs are generated entirely client-side with `pdf-lib`, at true
card size (2.5in x 3.5in) with crop marks and a green cut-line, ready to
print on Letter paper and cut out.

## Development

```
npm install
npm run dev
```

## Build

```
npm run build
```

Static output goes to `dist/`, including the bundled card images from
`public/card_images/`.

## Deployment

Pushes to `main` deploy automatically to GitHub Pages via
`.github/workflows/deploy.yml`. The site is served from a project path
(`https://<user>.github.io/palscrape/`), so `vite.config.ts` sets
`base: '/palscrape/'` — update that if the repo is ever renamed.

To enable Pages for this repo (one-time): **Settings → Pages → Build and
deployment → Source: GitHub Actions**.

## Other tools in this repo

- `scrape_cards.py` — scrapes card art per expansion from the official
  card list API into `card_images/<expansion>/`.
- `export_deck_pdf.py` / `export_counters_pdf.py` — Python equivalents of
  the in-browser PDF export, used before the web UI existed. Still handy
  for scripted/batch generation.

## Checking for new cards / updating an expansion

The official card list page (`en.palworld-official-cardgame.com/cardlist`)
renders client-side and paginates its own JSON API at a **hard server-side
cap of 100 items per page**, regardless of the `per_page` value requested.
An expansion with more than 100 entries (e.g. a booster pack with lots of
rarity variants) needs a second page fetch to get the rest — always check
the `total` field in the API response against how many `items` came back,
don't trust `len(items) < per_page` as an end-of-results signal.

`scrape_cards.py`'s pagination loop already accounts for this (it compares
against `total`, not `per_page`), so simply re-running it will pick up any
newly-added cards:

```
python scrape_cards.py EBP01      # or whichever expansion code changed
```

Full refresh workflow after scraping:

1. `python scrape_cards.py <EXP>` — pulls new images into
   `card_images/<EXP>/` and rewrites `card_images/<EXP>/manifest.json`.
2. Copy any newly-added images into `public/card_images/<EXP>/` (the Vite
   static copy the app actually serves) — the upscale step only mirrors
   files that already exist at the destination, it won't create new ones.
3. `python upscale_cards.py` — finds landscape ("Structure"-type) card
   art across the whole `card_images/` tree, 4x-upscales it in place with
   Real-ESRGAN, and mirrors the result into `public/card_images/`. Requires
   `tools/realesrgan/` (run `python tools/setup_upscaler.py` once if
   missing). This rescans *all* expansions each time, so it will also
   silently re-upscale previously-processed images — harmless, just slower
   than necessary; fine to leave as-is unless it becomes a real time cost.
4. Diff `card_images/<EXP>/manifest.json` against
   `src/data/cards.json`'s `<EXP>.cards` array by `cardNumber` /
   `card_number`, and append any missing entries in the app's shape:
   `{ cardNumber, cardName, rare, image: "card_images/<EXP>/<cardNumber>.png", starterDeckCount: 0 }`.

To sanity-check whether an expansion has grown before running any of this,
the fastest check is hitting the API directly:

```
python -c "
import urllib.request, json
url = 'https://en.palworld-official-cardgame.com/manage/card-list-user/list?expansion=EBP01&title=EBP01&page=1&per_page=200&sort=no'
req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://en.palworld-official-cardgame.com/cardlist'})
print(json.loads(urllib.request.urlopen(req, timeout=30).read())['total'])
"
```

Compare that `total` against `len(cards)` for that expansion in
`src/data/cards.json`.
