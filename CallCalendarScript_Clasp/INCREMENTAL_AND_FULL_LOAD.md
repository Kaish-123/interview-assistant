# Incremental vs full load — how to run

## 1. Effective-date pricing (already in the script)

- **KeywordMapping** columns: **A** = Keyword, **B** = Price, **C** = Start Effective Date (optional).
- If **C is blank**: that price is used for all events (historical / default rate).
- If **C is set** (e.g. `2026-01-01`): that price applies only for events **on or after** that date.
- For each event the script uses the event’s **Start Time** and picks the latest keyword row whose Start Effective Date is on or before that date. So before the effective date you keep the old amount; from that date you get the new amount.

## 2. Default price for no keyword match

- If an event title matches **no** keyword in KeywordMapping, its earnings are set to **12,500** (configurable as `DEFAULT_PRICE` in `CalculateEarningsIL_Optimized.gs`).

## 3. Incremental load (trigger — save computation)

- **Trigger:** Calendar – Changed → **syncCalendarAndCalculateEarnings**.
- This runs:
  1. **fetchCalendarEventsIL_Optimized()** — syncs calendar to the sheet (add/update Event ID, Title, Start, End; keeps Earnings, Manual Update, Selection Status).
  2. **calculateEarningsIL_Optimized()** — fills **only** rows where **Earnings is empty**; does not overwrite existing earnings or rows with Manual Update = Yes/Y/True/1.
- So on every calendar change you only compute earnings for new/updated rows that don’t have a value yet.

## 4. Full load script (manual — first time or full refresh)

**Use this one script for full load:**

| Script to run | What it does |
|---------------|----------------|
| **runFullLoad** | Syncs all calendar events to the sheet, then recalculates earnings for **every** row in the date range (except Manual Update). Run this manually once after deploy or when you want a full refresh. |

**How to run:** In the Apps Script editor → **Run** dropdown → select **runFullLoad** → click **Run**.

Optionally you can run only the earnings part (no calendar sync):
- **calculateEarningsIL_FullLoad** — recalculates earnings for all rows only (sheet already filled); same as the second step of `runFullLoad`.

## 5. What to deploy (clasp push)

Make sure these are in your Apps Script project (and push them if you use clasp):

- **FetchCalendarEventsIL_Optimized.gs** — calendar sync + `ensureHeaders_`
- **CalculateEarningsIL_Optimized.gs** — `calculateEarningsIL_Optimized`, `calculateEarningsIL_FullLoad`, and effective-date helpers
- **Wrapper_SyncAndEarnings.gs** — `syncCalendarAndCalculateEarnings()` (trigger) + **runFullLoad()** (manual full load)

Do **not** rename `syncCalendarAndCalculateEarnings` or your Calendar – Changed trigger will stop working.

## 6. Bug fixes applied (why the trigger was failing)

- **fetchCalendarEventsIL_Optimized** had wrong `getRange` calls:
  - Updating a single row used `getRange(item.row, 1, 1, 4)` instead of `getRange(item.row, 1, item.row, 4)`.
  - Inserting new rows used `getRange(startRow, 1, rowsToInsert.length, 7)` instead of `getRange(startRow, 1, startRow + rowsToInsert.length - 1, 7)`.
- Building the map of existing IDs used `lastRow - 1` instead of `lastRow`, so the last data row was ignored.

These fixes should resolve the 100% errors on **syncCalendarAndCalculateEarnings**.
