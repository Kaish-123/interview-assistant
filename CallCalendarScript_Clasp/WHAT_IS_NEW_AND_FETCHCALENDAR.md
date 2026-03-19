# What's new in the code + fetchCalendarEventsIL_Optimized

---

## Important: fetchCalendarEventsIL_Optimized() — DO NOT REPLACE

**`fetchCalendarEventsIL_Optimized()` is NOT in the code I provided.** It's a **separate function** that should already exist in your Apps Script project (likely in **CalendarILOpt.gs** or **New_CalendarIncrementalLoad.gs**).

**What to do:**  
- **DO NOT** replace or change `fetchCalendarEventsIL_Optimized()` — leave it as is.  
- It's called in the wrapper (`syncCalendarAndCalculateEarnings`) to sync calendar events to the sheet.  
- Only replace the **earnings calculation** part (`calculateEarningsIL_Optimized`) and the **wrapper** (which calls both functions).

---

## What's NEW in the code I provided (what changed)

### 1. Effective-date pricing (NEW)

**Old behavior:**  
- One price per keyword. If you changed a keyword's price, all events (past and future) would get the new price.

**New behavior:**  
- Multiple prices per keyword with **Start Effective Date**.  
- Events before the effective date keep the old price; events on/after the effective date get the new price.  
- Example: "vamshi" 5000 (blank date) and "vamshi" 8000 from 2026-01-01 → events before 2026-01-01 get 5000, events on/after get 8000.

**Where:**  
- `loadKeywordMapWithEffectiveDate_()` — reads column C (Start Effective Date) from KeywordMapping.  
- `getPriceForEventDate_()` — picks the right price based on event date vs. effective date.

---

### 2. Default price changed: 10k → 12.5k (NEW)

**Old:** Events that don't match any keyword → earnings = **10,000**.  
**New:** Events that don't match any keyword → earnings = **12,500** (12.5k).

**Where:**  
- `DEFAULT_PRICE = 12500` in `CalculateEarningsIL_Optimized.gs`.  
- `NS.DEFAULT_PRICE = 12500` in the wrapper (CALSYNC).

---

### 3. Configurable sheet/table names (NEW)

**Old:** Hardcoded sheet names in the code.  
**New:** Variables at the top so you can change sheet names easily:

```javascript
var CALENDAR_SHEET_NAME = 'CallCalendarSheet';
var KEYWORD_TABLE_NAME = 'KeywordMapping';
```

**Where:**  
- Top of `CalculateEarningsIL_Optimized.gs`.

---

### 4. CALSYNC also uses effective-date pricing (NEW)

**Old:** CALSYNC (`syncAndPrice_Rolling`) used simple keyword → price mapping.  
**New:** CALSYNC also uses effective-date pricing (same logic as `calculateEarningsIL_Optimized`).

**Where:**  
- `loadKeywordMap_()` inside CALSYNC now reads column C and builds effective-date structure.  
- `getPriceForEventDate_()` inside CALSYNC resolves price by event date.

---

## Summary: what you're replacing

| File to replace | What's new |
|-----------------|------------|
| **New_EarningIncremental.gs** (or **EarningILOpt.gs**) | • Effective-date pricing<br>• Default 12.5k (was 10k)<br>• Configurable sheet names<br>• New helpers: `loadKeywordMapWithEffectiveDate_()`, `getPriceForEventDate_()` |
| **Wrapper_Script.gs.gs** | • CALSYNC uses effective-date pricing<br>• Default 12.5k (was 10k)<br>• Same effective-date helpers inside CALSYNC |

**What you're NOT replacing:**  
- `fetchCalendarEventsIL_Optimized()` — leave it as is (it's in another file, e.g. CalendarILOpt.gs).

---

## If fetchCalendarEventsIL_Optimized is missing

If you get an error that `fetchCalendarEventsIL_Optimized` is not found, it means that function doesn't exist in your project. In that case, you need to either:

1. **Find it** in another file (CalendarILOpt.gs, New_CalendarIncrementalLoad.gs, etc.) and make sure that file is in your project.
2. **Or** if it's truly missing, you'd need to implement it (it syncs calendar events to CallCalendarSheet). But based on your triggers working, it should exist somewhere.

The code I provided **only** replaces the earnings calculation logic — it doesn't include the calendar sync function.
