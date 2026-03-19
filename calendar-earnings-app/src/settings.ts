import fs from 'fs';
import { paths, START_DATE, END_DATE } from './config';

export interface AppSettings {
  startDate: string;
  endDate: string;
  spreadsheetId?: string;
  callCalendarSheetName?: string;
  keywordMappingSheetName?: string;
}

const DEFAULT_SETTINGS: AppSettings = {
  startDate: formatDate(START_DATE),
  endDate: formatDate(END_DATE),
  spreadsheetId: '',
  callCalendarSheetName: 'CallCalendarSheet',
  keywordMappingSheetName: 'KeywordMapping',
};

function formatDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function ensureDataDir(): void {
  if (!fs.existsSync(paths.dataDir)) {
    fs.mkdirSync(paths.dataDir, { recursive: true });
  }
}

export function loadSettings(): AppSettings {
  ensureDataDir();
  if (!fs.existsSync(paths.settingsFile)) {
    return { ...DEFAULT_SETTINGS };
  }
  try {
    const raw = fs.readFileSync(paths.settingsFile, 'utf-8');
    const data = JSON.parse(raw) as Partial<AppSettings>;
    return {
      startDate: data.startDate && /^\d{4}-\d{2}-\d{2}$/.test(data.startDate) ? data.startDate : DEFAULT_SETTINGS.startDate,
      endDate: data.endDate && /^\d{4}-\d{2}-\d{2}$/.test(data.endDate) ? data.endDate : DEFAULT_SETTINGS.endDate,
      spreadsheetId: typeof data.spreadsheetId === 'string' ? data.spreadsheetId.trim() : DEFAULT_SETTINGS.spreadsheetId,
      callCalendarSheetName: data.callCalendarSheetName || DEFAULT_SETTINGS.callCalendarSheetName,
      keywordMappingSheetName: data.keywordMappingSheetName || DEFAULT_SETTINGS.keywordMappingSheetName,
    };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

export function saveSettings(settings: AppSettings): void {
  ensureDataDir();
  fs.writeFileSync(paths.settingsFile, JSON.stringify(settings, null, 2), 'utf-8');
}

/**
 * Returns the current date range as Date objects (start of day for start, end of day for end).
 * Used by calendar fetch and earnings logic.
 */
export function getDateRange(): { startDate: Date; endDate: Date } {
  const s = loadSettings();
  const startDate = new Date(s.startDate + 'T00:00:00.000Z');
  const endDate = new Date(s.endDate + 'T23:59:59.999Z');
  if (isNaN(startDate.getTime())) startDate.setTime(START_DATE.getTime());
  if (isNaN(endDate.getTime()) || endDate < startDate) endDate.setTime(END_DATE.getTime());
  return { startDate, endDate };
}
