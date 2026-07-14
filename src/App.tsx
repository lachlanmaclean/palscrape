import { useMemo, useState } from 'react';
import cardData from './data/cards.json';
import type { Card, CardDatabase, SelectionEntry } from './types/card';
import { downloadPdfBytes, exportCardsToPdf, type ExportProgress } from './export/pdfExport';
import './App.css';

const DB = cardData as unknown as CardDatabase;
const EXPANSION_CODES = Object.keys(DB);

function cardKey(expansionCode: string, cardNumber: string) {
  return `${expansionCode}::${cardNumber}`;
}

function App() {
  const [activeExpansion, setActiveExpansion] = useState(EXPANSION_CODES[0]);
  const [search, setSearch] = useState('');
  const [selection, setSelection] = useState<Map<string, SelectionEntry>>(new Map());
  const [exporting, setExporting] = useState(false);
  const [progress, setProgress] = useState<ExportProgress | null>(null);

  const expansion = DB[activeExpansion];

  const filteredCards = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return expansion.cards;
    return expansion.cards.filter(
      (c) => c.cardName.toLowerCase().includes(q) || c.cardNumber.toLowerCase().includes(q)
    );
  }, [expansion, search]);

  function setCount(expansionCode: string, card: Card, count: number) {
    setSelection((prev) => {
      const next = new Map(prev);
      const key = cardKey(expansionCode, card.cardNumber);
      if (count <= 0) {
        next.delete(key);
      } else {
        next.set(key, { card, count });
      }
      return next;
    });
  }

  function getCount(expansionCode: string, cardNumber: string) {
    return selection.get(cardKey(expansionCode, cardNumber))?.count ?? 0;
  }

  const selectionList = Array.from(selection.values());
  const totalSelectedCards = selectionList.reduce((sum, e) => sum + e.count, 0);

  async function handleExportSelection() {
    if (selectionList.length === 0) return;
    setExporting(true);
    setProgress({ loaded: 0, total: totalSelectedCards });
    try {
      const bytes = await exportCardsToPdf(selectionList, setProgress);
      downloadPdfBytes(bytes, 'custom_cards.pdf');
    } catch (e) {
      alert(`Export failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setExporting(false);
      setProgress(null);
    }
  }

  async function handleExportStarterDeck(expansionCode: string) {
    const exp = DB[expansionCode];
    const deckSelection: SelectionEntry[] = exp.cards
      .filter((c) => c.starterDeckCount > 0)
      .map((card) => ({ card, count: card.starterDeckCount }));
    if (deckSelection.length === 0) return;

    setExporting(true);
    const total = deckSelection.reduce((sum, e) => sum + e.count, 0);
    setProgress({ loaded: 0, total });
    try {
      const bytes = await exportCardsToPdf(deckSelection, setProgress);
      downloadPdfBytes(bytes, `${expansionCode}_starter_deck.pdf`);
    } catch (e) {
      alert(`Export failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setExporting(false);
      setProgress(null);
    }
  }

  function clearSelection() {
    setSelection(new Map());
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Palworld TCG Proxy Printer</h1>
        <p className="subtitle">Pick cards to reprint, or grab a ready-made starter deck PDF.</p>
      </header>

      <nav className="expansion-tabs">
        {EXPANSION_CODES.map((code) => (
          <button
            key={code}
            className={code === activeExpansion ? 'tab active' : 'tab'}
            onClick={() => setActiveExpansion(code)}
          >
            {code}
          </button>
        ))}
      </nav>

      <div className="expansion-toolbar">
        <h2>{expansion.name}</h2>
        <input
          className="search-input"
          type="text"
          placeholder="Search by name or card number..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {expansion.hasStarterDeck && (
          <button
            className="btn btn-secondary"
            disabled={exporting}
            onClick={() => handleExportStarterDeck(activeExpansion)}
          >
            Download {activeExpansion} Starter Deck PDF
          </button>
        )}
      </div>

      <div className="card-grid">
        {filteredCards.map((card) => {
          const count = getCount(activeExpansion, card.cardNumber);
          return (
            <div className="card-tile" key={card.cardNumber}>
              <img src={`${import.meta.env.BASE_URL}${card.image}`} alt={card.cardName} loading="lazy" />
              <div className="card-tile-info">
                <div className="card-tile-name">{card.cardName}</div>
                <div className="card-tile-meta">
                  {card.cardNumber} · {card.rare}
                </div>
              </div>
              <div className="qty-control">
                <button onClick={() => setCount(activeExpansion, card, Math.max(0, count - 1))}>
                  −
                </button>
                <input
                  type="number"
                  min={0}
                  value={count}
                  onChange={(e) => setCount(activeExpansion, card, Math.max(0, Number(e.target.value) || 0))}
                />
                <button onClick={() => setCount(activeExpansion, card, count + 1)}>+</button>
              </div>
            </div>
          );
        })}
      </div>

      {selectionList.length > 0 && (
        <div className="selection-tray">
          <div className="selection-tray-summary">
            <strong>{totalSelectedCards}</strong> card{totalSelectedCards !== 1 ? 's' : ''} selected
            {exporting && progress && (
              <span className="progress-text">
                {' '}
                — rendering {progress.loaded}/{progress.total}
              </span>
            )}
          </div>
          <div className="selection-tray-actions">
            <button className="btn btn-secondary" onClick={clearSelection} disabled={exporting}>
              Clear
            </button>
            <button className="btn btn-primary" onClick={handleExportSelection} disabled={exporting}>
              {exporting ? 'Generating PDF…' : 'Download Selected as PDF'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
