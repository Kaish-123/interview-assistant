import { ensureDataDir, loadEvents, loadKeywordMapping, saveEvents, saveKeywordMapping } from './storage';
import { runEarningsFull, buildKeywordMap, getPriceForEventDate } from './earnings';
import type { CalendarEventRow, KeywordMappingRow } from './types';
import { DEFAULT_PRICE } from './config';

export function runVerifyForServer(): { ok: boolean; message: string; checks: string[] } {
  const checks: string[] = [];
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

  const c1 = vamshiBefore === 5000;
  const c2 = vamshiAfter === 8000;
  const c3 = ramAfter === 10000;
  const c4 = unknown === DEFAULT_PRICE;
  checks.push(`vamshi before 2026-01-01: ${vamshiBefore} ${c1 ? 'OK' : 'FAIL'}`);
  checks.push(`vamshi after 2026-01-01: ${vamshiAfter} ${c2 ? 'OK' : 'FAIL'}`);
  checks.push(`Ram 2026-02-11: ${ramAfter} ${c3 ? 'OK' : 'FAIL'}`);
  checks.push(`Unknown default: ${unknown} ${c4 ? 'OK' : 'FAIL'}`);

  saveKeywordMapping(fixtureMapping);
  saveEvents(fixtureEvents);
  const updated = runEarningsFull(fixtureEvents);
  saveEvents(updated);
  const runOk =
    updated[0].earnings === 5000 &&
    updated[1].earnings === 8000 &&
    updated[2].earnings === 10000 &&
    updated[3].earnings === DEFAULT_PRICE;
  checks.push(`runEarningsFull on fixture: ${runOk ? 'OK' : 'FAIL'}`);

  const loadedEvents = loadEvents();
  const loadedMapping = loadKeywordMapping();
  const storageOk = loadedEvents.length === 4 && loadedMapping.length === 5;
  checks.push(`Storage: ${loadedEvents.length} events, ${loadedMapping.length} mapping ${storageOk ? 'OK' : 'FAIL'}`);

  const ok = c1 && c2 && c3 && c4 && runOk && storageOk;
  const message = ok
    ? 'All checks passed.'
    : checks.filter((c) => c.endsWith('FAIL')).join('\n');
  return { ok, message, checks };
}
