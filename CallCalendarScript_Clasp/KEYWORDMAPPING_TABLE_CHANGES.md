# KeywordMapping sheet: table change for effective-date pricing

## What you asked for

- When you add a **new price** for a keyword (or change price for an existing keyword), you can set a **Start Effective Date**.
- From that date onward, the **new price** is used for earnings.
- For events **before** that date, the **previous price** stays (so past calculations don’t change).

---

## Table change: add one column

**Sheet:** `KeywordMapping`

| Column | Header (row 1)        | Description |
|--------|------------------------|-------------|
| A      | Keyword                | Same as now. |
| B      | Price                  | Same as now. |
| **C**  | **Start Effective Date** | **NEW.** Date from which this price applies. Optional. |

### Rules

1. **Header:** In row 1, add (or rename) the third column to **Start Effective Date**.
2. **One row per price period:** You can have **multiple rows** for the same keyword with different prices and different Start Effective Date.  
   - The script uses the row whose Start Effective Date is **on or before** the event date and is the **latest** (most recent).
3. **Blank Start Effective Date:** If you leave C blank, that row is treated as "effective from the beginning" (1 Jan 2020), so it applies to all past events until a row with a later date takes over.
4. **Example:**
   - Row 1: `consulting` | `5000`  | (blank)           → from 2020-01-01
   - Row 2: `consulting` | `6000`  | `2025-06-01`     → from 2025-06-01  
   - Event on 2025-05-15 → price **5000**.  
   - Event on 2025-06-15 → price **6000**.

### Backward compatibility

- If you **don’t** add column C, the script still works: it uses only A and B and behaves as before (one price per keyword, no effective date).
- If you **add** column C later, existing rows with C blank get "effective from beginning" and new rows with a date get effective-date logic.

---

## Example layout (KeywordMapping)

| Keyword   | Price | Start Effective Date |
|-----------|-------|----------------------|
| consulting| 5000  |                      |
| consulting| 6000  | 2025-06-01           |
| support   | 3000  |                      |
| support   | 3500  | 2025-03-15           |

- Events with "consulting" before 2025-06-01 → 5000; on/after 2025-06-01 → 6000.
- Events with "support" before 2025-03-15 → 3000; on/after 2025-03-15 → 3500.

---

## Deploying the code

1. **In your Google Sheet:** Add column C to **KeywordMapping** with header **Start Effective Date** (see above).
2. **In Apps Script:** Replace (or add) the updated files:
   - **CalculateEarningsIL_Optimized.gs** — use the version from `CallCalendarScript_Backup/` or this folder (effective-date logic).
   - **Wrapper (CALSYNC):** If your trigger uses `syncAndPrice_Rolling`, replace the wrapper file content with `CallCalendarScript_Backup/Wrapper_SyncAndEarnings.gs` so CALSYNC also uses effective-date pricing.
3. **If using clasp:** Copy the updated `.gs` files into the folder where you ran `clasp clone`, then run `clasp push`.

Triggers stay the same; only the code and the KeywordMapping layout change.
