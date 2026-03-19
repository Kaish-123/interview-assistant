import fs from 'fs';
import path from 'path';
import { paths } from './config';
import type { CalendarEventRow, KeywordMappingRow } from './types';

function ensureDir(dir: string): void {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

export function loadEvents(): CalendarEventRow[] {
  ensureDir(paths.dataDir);
  if (!fs.existsSync(paths.eventsFile)) {
    return [];
  }
  const raw = fs.readFileSync(paths.eventsFile, 'utf-8');
  try {
    const data = JSON.parse(raw);
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export function saveEvents(events: CalendarEventRow[]): void {
  ensureDir(paths.dataDir);
  fs.writeFileSync(paths.eventsFile, JSON.stringify(events, null, 2), 'utf-8');
}

export function loadKeywordMapping(): KeywordMappingRow[] {
  ensureDir(paths.dataDir);
  if (!fs.existsSync(paths.keywordMappingFile)) {
    return [];
  }
  const raw = fs.readFileSync(paths.keywordMappingFile, 'utf-8');
  try {
    const data = JSON.parse(raw);
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export function saveKeywordMapping(rows: KeywordMappingRow[]): void {
  ensureDir(paths.dataDir);
  fs.writeFileSync(paths.keywordMappingFile, JSON.stringify(rows, null, 2), 'utf-8');
}

export function ensureDataDir(): void {
  ensureDir(paths.dataDir);
  if (!fs.existsSync(paths.eventsFile)) {
    fs.writeFileSync(paths.eventsFile, '[]', 'utf-8');
  }
  if (!fs.existsSync(paths.keywordMappingFile)) {
    const defaultMapping: KeywordMappingRow[] = [];
    fs.writeFileSync(paths.keywordMappingFile, JSON.stringify(defaultMapping, null, 2), 'utf-8');
  }
}
