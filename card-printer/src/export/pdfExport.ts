import { PDFDocument, rgb, type PDFImage, type PDFPage } from 'pdf-lib';
import type { SelectionEntry } from '../types/card';

const PT_PER_INCH = 72;
export const CARD_WIDTH_PT = 2.5 * PT_PER_INCH; // 180
export const CARD_HEIGHT_PT = 3.5 * PT_PER_INCH; // 252
const PAGE_WIDTH_PT = 612; // Letter
const PAGE_HEIGHT_PT = 792;

const PRINT_COLS = 3;
const PRINT_ROWS = 3;
const PER_PAGE = PRINT_COLS * PRINT_ROWS;

const CROP_MARK_COLOR = rgb(0, 0, 0);
const CARD_EDGE_COLOR = rgb(0x22 / 255, 0xc5 / 255, 0x5e / 255); // #22c55e
const CROP_MARK_LENGTH = 6;
const CROP_MARK_OFFSET = 2;
const CROP_MARK_THICKNESS = 1.25;
const CARD_EDGE_THICKNESS = 1;

const GRID_WIDTH_PT = PRINT_COLS * CARD_WIDTH_PT;
const GRID_HEIGHT_PT = PRINT_ROWS * CARD_HEIGHT_PT;
const MARGIN_LEFT = (PAGE_WIDTH_PT - GRID_WIDTH_PT) / 2;
const MARGIN_TOP = (PAGE_HEIGHT_PT - GRID_HEIGHT_PT) / 2;

function cutRectFor(row: number, col: number) {
  const cutX = MARGIN_LEFT + col * CARD_WIDTH_PT;
  const cutY = PAGE_HEIGHT_PT - MARGIN_TOP - row * CARD_HEIGHT_PT - CARD_HEIGHT_PT;
  return { cutX, cutY };
}

function drawCropMarks(page: PDFPage, row: number, col: number) {
  const { cutX, cutY } = cutRectFor(row, col);
  const corners = [
    { x: cutX, y: cutY, dx: -1, dy: -1 },
    { x: cutX + CARD_WIDTH_PT, y: cutY, dx: 1, dy: -1 },
    { x: cutX, y: cutY + CARD_HEIGHT_PT, dx: -1, dy: 1 },
    { x: cutX + CARD_WIDTH_PT, y: cutY + CARD_HEIGHT_PT, dx: 1, dy: 1 },
  ];
  for (const { x, y, dx, dy } of corners) {
    page.drawLine({
      start: { x: x + dx * CROP_MARK_OFFSET, y },
      end: { x: x + dx * (CROP_MARK_OFFSET + CROP_MARK_LENGTH), y },
      thickness: CROP_MARK_THICKNESS,
      color: CROP_MARK_COLOR,
    });
    page.drawLine({
      start: { x, y: y + dy * CROP_MARK_OFFSET },
      end: { x, y: y + dy * (CROP_MARK_OFFSET + CROP_MARK_LENGTH) },
      thickness: CROP_MARK_THICKNESS,
      color: CROP_MARK_COLOR,
    });
  }
}

function drawCardEdge(page: PDFPage, row: number, col: number) {
  const { cutX, cutY } = cutRectFor(row, col);
  page.drawRectangle({
    x: cutX,
    y: cutY,
    width: CARD_WIDTH_PT,
    height: CARD_HEIGHT_PT,
    borderColor: CARD_EDGE_COLOR,
    borderWidth: CARD_EDGE_THICKNESS,
  });
}

async function fetchImageBytes(url: string): Promise<Uint8Array> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch image: ${url}`);
  return new Uint8Array(await res.arrayBuffer());
}

/** Detects landscape (Structure-type) card art via an offscreen canvas and,
 * if landscape, returns it rotated 90deg clockwise so it reads correctly
 * once printed in the portrait card box (matches the physical card
 * printing convention for this game's Structure cards). */
async function loadPngBytesUpright(url: string): Promise<Uint8Array> {
  const bytes = await fetchImageBytes(url);
  const blob = new Blob([bytes as BlobPart]);
  const bitmap = await createImageBitmap(blob);

  if (bitmap.width <= bitmap.height) {
    return bytes;
  }

  const canvas = document.createElement('canvas');
  canvas.width = bitmap.height;
  canvas.height = bitmap.width;
  const ctx = canvas.getContext('2d')!;
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.rotate(Math.PI / 2);
  ctx.drawImage(bitmap, -bitmap.width / 2, -bitmap.height / 2);

  const rotatedBlob: Blob = await new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('toBlob failed'))), 'image/png')
  );
  return new Uint8Array(await rotatedBlob.arrayBuffer());
}

export interface ExportProgress {
  loaded: number;
  total: number;
}

/** Expands a selection (card + count) into a flat sequence of image URLs, one per physical copy. */
function buildSequence(selection: SelectionEntry[]): string[] {
  const sequence: string[] = [];
  for (const { card, count } of selection) {
    for (let i = 0; i < count; i++) sequence.push(card.image);
  }
  return sequence;
}

export async function exportCardsToPdf(
  selection: SelectionEntry[],
  onProgress?: (p: ExportProgress) => void
): Promise<Uint8Array> {
  const sequence = buildSequence(selection);
  const pdfDoc = await PDFDocument.create();
  const imageCache = new Map<string, PDFImage>();

  const numPages = Math.max(1, Math.ceil(sequence.length / PER_PAGE));
  const pages: PDFPage[] = [];
  for (let i = 0; i < numPages; i++) {
    pages.push(pdfDoc.addPage([PAGE_WIDTH_PT, PAGE_HEIGHT_PT]));
  }

  for (let i = 0; i < sequence.length; i++) {
    const imageUrl = sequence[i];
    let img = imageCache.get(imageUrl);
    if (!img) {
      const bytes = await loadPngBytesUpright(imageUrl);
      img = await pdfDoc.embedPng(bytes);
      imageCache.set(imageUrl, img);
    }

    const pageIndex = Math.floor(i / PER_PAGE);
    const posInPage = i % PER_PAGE;
    const row = Math.floor(posInPage / PRINT_COLS);
    const col = posInPage % PRINT_COLS;

    const page = pages[pageIndex];
    const { cutX, cutY } = cutRectFor(row, col);
    page.drawImage(img, { x: cutX, y: cutY, width: CARD_WIDTH_PT, height: CARD_HEIGHT_PT });
    drawCropMarks(page, row, col);
    drawCardEdge(page, row, col);

    onProgress?.({ loaded: i + 1, total: sequence.length });
  }

  return pdfDoc.save();
}

export function downloadPdfBytes(bytes: Uint8Array, fileName: string) {
  const blob = new Blob([bytes.slice().buffer as BlobPart], { type: 'application/pdf' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(url);
}
