# End-to-end: Google Calendar → Sheet → Earnings

This folder is the **complete system** for syncing your Google Calendar into a Google Sheet and calculating earnings per event using a keyword table. Everything is here so you (or an AI assistant) can run or change it from one place.

**When you give a command** (e.g. to Cursor or another AI): say *"Use the CallCalendarScript_Clasp folder; the full calendar → sheet → earnings system is there."* Then ask for what you want (e.g. add a column, change default price, new trigger). The assistant can handle it from this codebase.

---

## What it does

1. **Google Calendar** (your default calendar) → events are synced into a sheet.
2. **CallCalendarSheet** holds: Event ID, Title, Start/End Time, Earnings, Manual Update, Selection Status.
3. **KeywordMapping** sheet: you list keywords (e.g. names) and prices; optional **Start Effective Date** so you can change a person’s rate from a specific date (earlier events keep the old rate).
4. **Earnings** are calculated from event titles: first matching keyword + effective date → price; no match → default **12,500**.
5. **Trigger (Calendar – Changed)** runs incremental sync + earnings (only fills empty earnings).
6. **Manual “full load”** runs sync + full earnings recalc when you want (e.g. first time or after changing keywords).

---

## What you need

- A **Google account**.
- One **Google Sheet** (new or existing) that will hold the data and script.

---

## Setup (from zero)

### Step 1: Create or open a Google Sheet

- Go to [sheets.google.com](https://sheets.google.com) and create a new spreadsheet (or open the one you want to use).

### Step 2: Open Apps Script

- Menu: **Extensions** → **Apps Script**.
- You get a new script project tied to this sheet. Delete any sample code in `Code.gs`.

### Step 3: Add the script files

You need **four** files in the project. Create each file (click **+** next to Files → **Script**) and paste the contents from this folder:

| File name in Apps Script | Copy from (this folder) |
|--------------------------|---------------------------|
| `Setup.gs` | `Setup.gs` |
| `FetchCalendarEventsIL_Optimized.gs` | `FetchCalendarEventsIL_Optimized.gs` |
| `CalculateEarningsIL_Optimized.gs` | `CalculateEarningsIL_Optimized.gs` |
| `Wrapper_SyncAndEarnings.gs` | `Wrapper_SyncAndEarnings.gs` |

If you use **clasp** instead: clone/push this folder so the same four files are in your Apps Script project.

### Step 4: One-time setup of the sheet

- In Apps Script: **Run** → select **setupSpreadsheet** → **Run**.
- First run will ask for permissions (view/edit your Sheet, view calendar). Approve.
- The spreadsheet will get two sheets (if missing) with correct headers:
  - **CallCalendarSheet** – Event ID, Event Title, Start Time, End Time, Earnings, Manual Update, Selection Status.
  - **KeywordMapping** – Keyword, Price, Start Effective Date.

### Step 5: Add your keywords

- In the Google Sheet, open the **KeywordMapping** tab.
- From row 2 onward, add one row per keyword (e.g. name or phrase that appears in calendar event titles):
  - **A** = Keyword (e.g. `Ram`, `vamshi`).
  - **B** = Price (e.g. `9750`, `8000`).
  - **C** = Start Effective Date (optional). Leave blank for “always”; set e.g. `2026-01-01` to apply this price only from that date onward. Older events keep the previous price.

### Step 6: First full load

- In Apps Script: **Run** → select **runFullLoad** → **Run**.
- This syncs your calendar into CallCalendarSheet and fills earnings for all events. Check the **CallCalendarSheet** tab.

### Step 7: Automatic updates (incremental)

- In Apps Script: **Triggers** (clock icon) → **Add Trigger**.
  - Function: **syncCalendarAndCalculateEarnings**
  - Event: **Calendar – Changed**
  - Save.
- From now on, when you change the calendar, the script will sync and fill earnings only for new/empty rows (incremental).

---

## Scripts you can run (reference)

| Run this | When |
|----------|------|
| **setupSpreadsheet** | Once, on a new sheet, to create tabs and headers. |
| **runFullLoad** | Manually when you want a full sync + full earnings recalc (e.g. first time or after changing KeywordMapping). |
| **syncCalendarAndCalculateEarnings** | Used by the trigger; also runnable manually for an incremental sync + earnings. |
| **calculateEarningsIL_FullLoad** | Manual: recalc all earnings only (no calendar sync). |
| **fetchCalendarEventsIL_Optimized** | Manual: sync calendar only (no earnings). |
| **calculateEarningsIL_Optimized** | Manual: fill earnings only for rows that are still empty. |

---

## Changing the system later

- All logic lives in the four `.gs` files above.
- To change date range, default price, or sheet names: edit the variables at the top of `CalculateEarningsIL_Optimized.gs` and `FetchCalendarEventsIL_Optimized.gs`.
- When you ask an AI (or work yourself): **“Use the CallCalendarScript_Clasp folder; everything for calendar → sheet → earnings is there.”** Then you can say e.g. “add a new column”, “change default price”, “add a new trigger”, and the assistant can do it from this codebase.

---

## File list (this folder)

- **Setup.gs** – One-time sheet/tab and header setup.
- **FetchCalendarEventsIL_Optimized.gs** – Calendar sync into CallCalendarSheet.
- **CalculateEarningsIL_Optimized.gs** – Earnings from KeywordMapping (effective-date + default 12.5k), incremental + full load.
- **Wrapper_SyncAndEarnings.gs** – Trigger entry (syncCalendarAndCalculateEarnings) + manual full load (runFullLoad).
- **README_END_TO_END.md** – This file.
- **INCREMENTAL_AND_FULL_LOAD.md** – Details on incremental vs full load and effective-date behaviour.

You can use this package directly: create one sheet, add these scripts, run setup then runFullLoad, then set the trigger. When you give a command later (e.g. to an AI), point it at this folder and it can take care of the rest from here.
