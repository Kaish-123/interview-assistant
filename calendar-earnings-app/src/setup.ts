/**
 * One-time setup: create config/ and data/, copy example keyword mapping if missing.
 * Run: npm run build && node dist/setup.js   or   npm run setup
 */
import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(__dirname, '..');
const CONFIG_DIR = path.join(ROOT, 'config');
const DATA_DIR = path.join(ROOT, 'data');
const CREDENTIALS_EXAMPLE = path.join(CONFIG_DIR, 'credentials.example.json');
const KEYWORD_EXAMPLE = path.join(DATA_DIR, 'keywordMapping.example.json');
const KEYWORD_FILE = path.join(DATA_DIR, 'keywordMapping.json');
const EVENTS_FILE = path.join(DATA_DIR, 'events.json');

function main(): void {
  if (!fs.existsSync(CONFIG_DIR)) {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
    console.log('Created config/');
  }
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    console.log('Created data/');
  }
  if (!fs.existsSync(EVENTS_FILE)) {
    fs.writeFileSync(EVENTS_FILE, '[]', 'utf-8');
    console.log('Created data/events.json');
  }
  if (!fs.existsSync(KEYWORD_FILE)) {
    if (fs.existsSync(KEYWORD_EXAMPLE)) {
      fs.copyFileSync(KEYWORD_EXAMPLE, KEYWORD_FILE);
      console.log('Copied keywordMapping.example.json → keywordMapping.json');
    } else {
      fs.writeFileSync(KEYWORD_FILE, '[]', 'utf-8');
      console.log('Created data/keywordMapping.json (empty). Add keywords or copy from data/keywordMapping.example.json');
    }
  }
  const hasCreds = fs.existsSync(path.join(CONFIG_DIR, 'credentials.json'));
  if (!hasCreds && fs.existsSync(CREDENTIALS_EXAMPLE)) {
    console.log('\nNext: add config/credentials.json (see config/README.md). Then run: npm run dev');
  } else if (!hasCreds) {
    console.log('\nNext: add config/credentials.json from Google Cloud Console. Then run: npm run dev');
  } else {
    console.log('\nReady. Run: npm run dev   then open http://localhost:3000');
  }
}

main();
