# Calendar Earnings App (Node.js — runnable & verifiable)

Same behavior as the Google Apps Script version: **Google Calendar → events → earnings** from a keyword table with **effective-date pricing** and **12,500 default** for non-matches. This version runs on your machine so it can be **run, tested, and changed** end-to-end (e.g. by an AI or by you in the terminal).

---

## What it does

- **Fetches** events from your Google Calendar (primary) for the date range 2024-01-01 to 2026-03-01.
- **Stores** events in `data/events.json` and keyword mapping in `data/keywordMapping.json`.
- **Earnings**: matches event title to keywords; uses **Start Effective Date** so you can change a person’s rate from a date (e.g. 2026-01-01); no match → **12,500**.
- **Incremental**: only fills earnings for rows that don’t have a value yet.
- **Full load**: syncs all events and recalculates all earnings (except manual).

---

## Prerequisites

- **Node.js 18+**
- **Google Cloud project** with Calendar API enabled and OAuth 2.0 Desktop client credentials.

---

## One-time setup

### 1. Install

```bash
cd calendar-earnings-app
npm install
npm run build
```

### 2. Google OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → your project (or create one).
2. **APIs & Services** → **Enable API** → enable **Google Calendar API**.
3. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**.
4. Application type: **Desktop app**.
5. Add **Authorized redirect URI**: `http://localhost:3000/` (same as the dashboard URL).
6. Download the JSON and save it as **`config/credentials.json`** in this project.

### 3. Authenticate

```bash
npm run auth
```

A browser opens; log in with Google and allow calendar read access. On success, tokens are saved in `config/tokens.json` and the terminal says you can close the tab.

### 4. Keyword mapping

Edit **`data/keywordMapping.json`** (create it if missing). Example:

```json
[
  { "keyword": "vamshi", "price": 5000, "startEffectiveDate": null },
  { "keyword": "vamshi", "price": 8000, "startEffectiveDate": "2026-01-01" },
  { "keyword": "Ram", "price": 9750, "startEffectiveDate": null }
]
```

- `startEffectiveDate: null` = use this price for all dates (until a later dated row).
- `startEffectiveDate: "2026-01-01"` = use this price from that date onward.

---

## Commands

| Command | What it does |
|--------|----------------|
| **`npm run dev`** | Build and start the **dashboard** at **http://localhost:3000**. Open this in your browser to run full load, incremental, earnings-only, verify, and to connect Google (OAuth). |
| `npm run auth` | One-time OAuth; starts a small server, opens browser, saves tokens. (Or use “Connect Google” on the dashboard.) |
| `npm run full-load` | Fetch all calendar events, merge into `data/events.json`, recalc **all** earnings. |
| `npm run incremental` | Fetch events, merge, fill earnings **only for rows that are still empty**. |
| `npm run earnings-only` | Recalc all earnings from current `data/events.json` (no calendar fetch). |
| `npm run verify` | Run local test: earnings logic + storage with fixture data (no Google). |

---

## Verifying without Google

You can confirm the app logic without credentials:

```bash
npm run build
npm run verify
```

This uses fixture events and keyword mapping, runs the earnings logic, and checks effective-date and default 12,500. It also writes to `data/` so you can inspect the output.

---

## Data files

- **`data/events.json`** – Calendar events + earnings (and manual/selection if you add them).
- **`data/keywordMapping.json`** – Keyword, price, startEffectiveDate.
- **`config/credentials.json`** – Your OAuth client JSON (do not commit).
- **`config/tokens.json`** – Refresh/access tokens (do not commit).

---

## Google Sheet + trigger (replace Apps Script)

Set **Spreadsheet ID** and sheet names in the dashboard so the app writes to **CallCalendarSheet** and reads **KeywordMapping** from your Google Sheet (Looker keeps working). Re-auth once to grant Sheets scope. Trigger incremental when the calendar changes by calling **POST /trigger/incremental** from a small Apps Script or cron. See **GOOGLE_SHEETS_AND_TRIGGER.md**.

## End-to-end control

This repo is self-contained. You (or an AI) can:

- Run `npm run build` and `npm run verify` to validate logic.
- Change date range, default price, or file paths in `src/config.ts`.
- Change earnings rules in `src/earnings.ts`.
- Add features (e.g. export to CSV, filters) in the same codebase.

When you say **“use the calendar-earnings-app and do X”**, the assistant can edit these files, run `npm run build` and `npm run verify` (or `full-load` with your credentials), and confirm everything works—no Google Apps Script or locker involved.
