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
3. **Blank Start Effective Date:** If you leave C blank, that row is treated as “effective from the beginning” (1 Jan 2020), so it applies to all past events until a row with a later date takes over.
4. **Example:**
   - Row 1: `consulting` | `5000`  | (blank)           → from 2020-01-01
   - Row 2: `consulting` | `6000`  | `2025-06-01`     → from 2025-06-01  
   - Event on 2025-05-15 → price **5000**.  
   - Event on 2025-06-15 → price **6000**.

### Backward compatibility

- If you **don’t** add column C, the script still works: it uses only A and B and behaves as before (one price per keyword, no effective date).
- If you **add** column C later, existing rows with C blank get “effective from beginning” and new rows with a date get effective-date logic.

---

## Example layout (KeywordMapping)

| Keyword   | Price | Start Effective Date |
|-----------|-------|----------------------|
| consulting| 5000  |                      |
| consulting| 6000  | 2025-06-01           |
| support   | 3000  |                      |
| support   | 3500  | 2025-03-15           |

- Events with “consulting” before 2025-06-01 → 5000; on/after 2025-06-01 → 6000.
- Events with “support” before 2025-03-15 → 3000; on/after 2025-03-15 → 3500.

---

## What was changed in code

1. **CalculateEarningsIL_Optimized.gs** (Path A – 0% errors):  
   - Reads A:B or A:C from KeywordMapping.  
   - Builds “keyword → list of {price, Start Effective Date}” (sorted by date).  
   - For each event, uses the event’s **start date** and picks the **latest** applicable price (Start Effective Date ≤ event date).  
   - Past events keep old price; new events use new price from the effective date.

2. **Wrapper (CALSYNC)** – `loadKeywordMap_` and `recalcEarningsForWindow_`:  
   - Same effective-date structure and same rule: price for event = latest row where Start Effective Date ≤ event date.  
   - So Path B (syncAndPrice_Rolling) also uses effective-date pricing.

No change to trigger names or to CallCalendarSheet layout.
