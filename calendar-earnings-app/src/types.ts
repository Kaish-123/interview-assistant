export interface CalendarEventRow {
  eventId: string;
  title: string;
  start: string; // ISO
  end: string;
  earnings: number | null;
  manualUpdate: string;
  selectionStatus?: string;
}

export interface KeywordMappingRow {
  keyword: string;
  price: number;
  startEffectiveDate: string | null; // ISO or null = from epoch
}

export interface KeywordEntry {
  price: number;
  effectiveDate: Date;
}

export type KeywordMap = Record<string, KeywordEntry[]>;
