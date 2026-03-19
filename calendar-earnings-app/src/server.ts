import http from 'http';
import fs from 'fs';
import { paths } from './config';
import { loadEvents } from './storage';
import { loadSettings, saveSettings } from './settings';
import { fullLoad, incremental, getAuthUrl, saveTokensFromCode } from './calendar';
import { runEarningsFull } from './earnings';

const PORT = Number(process.env.PORT) || 3000;
const HOST = '127.0.0.1';

function html(title: string, body: string): string {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${title}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 560px; margin: 2rem auto; padding: 0 1rem; }
    h1 { color: #1a1a2e; }
    .card { background: #f6f6f6; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
    button, .btn { display: inline-block; padding: 0.6rem 1rem; margin: 0.25rem; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 14px; }
    button:hover, .btn:hover { background: #1d4ed8; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }
    .secondary { background: #64748b; }
    .secondary:hover { background: #475569; }
    #result { margin-top: 1rem; padding: 0.75rem; border-radius: 6px; white-space: pre-wrap; }
    .ok { background: #dcfce7; color: #166534; }
    .err { background: #fee2e2; color: #991b1b; }
    .status { color: #64748b; font-size: 14px; margin-bottom: 1rem; }
    .events-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; font-size: 13px; }
    .events-table th, .events-table td { text-align: left; padding: 0.35rem 0.5rem; border-bottom: 1px solid #e2e8f0; }
    .events-table th { background: #e2e8f0; color: #334155; }
    .events-table tr:hover { background: #f1f5f9; }
    #eventsBox { max-height: 360px; overflow: auto; }
    .toggle-events { margin-top: 0.5rem; }
    .form-row { margin: 0.5rem 0; }
    .form-row label { display: inline-block; width: 100px; }
    input[type=date] { padding: 0.35rem; }
  </style>
</head>
<body>
  <h1>Calendar Earnings</h1>
  ${body}
</body>
</html>`;
}

function getStatus(): { eventsCount: number; hasCredentials: boolean; hasTokens: boolean } {
  const events = loadEvents();
  const hasCredentials = fs.existsSync(paths.credentialsFile);
  const hasTokens = fs.existsSync(paths.tokensFile);
  return { eventsCount: events.length, hasCredentials, hasTokens };
}

async function handleRun(
  pathname: string,
  res: http.ServerResponse,
  sendJson: (obj: object) => void
): Promise<boolean> {
  if (pathname === '/run/full-load') {
    try {
      const out = await fullLoad();
      sendJson({ success: true, message: out.message, count: out.count });
    } catch (e) {
      sendJson({ success: false, error: (e as Error).message });
    }
    return true;
  }
  if (pathname === '/run/incremental') {
    try {
      const out = await incremental();
      sendJson({ success: true, message: out.message, count: out.count });
    } catch (e) {
      sendJson({ success: false, error: (e as Error).message });
    }
    return true;
  }
  if (pathname === '/run/earnings-only') {
    try {
      const events = loadEvents();
      const updated = runEarningsFull(events);
      const { saveEvents } = await import('./storage');
      saveEvents(updated);
      sendJson({ success: true, message: `Earnings recalculated for ${updated.length} events.`, count: updated.length });
    } catch (e) {
      sendJson({ success: false, error: (e as Error).message });
    }
    return true;
  }
  if (pathname === '/run/verify') {
    try {
      const { runVerifyForServer } = await import('./verify-server');
      const result = runVerifyForServer();
      sendJson({ success: result.ok, message: result.message, checks: result.checks });
    } catch (e) {
      sendJson({ success: false, error: (e as Error).message });
    }
    return true;
  }
  return false;
}

function dashboardHtml(lastResult: string | null, status: ReturnType<typeof getStatus>): string {
  const authLink = status.hasCredentials && !status.hasTokens
    ? `<p><a href="/auth" class="btn">Connect Google (OAuth)</a></p>`
    : status.hasTokens
      ? '<p class="status">Google: connected</p>'
      : '<p class="status">Add config/credentials.json and click Connect Google.</p>';

  const runButtons = status.hasTokens
    ? `
    <p>
      <button onclick="run('full-load')">Full load</button>
      <button onclick="run('incremental')" class="secondary">Incremental</button>
      <button onclick="run('earnings-only')" class="secondary">Earnings only</button>
    </p>`
    : '<p class="status">Connect Google first to run full load / incremental.</p>';

  const eventsSection = status.eventsCount > 0
    ? `
    <p class="toggle-events"><button type="button" class="secondary" onclick="toggleEvents()">Show events (${status.eventsCount})</button></p>
    <div id="eventsBox" style="display:none;">
      <table class="events-table"><thead><tr><th>Title</th><th>Start</th><th>Earnings</th></tr></thead><tbody id="eventsBody"></tbody></table>
    </div>`
    : '<p class="status">No events yet. Click <strong>Full load</strong> to fetch from Google Calendar.</p>';

  return `
  <div class="card">
    <p class="status"><strong>Date range</strong> (calendar fetch &amp; earnings)</p>
    <div class="form-row">
      <label for="startDate">From</label>
      <input type="date" id="startDate" />
    </div>
    <div class="form-row">
      <label for="endDate">To</label>
      <input type="date" id="endDate" />
    </div>
    <p><button type="button" class="secondary" onclick="saveSettingsAll()">Save date range</button> <span id="dateRangeMsg"></span></p>
  </div>
  <div class="card">
    <p class="status"><strong>Google Sheet</strong> (CallCalendarSheet + KeywordMapping for Looker)</p>
    <p class="status">When set, Full load / Incremental sync to this spreadsheet. Re-auth once to grant Sheets access.</p>
    <div class="form-row">
      <label for="spreadsheetId">Spreadsheet ID</label>
      <input type="text" id="spreadsheetId" placeholder="From Sheet URL: .../d/SPREADSHEET_ID/edit" style="width: 100%; max-width: 320px;" />
    </div>
    <div class="form-row">
      <label for="callCalendarSheetName">Calendar sheet</label>
      <input type="text" id="callCalendarSheetName" placeholder="CallCalendarSheet" style="width: 160px;" />
    </div>
    <div class="form-row">
      <label for="keywordMappingSheetName">Mapping sheet</label>
      <input type="text" id="keywordMappingSheetName" placeholder="KeywordMapping" style="width: 160px;" />
    </div>
    <p><button type="button" class="secondary" onclick="saveSettingsAll()">Save sheet settings</button> <span id="sheetMsg"></span></p>
    <p class="status"><strong>Trigger (incremental on calendar change):</strong> Call <code>POST /trigger/incremental</code> from Apps Script or cron.</p>
  </div>
  <div class="card">
    <p class="status">Events in data: <strong>${status.eventsCount}</strong></p>
    ${authLink}
    ${runButtons}
    ${eventsSection}
    <p>
      <button onclick="run('verify')" class="secondary">Run verify (no Google)</button>
    </p>
    <div id="result">${lastResult != null ? lastResult : ''}</div>
  </div>
  <script>
    (function loadSettings() {
      fetch('/api/settings').then(function(r) { return r.json(); }).then(function(s) {
        if (s.startDate) document.getElementById('startDate').value = s.startDate;
        if (s.endDate) document.getElementById('endDate').value = s.endDate;
        if (s.spreadsheetId) document.getElementById('spreadsheetId').value = s.spreadsheetId;
        if (s.callCalendarSheetName) document.getElementById('callCalendarSheetName').value = s.callCalendarSheetName;
        if (s.keywordMappingSheetName) document.getElementById('keywordMappingSheetName').value = s.keywordMappingSheetName;
      }).catch(function() {});
    })();
    async function saveSettingsAll() {
      var start = document.getElementById('startDate').value;
      var end = document.getElementById('endDate').value;
      var spreadsheetId = document.getElementById('spreadsheetId').value.trim();
      var callCalendarSheetName = document.getElementById('callCalendarSheetName').value.trim() || 'CallCalendarSheet';
      var keywordMappingSheetName = document.getElementById('keywordMappingSheetName').value.trim() || 'KeywordMapping';
      var msg = document.getElementById('dateRangeMsg');
      var sheetMsg = document.getElementById('sheetMsg');
      if (!start || !end) { msg.textContent = 'Set both dates.'; msg.className = 'err'; return; }
      if (start > end) { msg.textContent = 'From must be before To.'; msg.className = 'err'; return; }
      msg.textContent = ''; sheetMsg.textContent = 'Saving...';
      try {
        var r = await fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ startDate: start, endDate: end, spreadsheetId: spreadsheetId, callCalendarSheetName: callCalendarSheetName, keywordMappingSheetName: keywordMappingSheetName }) });
        var j = await r.json();
        if (j.success) { msg.textContent = 'Saved.'; msg.className = 'ok'; sheetMsg.textContent = 'Saved.'; sheetMsg.className = 'ok'; } else { sheetMsg.textContent = j.error || 'Failed'; sheetMsg.className = 'err'; }
      } catch (e) { sheetMsg.textContent = 'Error'; sheetMsg.className = 'err'; }
    }
    async function run(cmd) {
      const result = document.getElementById('result');
      result.textContent = 'Running...';
      result.className = '';
      try {
        const r = await fetch('/run/' + cmd, { method: 'POST' });
        const j = await r.json();
        result.textContent = j.message || j.error || JSON.stringify(j);
        result.className = j.success ? 'ok' : 'err';
        if (j.success && (cmd === 'full-load' || cmd === 'incremental' || cmd === 'earnings-only')) setTimeout(function(){ location.reload(); }, 800);
      } catch (e) {
        result.textContent = 'Error: ' + e.message;
        result.className = 'err';
      }
    }
    async function toggleEvents() {
      var box = document.getElementById('eventsBox');
      if (box.style.display === 'none') {
        box.style.display = 'block';
        var body = document.getElementById('eventsBody');
        if (body && body.innerHTML === '') {
          body.innerHTML = '<tr><td colspan="3">Loading...</td></tr>';
          var r = await fetch('/api/events?limit=100');
          var d = await r.json();
          body.innerHTML = d.events.map(function(e) {
            var start = e.start ? new Date(e.start).toLocaleString() : '';
            var t = (e.title || '').split('<').join('&lt;');
            return '<tr><td>' + t + '</td><td>' + start + '</td><td>' + (e.earnings != null ? e.earnings : '') + '</td></tr>';
          }).join('') || '<tr><td colspan="3">No events</td></tr>';
        }
      } else {
        box.style.display = 'none';
      }
    }
  </script>`;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url || '/', `http://${HOST}:${PORT}`);
  const pathname = url.pathname;
  const code = url.searchParams.get('code');

  const sendJson = (obj: object) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(obj));
  };

  // OAuth callback
  if (code && pathname === '/') {
    try {
      await saveTokensFromCode(code);
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(html('Success', `
        <div class="card">
          <p><strong>Google connected.</strong></p>
          <p><a href="/" class="btn">Back to dashboard</a></p>
        </div>`));
    } catch (e) {
      res.writeHead(500, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(html('Error', `<div class="card"><p class="err">${(e as Error).message}</p><p><a href="/" class="btn">Back</a></p></div>`));
    }
    return;
  }

  // Auth redirect (link to Google OAuth)
  if (pathname === '/auth') {
    try {
      const authUrl = getAuthUrl();
      res.writeHead(302, { Location: authUrl });
      res.end();
    } catch (e) {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(html('Error', `<div class="card"><p class="err">${(e as Error).message}</p><p><a href="/" class="btn">Back</a></p></div>`));
    }
    return;
  }

  // POST /run/*
  if (req.method === 'POST' && pathname.startsWith('/run/')) {
    const handled = await handleRun(pathname, res, sendJson);
    if (handled) return;
  }

  // GET /api/settings -> current date range
  if (pathname === '/api/settings' && req.method === 'GET') {
    sendJson(loadSettings());
    return;
  }

  // POST /api/settings -> save all settings (merge with existing)
  if (pathname === '/api/settings' && req.method === 'POST') {
    let body = '';
    req.on('data', (chunk: Buffer) => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const current = loadSettings();
        const data = JSON.parse(body || '{}') as Partial<{ startDate: string; endDate: string; spreadsheetId: string; callCalendarSheetName: string; keywordMappingSheetName: string }>;
        const startDate = typeof data.startDate === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(data.startDate) ? data.startDate : current.startDate;
        const endDate = typeof data.endDate === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(data.endDate) ? data.endDate : current.endDate;
        if (startDate > endDate) {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: false, error: 'Start date must be before end date.' }));
          return;
        }
        const spreadsheetId = typeof data.spreadsheetId === 'string' ? data.spreadsheetId.trim() : (current.spreadsheetId ?? '');
        const callCalendarSheetName = (data.callCalendarSheetName && String(data.callCalendarSheetName).trim()) || current.callCalendarSheetName || 'CallCalendarSheet';
        const keywordMappingSheetName = (data.keywordMappingSheetName && String(data.keywordMappingSheetName).trim()) || current.keywordMappingSheetName || 'KeywordMapping';
        saveSettings({ startDate, endDate, spreadsheetId, callCalendarSheetName, keywordMappingSheetName });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true }));
      } catch (e) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: (e as Error).message }));
      }
    });
    return;
  }

  // POST or GET /trigger/incremental -> run incremental (for Apps Script or cron)
  if (pathname === '/trigger/incremental' && (req.method === 'POST' || req.method === 'GET')) {
    try {
      const out = await incremental();
      sendJson({ success: true, message: out.message, count: out.count });
    } catch (e) {
      sendJson({ success: false, error: (e as Error).message });
    }
    return;
  }

  // GET /api/events -> JSON list of events (for dashboard table)
  if (pathname === '/api/events' && req.method === 'GET') {
    const events = loadEvents();
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '100', 10) || 100, 500);
    const slice = events.slice(-limit).reverse(); // latest first
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ total: events.length, events: slice }));
    return;
  }

  // GET / -> dashboard
  if (pathname === '/' && req.method === 'GET') {
    const status = getStatus();
    const lastResult = url.searchParams.get('result') ? decodeURIComponent(url.searchParams.get('result')!) : null;
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(html('Calendar Earnings', dashboardHtml(lastResult, status)));
    return;
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not found');
});

server.listen(PORT, HOST, () => {
  console.log(`Dashboard: http://${HOST}:${PORT}`);
  console.log('Open this URL in your browser to run and test.');
});
