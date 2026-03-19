# What to do after updating KeywordMapping

Your KeywordMapping sheet is set up correctly:
- **Column A:** Keyword  
- **Column B:** Earnings (the script uses this as the price)  
- **Column C:** Start Effective Date  

Example: "vamshi" 5000 (blank) and "vamshi" 8000 from 2026-01-01 will give events before that date 5000 and from that date 8000.

---

## 1. Deploy the updated script (if not done yet)

**Option A – You use clasp (local project)**  
From the folder where you ran `clasp clone`:
```bash
cd /path/to/your/clasp/project
clasp push
```

**Option B – You edit in the browser**  
1. Open your project at [script.google.com](https://script.google.com).  
2. Open **CalculateEarningsIL_Optimized.gs**.  
3. Replace its **entire** content with the version from `CallCalendarScript_Backup/CalculateEarningsIL_Optimized.gs` (or from `CallCalendarScript_Clasp/CalculateEarningsIL_Optimized.gs`).  
4. If you use the other trigger (**syncAndPrice_Rolling**), also replace the wrapper file content with `CallCalendarScript_Backup/Wrapper_SyncAndEarnings.gs`.  
5. Save (Ctrl+S / Cmd+S).

---

## 2. Test once

1. In Apps Script, open the **Run** dropdown and select **calculateEarningsIL_Optimized**.  
2. Click **Run**.  
3. Check **CallCalendarSheet**:  
   - Events with "vamshi" in the title **before** 2026-01-01 should have earnings **5000**.  
   - Events with "vamshi" **on or after** 2026-01-01 should have earnings **8000**.  

If you use triggers, you can instead change something on the calendar and wait for the trigger to run, then check the sheet.

---

## 3. Optional: separator row "----------"

Row 17 with **----------** in Keyword and **0** in Earnings is treated as a real keyword: any event whose title contains "----------" would get earnings 0.  

- If you don’t want that, **delete that row** or move it below the data.  
- If you’re fine with it, leave it as is.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Deploy: `clasp push` or paste updated `.gs` in the browser and save. |
| 2 | Test: Run **calculateEarningsIL_Optimized** and check CallCalendarSheet. |
| 3 | Optional: Remove or move the "----------" row if you don’t want it as a keyword. |

After that, the script will use your new table as-is; no further table changes needed unless you add more keywords or effective dates.
