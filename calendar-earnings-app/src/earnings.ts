import { DEFAULT_PRICE, MANUAL_YES_VALUES, EPOCH_START } from './config';
import { getDateRange } from './settings';
import type { CalendarEventRow, KeywordMappingRow, KeywordMap } from './types';
import { loadKeywordMapping } from './storage';

export function buildKeywordMap(rows: KeywordMappingRow[]): KeywordMap {
  const map: KeywordMap = {};
  for (const row of rows) {
    const kw = (row.keyword || '').trim().toLowerCase();
    if (!kw) continue;
    const price = Number(row.price) || 0;
    let effectiveDate = EPOCH_START;
    if (row.startEffectiveDate) {
      const d = new Date(row.startEffectiveDate);
      if (!isNaN(d.getTime())) effectiveDate = d;
    }
    if (!map[kw]) map[kw] = [];
    map[kw].push({ price, effectiveDate });
  }
  for (const k of Object.keys(map)) {
    map[k].sort((a, b) => a.effectiveDate.getTime() - b.effectiveDate.getTime());
  }
  return map;
}

export function getPriceForEventDate(
  keywordMap: KeywordMap,
  title: string,
  eventDate: Date,
  defaultPrice: number = DEFAULT_PRICE
): number {
  const lowerTitle = (title || '').toLowerCase();
  for (const keyword of Object.keys(keywordMap)) {
    if (!keyword || !lowerTitle.includes(keyword)) continue;
    const entries = keywordMap[keyword];
    let best: { price: number; effectiveDate: Date } | null = null;
    for (let i = 0; i < entries.length; i++) {
      if (entries[i].effectiveDate <= eventDate) best = entries[i];
      else break;
    }
    if (best) return best.price;
  }
  return defaultPrice;
}

function isManualYes(value: string): boolean {
  return MANUAL_YES_VALUES.has((value || '').toString().trim().toLowerCase());
}

function inDateRange(d: Date): boolean {
  const { startDate, endDate } = getDateRange();
  return d >= startDate && d <= endDate;
}

function hasEarnings(row: CalendarEventRow): boolean {
  if (row.earnings !== null && row.earnings !== undefined) return true;
  if (typeof row.earnings === 'number' && !isNaN(row.earnings)) return true;
  return false;
}

export function runEarnings(
  events: CalendarEventRow[],
  keywordMap: KeywordMap,
  incrementalOnly: boolean
): CalendarEventRow[] {
  const result = events.map((row) => {
    const eventDate = new Date(row.start);
    if (!inDateRange(eventDate)) return row;
    if (isManualYes(row.manualUpdate || '')) return row;
    if (incrementalOnly && hasEarnings(row)) return row;

    const earnings = getPriceForEventDate(keywordMap, row.title || '', eventDate, DEFAULT_PRICE);
    return { ...row, earnings };
  });
  return result;
}

export function runEarningsFull(events: CalendarEventRow[], mapping?: KeywordMappingRow[]): CalendarEventRow[] {
  const rows = mapping ?? loadKeywordMapping();
  const keywordMap = buildKeywordMap(rows);
  return runEarnings(events, keywordMap, false);
}

export function runEarningsIncremental(events: CalendarEventRow[], mapping?: KeywordMappingRow[]): CalendarEventRow[] {
  const rows = mapping ?? loadKeywordMapping();
  const keywordMap = buildKeywordMap(rows);
  return runEarnings(events, keywordMap, true);
}
