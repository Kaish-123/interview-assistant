import path from 'path';

const APP_DIR = path.resolve(__dirname, '..');
const DATA_DIR = path.join(APP_DIR, 'data');
const CONFIG_DIR = path.join(APP_DIR, 'config');

export const paths = {
  appDir: APP_DIR,
  dataDir: DATA_DIR,
  configDir: CONFIG_DIR,
  eventsFile: path.join(DATA_DIR, 'events.json'),
  keywordMappingFile: path.join(DATA_DIR, 'keywordMapping.json'),
  settingsFile: path.join(DATA_DIR, 'settings.json'),
  credentialsFile: path.join(CONFIG_DIR, 'credentials.json'),
  tokensFile: path.join(CONFIG_DIR, 'tokens.json'),
} as const;

export const DEFAULT_PRICE = 12500;
export const MANUAL_YES_VALUES = new Set(['yes', 'y', 'true', '1']);
export const EPOCH_START = new Date(2020, 0, 1);
export const START_DATE = new Date(2024, 0, 1);
export const END_DATE = new Date(2026, 2, 1); // Mar 1, 2026

export const CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly'];
export const SPREADSHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets'];
