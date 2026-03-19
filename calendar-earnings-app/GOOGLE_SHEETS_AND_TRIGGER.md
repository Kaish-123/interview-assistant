# Replace Apps Script with this app + Google Sheets + automatic trigger

This app can **sync to the same Google Sheet** you used with Apps Script (CallCalendarSheet, KeywordMapping) so **Looker** and other tools keep working. You can then **trigger incremental updates** when the calendar changes, without running the old Apps Script.

---

## 1. One-time setup

### 1.1 Grant Calendar + Sheets access

The app needs **Google Sheets** access as well as Calendar. Re-run auth once so the token includes both:

1. Open the dashboard: **http://localhost:3000**
2. Click **Connect Google (OAuth)** and sign in
3. When asked for permissions, allow **Calendar** and **Sheets** (both are requested together)

### 1.2 Set your Google Sheet in the dashboard

1. Open your **Google Sheet** (the one with CallCalendarSheet and KeywordMapping)
2. Copy the **Spreadsheet ID** from the URL:  
   `https://docs.google.com/spreadsheets/d/ **SPREADSHEET_ID** /edit`
3. In the dashboard, in the **Google Sheet** card:
   - **Spreadsheet ID:** paste the ID
   - **Calendar sheet:** `CallCalendarSheet` (or your sheet name for events)
   - **Mapping sheet:** `KeywordMapping` (or your sheet name for keywords/prices)
4. Click **Save sheet settings**

### 1.3 Run a full load once

Click **Full load** in the dashboard. The app will:

- Fetch events from Google Calendar (date range from the dashboard)
- Read **KeywordMapping** from the Sheet (Keyword, Price, Start Effective Date)
- Compute earnings and write to **CallCalendarSheet** (Event ID, Title, Start, End, Earnings, Manual Update, Selection Status)

Looker (and anything else reading that spreadsheet) will see the same layout as before.

---

## 2. Automatic trigger when calendar changes (incremental)

You have two ways to run an **incremental** update (fetch new/updated events, merge, recalc earnings, write to Sheet) without opening the dashboard.

### Option A: Tiny Apps Script trigger (recommended)

Keep a **minimal** Apps Script that only runs when the calendar changes and **calls this app**:

1. In **Google Apps Script** (script.google.com), create a new project or open the one tied to your sheet.
2. Add a single function and set a trigger:

```javascript
// Only job: call your app’s incremental endpoint when calendar changes.
function onCalendarChange() {
  var url = 'http://YOUR_SERVER/trigger/incremental';  // see below
  var options = { method: 'post', muteHttpExceptions: true };
  UrlFetchApp.fetch(url, options);
}
```

3. Set a trigger: **Edit → Current project’s triggers → Add trigger**  
   - Function: **onCalendarChange**  
   - Event: **Calendar – Changed** (if available) or **Time-driven** (e.g. every 15 minutes)

**What is YOUR_SERVER?**

- **If the app runs on your machine:** use a tunnel (e.g. ngrok: `ngrok http 3000`) and put the HTTPS URL:  
  `https://xxxx.ngrok.io/trigger/incremental`
- **If you deploy the app** (e.g. Cloud Run, Railway, a VPS): use that URL, e.g.  
  `https://your-app.run.app/trigger/incremental`

So: **replace the old Apps Script logic** with this app; the only thing left in Apps Script is this one function that calls your app’s `/trigger/incremental`.

### Option B: Cron / Cloud Scheduler

Run incremental on a schedule instead of “on calendar change”:

- **Cron (Mac/Linux):**  
  `*/15 * * * * curl -X POST http://localhost:3000/trigger/incremental`
- **Google Cloud Scheduler:** create a job that sends `POST https://YOUR_DEPLOYED_APP/trigger/incremental` every 10–15 minutes.

---

## 3. Controlling from Cursor

You can control this app from Cursor by:

- **Starting the app:**  
  `cd calendar-earnings-app && npm run dev`
- **Triggering incremental (when app is running):**  
  `curl -X POST http://localhost:3000/trigger/incremental`
- **Changing settings:** use the dashboard (date range, Spreadsheet ID, sheet names) or edit `data/settings.json`.

So you “replace Apps Script” by:  
(1) using this app as the only place that fetches calendar and computes earnings,  
(2) writing results to the same Google Sheet (CallCalendarSheet + KeywordMapping),  
(3) triggering that logic automatically via `/trigger/incremental` from a small Apps Script or cron.

Looker keeps pointing at the same spreadsheet; no change needed there.
