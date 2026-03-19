import http from 'http';
import { exec } from 'child_process';
import { getAuthUrl, saveTokensFromCode } from './calendar';
import { paths } from './config';
import fs from 'fs';

const PORT = 3000;

function openBrowser(url: string): void {
  const cmd = process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'start' : 'xdg-open';
  exec(`${cmd} "${url}"`, () => {});
}

export async function runAuth(): Promise<void> {
  if (!fs.existsSync(paths.configDir)) {
    fs.mkdirSync(paths.configDir, { recursive: true });
  }
  if (!fs.existsSync(paths.credentialsFile)) {
    console.error(`Place your Google OAuth credentials at: ${paths.credentialsFile}`);
    console.error('Download from: https://console.cloud.google.com/apis/credentials');
    console.error('Create OAuth 2.0 Client ID (Desktop app), then download JSON and save as config/credentials.json');
    process.exit(1);
  }

  const url = getAuthUrl();
  console.log('Open this URL in your browser to authorize:');
  console.log(url);
  console.log(`\nListening for callback on http://localhost:${PORT}...`);

  const server = http.createServer(async (req, res) => {
    const u = new URL(req.url || '', `http://localhost:${PORT}`);
    const code = u.searchParams.get('code');
    if (code) {
      try {
        await saveTokensFromCode(code);
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end('<h1>Success</h1><p>You can close this tab and return to the terminal.</p>');
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Error saving tokens: ' + (e as Error).message);
      }
      server.close();
    } else {
      res.writeHead(400, { 'Content-Type': 'text/plain' });
      res.end('Missing code parameter.');
    }
  });
  server.listen(PORT, () => {
    openBrowser(url);
  });
}
