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
