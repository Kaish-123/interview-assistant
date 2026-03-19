/**
 * Run this to verify earnings logic and storage without Google Calendar.
 * Uses fixture data so the pipeline can be tested end-to-end locally.
 */
import { ensureDataDir, loadEvents, saveEvents, loadKeywordMapping, saveKeywordMapping } from './storage';
import { runEarningsFull, buildKeywordMap, getPriceForEventDate } from './earnings';
import type { CalendarEventRow, KeywordMappingRow } from './types';
import { DEFAULT_PRICE } from './config';

function runVerify(): void {
  ensureDataDir();

  const fixtureMapping: KeywordMappingRow[] = [
    { keyword: 'vamshi', price: 5000, startEffectiveDate: null },
    { keyword: 'vamshi', price: 8000, startEffectiveDate: '2026-01-01' },
    { keyword: 'ram', price: 9750, startEffectiveDate: null },
    { keyword: 'ram', price: 10000, startEffectiveDate: '2026-01-01' },
    { keyword: 'nobody', price: 0, startEffectiveDate: null },
  ];

  const fixtureEvents: CalendarEventRow[] = [
    { eventId: '1', title: 'vamshi call', start: '2025-06-15T10:00:00Z', end: '2025-06-15T11:00:00Z', earnings: null, manualUpdate: '' },
    { eventId: '2', title: 'vamshi call', start: '2026-02-07T14:00:00Z', end: '2026-02-07T15:00:00Z', earnings: null, manualUpdate: '' },
    { eventId: '3', title: 'Ram call', start: '2026-02-11T23:00:00Z', end: '2026-02-12T00:00:00Z', earnings: null, manualUpdate: '' },
    { eventId: '4', title: 'Unknown person call', start: '2025-12-01T09:00:00Z', end: '2025-12-01T10:00:00Z', earnings: null, manualUpdate: '' },
  ];

  const map = buildKeywordMap(fixtureMapping);
  const vamshiBefore = getPriceForEventDate(map, 'vamshi call', new Date('2025-06-15'), DEFAULT_PRICE);
  const vamshiAfter = getPriceForEventDate(map, 'vamshi call', new Date('2026-02-07'), DEFAULT_PRICE);
  const ramAfter = getPriceForEventDate(map, 'Ram call', new Date('2026-02-11'), DEFAULT_PRICE);
  const unknown = getPriceForEventDate(map, 'Unknown person call', new Date('2025-12-01'), DEFAULT_PRICE);

  console.log('Earnings logic check:');
  console.log('  vamshi 2025-06-15 (before 2026-01-01):', vamshiBefore, vamshiBefore === 5000 ? 'OK' : 'FAIL');
  console.log('  vamshi 2026-02-07 (after 2026-01-01):', vamshiAfter, vamshiAfter === 8000 ? 'OK' : 'FAIL');
  console.log('  Ram 2026-02-11:', ramAfter, ramAfter === 10000 ? 'OK' : 'FAIL');
  console.log('  Unknown (default 12500):', unknown, unknown === DEFAULT_PRICE ? 'OK' : 'FAIL');

  saveKeywordMapping(fixtureMapping);
  saveEvents(fixtureEvents);
  const updated = runEarningsFull(fixtureEvents);
  saveEvents(updated);
  const ok =
    updated[0].earnings === 5000 &&
    updated[1].earnings === 8000 &&
    updated[2].earnings === 10000 &&
    updated[3].earnings === DEFAULT_PRICE;
  console.log('  runEarningsFull on fixture:', ok ? 'OK' : 'FAIL');

  const loadedEvents = loadEvents();
  const loadedMapping = loadKeywordMapping();
  console.log('  Storage: events', loadedEvents.length, 'mapping', loadedMapping.length, loadedEvents.length === 4 && loadedMapping.length === 5 ? 'OK' : 'FAIL');

  console.log('\nVerification done. Data written to data/ for inspection.');
}

runVerify();
