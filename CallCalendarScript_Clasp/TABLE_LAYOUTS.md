# How both tables (sheets) look

Only **one** table was changed: the keyword/mapping sheet. The calendar sheet is unchanged.

---

## 1. CallCalendarSheet — **unchanged**

This is the sheet where calendar events and earnings are written. No columns were added or renamed.

| A          | B            | C          | D        | E         | F             | G                |
|------------|--------------|------------|----------|-----------|---------------|------------------|
| Event ID   | Event Title  | Start Time | End Time | Earnings  | Manual Update | Selection Status |
| (id)       | (title)      | (date)     | (date)   | (number)  | yes/blank     | (optional)       |
| …          | …            | …          | …        | …         | …             | …                |

**Nothing to change here.**

---

## 2. KeywordMapping (keyword table) — **changed** (add column C)

This is the sheet that maps keywords to prices. We added one column: **Start Effective Date**.

### Before (old — 2 columns)

| A (Keyword) | B (Price) |
|-------------|-----------|
| consulting  | 5000      |
| support     | 3000      |

### After (new — 3 columns)

| A (Keyword) | B (Price) | **C (Start Effective Date)** |
|-------------|-----------|-----------------------------|
| consulting  | 5000      | *(blank = from beginning)*   |
| consulting  | 6000      | 2025-06-01                  |
| support     | 3000      |                             |
| support     | 3500      | 2025-03-15                  |

**What you do:**

1. In **row 1** of KeywordMapping, add a third column header: **Start Effective Date**.
2. From **row 2** onward:
   - **Column A:** Keyword (same as before).
   - **Column B:** Price (same as before).
   - **Column C:** Start Effective Date (optional). Leave blank for “from the beginning”; or put a date (e.g. `2025-06-01`) so that price applies from that day onward. You can have multiple rows for the same keyword with different prices and dates.

**Summary:** Only the **KeywordMapping** table layout changed (added column C). **CallCalendarSheet** stays as it is.
