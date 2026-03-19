# Push / replace changes — one by one (with script names)

Do this in **Google Apps Script** (script.google.com → open **CallCalendarScript**).

---

## Step 1 — Earnings script

| Item | Value |
|------|--------|
| **In Apps Script, open this file:** | **New_EarningIncremental.gs** (or **EarningILOpt.gs** if that’s where `calculateEarningsIL_Optimized` lives) |
| **Replace with code from (on your laptop):** | `CallCalendarScript_Backup/CalculateEarningsIL_Optimized.gs` **or** `CallCalendarScript_Clasp/CalculateEarningsIL_Optimized.gs` |
| **What to do:** | In Apps Script: select **all** code in that file → delete → open the file above on your laptop → copy **all** → paste into Apps Script → **Save** (Ctrl+S / Cmd+S) |

---

## Step 2 — Wrapper + CALSYNC script

| Item | Value |
|------|--------|
| **In Apps Script, open this file:** | **Wrapper_Script.gs.gs** (or the file that has `syncCalendarAndCalculateEarnings` and `syncAndPrice_Rolling`) |
| **Replace with code from (on your laptop):** | `CallCalendarScript_Backup/Wrapper_SyncAndEarnings.gs` |
| **What to do:** | In Apps Script: select **all** code in that file → delete → open the file above on your laptop → copy **all** → paste into Apps Script → **Save** (Ctrl+S / Cmd+S) |

---

## If you use clasp (command line)

From the folder where you ran `clasp clone` (and where your `.gs` files are):

```bash
clasp push
```

That pushes **all** changed `.gs` files. Make sure that folder has the updated:
- **CalculateEarningsIL_Optimized.gs** (or the file that contains it)
- **Wrapper_Script.gs.gs** (or the file that contains the wrapper + CALSYNC)

with the same **names** as in Apps Script. If your local file names differ, rename them to match Apps Script before `clasp push`, or copy the content from Backup into the correct local files.

---

## Checklist (copy and tick)

- [ ] **Step 1:** Replaced **New_EarningIncremental.gs** (or **EarningILOpt.gs**) with `CalculateEarningsIL_Optimized.gs` from Backup/Clasp folder. Saved.
- [ ] **Step 2:** Replaced **Wrapper_Script.gs.gs** with `Wrapper_SyncAndEarnings.gs` from Backup folder. Saved.
- [ ] **Optional (clasp):** Ran `clasp push` from the clasp project folder.

After that, run **calculateEarningsIL_Optimized** once from the Run menu to test.
