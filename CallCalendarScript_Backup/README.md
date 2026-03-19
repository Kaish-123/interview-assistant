# CallCalendarScript — Backup & Trigger Summary

**Date:** Feb 2, 2026  
**Project:** CallCalendarScript (Google Apps Script)

---

## 1. Which schedule is actually running?

From your **Triggers** page you have **2 active triggers**, both **event-driven** (not time-based):

| Function | Event | Last run (example) | Error rate |
|----------|--------|---------------------|------------|
| `syncAndPrice_Rolling` | **Calendar – Changed** | Feb 2, 2026 10:02:42 PM | 1.87% |
| `syncCalendarAndCalculateEarnings` | **Calendar – Changed** | Feb 2, 2026 10:02:41 PM | **0%** |

- **Neither** runs on a fixed schedule (no hourly/daily). Both run **whenever the calendar is changed** (add/edit/delete event).
- The one with **0% errors** is `syncCalendarAndCalculateEarnings` (it calls `fetchCalendarEventsIL_Optimized` then `calculateEarningsIL_Optimized`).
- So the flow that’s “working fine” in terms of no errors is: **Calendar change → `syncCalendarAndCalculateEarnings`**.

---

## 2. Quick way to confirm which is working

1. **Triggers (you already have this)**  
   Apps Script → left sidebar → **Triggers** (clock icon). You’ll see both functions and their events.

2. **Execution log**  
   Apps Script → left sidebar → **Executions**. After you change something on the calendar, check which function ran and whether it succeeded (green) or failed (red).

3. **Optional: one-line “who ran” in the sheet**  
   If you want to see in the sheet itself which path last ran, we can add a single line that writes e.g. `"Last run: syncCalendarAndCalculateEarnings"` and the timestamp to a fixed cell (e.g. on a “Config” sheet or row). Then you can glance at the sheet to confirm. Say if you want this and where to put it.

---

## 3. Keeping triggers unchanged during enhancements

- **Do not** add/remove/change triggers until you’re done testing.
- Do all changes in **new or duplicate .gs files** (e.g. `New_EarningIncremental_v2.gs`), or in copies of existing files.
- Leave the **function names** that the triggers call exactly as they are:
  - `syncCalendarAndCalculateEarnings`
  - `syncAndPrice_Rolling`
- If you want to test a new implementation:
  - Implement it as a **new function** (e.g. `calculateEarningsIL_Optimized_v2`).
  - When ready, **inside** `syncCalendarAndCalculateEarnings` (or the wrapper), switch the call from the old function to the new one and save. Triggers stay the same; only the code they run changes.

---

## 4. Backup: what’s in this folder

This folder is a **local backup** of the script code you shared:

- `Wrapper_SyncAndEarnings.gs` — `syncCalendarAndCalculateEarnings` + CALSYNC namespace (`syncAndPrice_Rolling`, etc.)
- `CalculateEarningsIL_Optimized.gs` — `calculateEarningsIL_Optimized`
- `README.md` — this file

Small range/write fixes were applied in the backup so the code runs correctly (e.g. correct row ranges for `setValues`); the business logic is unchanged.

**You still need to backup what’s only in Apps Script:**

1. **All other .gs files** in the project (e.g. `CalendarILOpt.gs`, `EarningILOpt.gs`, `New_CalendarIncremental.gs`, `New_EarningFullLoad.gs`, etc.): open each in script.google.com, copy full contents, and save into this folder as `CalendarILOpt.gs`, etc.
2. **Trigger setup:** In Triggers, note (or screenshot) which triggers exist and which function each runs. You already have 2 × Calendar–Changed.
3. **Version history (optional):** In Apps Script, File → Version history → See version history, and optionally “Name current version” before big changes (e.g. “Before earnings enhancement”).

---

## 5. Can an assistant “take over” the browser and test?

**No.** No one can access your Google account or your laptop’s browser from here. Everything runs in **script.google.com** in your browser; there is no local project for Apps Script unless you use **clasp**.

What we can do:

- **Here:** Edit and prepare all code (new logic, bug fixes, new functions), and give you step-by-step instructions and exact code blocks to paste and run.
- **You:** Paste into Apps Script, run once (Run → choose function), check Executions and the sheet. If something breaks, you still have this backup and can revert.

If you want to develop in VS Code and push to Apps Script, you can use **clasp** (Command Line Apps Script Projects): `npm install -g @google/clasp`, then `clasp clone <scriptId>` to pull the project and `clasp push` to deploy. Then I can work on the local files and you push after testing.

---

## 6. Next step

Your triggers are clear; you have a local backup of the main pieces; triggers can stay the same while you enhance. When you’re ready, describe the **enhancement** you want (e.g. “only update earnings for rows where title contains X” or “new keyword rule”), and we can implement it in a new function and wire it in without touching the trigger setup.
