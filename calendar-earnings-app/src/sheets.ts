import { google } from 'googleapis';
import fs from 'fs';
import type { CalendarEventRow, KeywordMappingRow } from './types';
import { paths } from './config';
import { loadSettings } from './settings';

const REDIRECT_URI = 'http://localhost:3000/';

function getAuthClient() {
  if (!fs.existsSync(paths.credentialsFile)) {
    throw new Error('Missing credentials.json. Add Google OAuth credentials with Calendar + Sheets scope.');
  }
  const credentials = JSON.parse(fs.readFileSync(paths.credentialsFile, 'utf-8'));
  const { client_secret, client_id } = credentials.installed || credentials.web;
  const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, REDIRECT_URI);
  if (fs.existsSync(paths.tokensFile)) {
    const tokens = JSON.parse(fs.readFileSync(paths.tokensFile, 'utf-8'));
    oAuth2Client.setCredentials(tokens);
  } else {
    throw new Error('Not authenticated. Run npm run auth (Calendar + Sheets scope).');
  }
  return oAuth2Client;
}

/**
 * Read KeywordMapping from Google Sheet (columns A=Keyword, B=Price, C=Start Effective Date).
 */
export async function readKeywordMappingFromSheet(
  spreadsheetId: string,
  sheetName: string
): Promise<KeywordMappingRow[]> {
  const auth = getAuthClient();
  const sheets = google.sheets({ version: 'v4', auth });
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: `'${sheetName}'!A2:C`,
  });
  const rows = (res.data.values || []) as (string | number)[][];
  const out: KeywordMappingRow[] = [];
  for (const row of rows) {
    const keyword = (row[0] || '').toString().trim();
    if (!keyword) continue;
    const price = Number(row[1]) || 0;
    const startEffectiveDate = row[2] ? String(row[2]).trim() || null : null;
    out.push({ keyword, price, startEffectiveDate: startEffectiveDate || null });
  }
  return out;
}

const CALL_CALENDAR_HEADERS = [
  'Event ID',
  'Event Title',
  'Start Time',
  'End Time',
  'Earnings',
  'Manual Update',
  'Selection Status',
];

/**
 * Write events to CallCalendarSheet. Clears the sheet and writes headers + data.
 */
export async function writeCallCalendarSheet(
  spreadsheetId: string,
  sheetName: string,
  events: CalendarEventRow[]
): Promise<void> {
  const auth = getAuthClient();
  const sheets = google.sheets({ version: 'v4', auth });

  const rows: (string | number)[][] = [CALL_CALENDAR_HEADERS];
  for (const e of events) {
    rows.push([
      e.eventId,
      e.title || '',
      e.start || '',
      e.end || '',
      e.earnings != null ? e.earnings : '',
      e.manualUpdate || '',
      e.selectionStatus || '',
    ]);
  }

  const range = `'${sheetName}'!A1:G${rows.length}`;
  await sheets.spreadsheets.values.update({
    spreadsheetId,
    range,
    valueInputOption: 'USER_ENTERED',
    requestBody: { values: rows },
  });
}

/**
 * Read existing CallCalendarSheet for incremental merge (eventId -> row with earnings, manual, selection).
 */
export async function readCallCalendarSheet(
  spreadsheetId: string,
  sheetName: string
): Promise<CalendarEventRow[]> {
  const auth = getAuthClient();
  const sheets = google.sheets({ version: 'v4', auth });
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: `'${sheetName}'!A2:G`,
  });
  const rows = (res.data.values || []) as (string | number)[][];
  const out: CalendarEventRow[] = [];
  for (const row of rows) {
    if (!row[0]) continue;
    out.push({
      eventId: String(row[0]),
      title: String(row[1] || ''),
      start: String(row[2] || ''),
      end: String(row[3] || ''),
      earnings: row[4] !== '' && row[4] !== undefined && row[4] !== null ? Number(row[4]) : null,
      manualUpdate: String(row[5] || ''),
      selectionStatus: String(row[6] || ''),
    });
  }
  return out;
}

export function isSheetsEnabled(): boolean {
  const s = loadSettings();
  return !!s.spreadsheetId && s.spreadsheetId.length > 0;
}
