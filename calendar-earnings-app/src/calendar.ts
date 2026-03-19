import { google } from 'googleapis';
import fs from 'fs';
import type { CalendarEventRow } from './types';
import { paths, CALENDAR_SCOPES, SPREADSHEET_SCOPES } from './config';
import { getDateRange, loadSettings } from './settings';
import { loadEvents, saveEvents } from './storage';
import * as sheets from './sheets';

const REDIRECT_URI = 'http://localhost:3000/';

function getAuthClient() {
  if (!fs.existsSync(paths.credentialsFile)) {
    throw new Error(
      `Missing ${paths.credentialsFile}. Download from Google Cloud Console (Calendar API) and place in config/credentials.json`
    );
  }
  const credentials = JSON.parse(fs.readFileSync(paths.credentialsFile, 'utf-8'));
  const { client_secret, client_id } = credentials.installed || credentials.web;
  const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, REDIRECT_URI);

  if (fs.existsSync(paths.tokensFile)) {
    const tokens = JSON.parse(fs.readFileSync(paths.tokensFile, 'utf-8'));
    oAuth2Client.setCredentials(tokens);
  } else {
    throw new Error('Not authenticated. Run: npm run auth');
  }
  return oAuth2Client;
}

function eventToRow(ev: { id?: string | null; summary?: string | null; start?: { dateTime?: string | null; date?: string | null } | null; end?: { dateTime?: string | null; date?: string | null } | null }): CalendarEventRow {
  return {
    eventId: String(ev.id || ''),
    title: String(ev.summary || ''),
    start: String((ev.start && (ev.start.dateTime || ev.start.date)) || ''),
    end: String((ev.end && (ev.end.dateTime || ev.end.date)) || ''),
    earnings: null,
    manualUpdate: '',
    selectionStatus: '',
  };
}

/**
 * Fetch ALL events in the configured date range (from dashboard settings).
 * Uses pagination so every event is retrieved (Google returns 250 per page).
 */
export async function fetchCalendarEvents(): Promise<CalendarEventRow[]> {
  const { startDate, endDate } = getDateRange();
  const auth = getAuthClient();
  const calendar = google.calendar({ version: 'v3', auth });
  const allItems: CalendarEventRow[] = [];
  let pageToken: string | undefined;

  do {
    const res = await calendar.events.list({
      calendarId: 'primary',
      timeMin: startDate.toISOString(),
      timeMax: endDate.toISOString(),
      singleEvents: true,
      orderBy: 'startTime',
      maxResults: 2500,
      pageToken: pageToken,
    });
    const items = res.data.items || [];
    for (const ev of items) {
      allItems.push(eventToRow(ev));
    }
    pageToken = res.data.nextPageToken || undefined;
  } while (pageToken);

  return allItems;
}

export function mergeEvents(
  existing: CalendarEventRow[],
  fetched: CalendarEventRow[]
): CalendarEventRow[] {
  const byId = new Map<string, CalendarEventRow>();
  for (const row of existing) {
    if (row.eventId) byId.set(row.eventId, row);
  }
  for (const row of fetched) {
    const prev = byId.get(row.eventId);
    if (prev) {
      byId.set(row.eventId, {
        ...row,
        earnings: prev.earnings,
        manualUpdate: prev.manualUpdate,
        selectionStatus: prev.selectionStatus,
      });
    } else {
      byId.set(row.eventId, row);
    }
  }
  return Array.from(byId.values()).sort(
    (a, b) => new Date(a.start).getTime() - new Date(b.start).getTime()
  );
}

export async function fullLoad(): Promise<{ count: number; message: string }> {
  const settings = loadSettings();
  const fetched = await fetchCalendarEvents();
  let mapping: { keyword: string; price: number; startEffectiveDate: string | null }[] | undefined;
  if (sheets.isSheetsEnabled() && settings.spreadsheetId && settings.keywordMappingSheetName) {
    mapping = await sheets.readKeywordMappingFromSheet(settings.spreadsheetId, settings.keywordMappingSheetName);
  }
  saveEvents(fetched);
  const { runEarningsFull } = await import('./earnings');
  const events = loadEvents();
  const updated = runEarningsFull(events, mapping);
  saveEvents(updated);
  if (sheets.isSheetsEnabled() && settings.spreadsheetId && settings.callCalendarSheetName) {
    await sheets.writeCallCalendarSheet(settings.spreadsheetId, settings.callCalendarSheetName, updated);
  }
  const msg = `Full load done: ${updated.length} events${sheets.isSheetsEnabled() ? ', synced to Google Sheet' : ''}.`;
  console.log(msg);
  return { count: updated.length, message: msg };
}

export async function incremental(): Promise<{ count: number; message: string }> {
  const settings = loadSettings();
  const fetched = await fetchCalendarEvents();
  let existing = loadEvents();
  if (sheets.isSheetsEnabled() && settings.spreadsheetId && settings.callCalendarSheetName) {
    try {
      existing = await sheets.readCallCalendarSheet(settings.spreadsheetId, settings.callCalendarSheetName);
    } catch (_) {
      existing = loadEvents();
    }
  }
  const merged = mergeEvents(existing, fetched);
  saveEvents(merged);
  let mapping: { keyword: string; price: number; startEffectiveDate: string | null }[] | undefined;
  if (sheets.isSheetsEnabled() && settings.spreadsheetId && settings.keywordMappingSheetName) {
    mapping = await sheets.readKeywordMappingFromSheet(settings.spreadsheetId, settings.keywordMappingSheetName);
  }
  const { runEarningsIncremental } = await import('./earnings');
  const updated = runEarningsIncremental(merged, mapping);
  saveEvents(updated);
  if (sheets.isSheetsEnabled() && settings.spreadsheetId && settings.callCalendarSheetName) {
    await sheets.writeCallCalendarSheet(settings.spreadsheetId, settings.callCalendarSheetName, updated);
  }
  const msg = `Incremental done: ${updated.length} events${sheets.isSheetsEnabled() ? ', synced to Google Sheet' : ''}.`;
  console.log(msg);
  return { count: updated.length, message: msg };
}

export function getAuthUrl(): string {
  if (!fs.existsSync(paths.credentialsFile)) {
    throw new Error(`Place credentials.json in ${paths.configDir}`);
  }
  const credentials = JSON.parse(fs.readFileSync(paths.credentialsFile, 'utf-8'));
  const { client_secret, client_id } = credentials.installed || credentials.web;
  const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, REDIRECT_URI);
  return oAuth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: [...CALENDAR_SCOPES, ...SPREADSHEET_SCOPES],
    prompt: 'consent',
  });
}

export async function saveTokensFromCode(code: string): Promise<void> {
  const credentials = JSON.parse(fs.readFileSync(paths.credentialsFile, 'utf-8'));
  const { client_secret, client_id } = credentials.installed || credentials.web;
  const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, REDIRECT_URI);
  const { tokens } = await oAuth2Client.getToken(code);
  if (!fs.existsSync(paths.configDir)) fs.mkdirSync(paths.configDir, { recursive: true });
  fs.writeFileSync(paths.tokensFile, JSON.stringify(tokens, null, 2), 'utf-8');
  console.log('Tokens saved. You can run npm run full-load or npm run incremental.');
}
