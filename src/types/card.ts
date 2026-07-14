export interface Card {
  cardNumber: string;
  cardName: string;
  rare: string;
  image: string;
  starterDeckCount: number;
}

export interface Expansion {
  name: string;
  cards: Card[];
  hasStarterDeck: boolean;
}

export type CardDatabase = Record<string, Expansion>;

export interface SelectionEntry {
  card: Card;
  count: number;
}
