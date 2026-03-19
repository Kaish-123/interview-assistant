# Code and where to replace in browser (one by one)

Open **script.google.com** → your project **CallCalendarScript**. Then do **Step 1** and **Step 2** below.

---

## STEP 1

**In the browser (Apps Script):**  
Click the file **New_EarningIncremental.gs** in the left sidebar (or **EarningILOpt.gs** if that’s where `calculateEarningsIL_Optimized` is).

**What to do:** Select all code in the editor (Ctrl+A / Cmd+A) → Delete → Paste the code below (from the first `/**` to the last `}`) → Save (Ctrl+S / Cmd+S).

---

### Code for Step 1 (paste this entire block)

```javascript
/**
 * Calculate earnings from keyword table (mapping sheet) for calendar sheet.
 * Supports effective-date pricing: same keyword can have multiple prices with
 * "Start Effective Date"; the price used is the one whose Start Effective Date
 * is on or before the event date (latest such date wins).
 * Called by syncCalendarAndCalculateEarnings() after fetchCalendarEventsIL_Optimized().
 *
 * Change sheet/table names below if your spreadsheet uses different names.
 */
var CALENDAR_SHEET_NAME = 'CallCalendarSheet';   // Sheet where calendar events + earnings are written
var KEYWORD_TABLE_NAME = 'KeywordMapping';      // Sheet (table) with Keyword | Price | Start Effective Date

function calculateEarningsIL_Optimized() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CALENDAR_SHEET_NAME);
  const mappingSheet = ss.getSheetByName(KEYWORD_TABLE_NAME);
  if (!sheet || !mappingSheet) return;

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;
  const data = sheet.getRange(2, 1, lastRow, 6).getValues(); // A-F

  const keywordMap = loadKeywordMapWithEffectiveDate_(mappingSheet);

  const startDate = new Date(2024, 0, 1);
  const endDate = new Date(2026, 2, 1);
  const DEFAULT_PRICE = 12500;   // Default for events that don't match any keyword in mapping (12.5k)

  const updatedData = data.map(row => {
    let [eventId, title, start, end, earnings, manualUpdate] = row;

    const eventDate = start instanceof Date ? start : new Date(start);
    if (eventDate < startDate || eventDate > endDate) return row;
    if (manualUpdate && manualUpdate.toString().toLowerCase() === "yes") return row;
    if (earnings) return row; // Skip if already filled

    const updatedEarnings = getPriceForEventDate_(keywordMap, (title || '').toString(), eventDate, DEFAULT_PRICE);
    row[4] = updatedEarnings;
    return row;
  });

  if (updatedData.length) {
    sheet.getRange(2, 1, 1 + updatedData.length, updatedData[0].length).setValues(updatedData);
  }
}

/**
 * Build keyword -> [{price, effectiveDate}, ...] sorted by effectiveDate asc.
 * If column C (Start Effective Date) is missing or blank, treats as effective from 2020-01-01.
 */
function loadKeywordMapWithEffectiveDate_(mappingSheet) {
  const last = Math.max(2, mappingSheet.getLastRow());
  const numCols = mappingSheet.getLastColumn();
  const hasEffectiveDate = numCols >= 3;
  const range = hasEffectiveDate
    ? mappingSheet.getRange(2, 1, last, 3).getValues()
    : mappingSheet.getRange(2, 1, last, 2).getValues();

  const map = {};
  const epochStart = new Date(2020, 0, 1);

  for (const row of range) {
    const kw = (row[0] || '').toString().trim().toLowerCase();
    if (!kw) continue;
    const price = Number(row[1]) || 0;
    let effectiveDate = epochStart;
    if (hasEffectiveDate && row[2]) {
      const d = row[2];
      effectiveDate = d instanceof Date ? d : new Date(d);
      if (isNaN(effectiveDate.getTime())) effectiveDate = epochStart;
    }
    if (!map[kw]) map[kw] = [];
    map[kw].push({ price: price, effectiveDate: effectiveDate });
  }
  for (const k in map) {
    map[k].sort((a, b) => a.effectiveDate.getTime() - b.effectiveDate.getTime());
  }
  return map;
}

/**
 * For a given title and event date, return the applicable price from keywordMap.
 * Uses first matching keyword; for that keyword, uses the latest row where effectiveDate <= eventDate.
 */
function getPriceForEventDate_(keywordMap, title, eventDate, defaultPrice) {
  const lowerTitle = title.toLowerCase();
  for (const keyword in keywordMap) {
    if (!keyword || !lowerTitle.includes(keyword)) continue;
    const entries = keywordMap[keyword];
    let best = null;
    for (let i = 0; i < entries.length; i++) {
      if (entries[i].effectiveDate <= eventDate) best = entries[i];
      else break;
    }
    if (best) return best.price;
  }
  return defaultPrice;
}
```

---

## STEP 2

**In the browser (Apps Script):**  
Click the file **Wrapper_Script.gs.gs** in the left sidebar (or the file that has `syncCalendarAndCalculateEarnings` and `syncAndPrice_Rolling`).

**What to do:** Select all code in the editor (Ctrl+A / Cmd+A) → Delete → Paste the code below (from the first `/**` to the last `);`) → Save (Ctrl+S / Cmd+S).

---

### Code for Step 2 (paste this entire block)

```javascript
/**
 * Wrapper: sync calendar then calculate earnings.
 * Trigger: Calendar – Changed (do not rename this function if trigger is set).
 */
function syncCalendarAndCalculateEarnings() {
  fetchCalendarEventsIL_Optimized();       // Sync calendar data (add/update)
  calculateEarningsIL_Optimized();         // Then calculate earnings for new/updated entries
}

/**************************************************************
 * NAMESPACE-SAFE version (no global constant collisions)
 * - Rolling incremental Calendar sync + keyword-based pricing
 * - Respects "Manual Update" column (Yes/Y/True/1)
 * - Deletes rows for events removed/moved out of window
 **************************************************************/

var CALSYNC = (typeof CALSYNC !== 'undefined') ? CALSYNC : {};

(function(NS) {
  // ---- Config (inside namespace) ----
  NS.SHEET_NAME        = NS.SHEET_NAME || 'CallCalendarSheet';
  NS.MAPPING_SHEET     = NS.MAPPING_SHEET || 'KeywordMapping';
  NS.CAL_ID            = (typeof NS.CAL_ID !== 'undefined') ? NS.CAL_ID : null; // null → primary calendar
  NS.LOOKBACK_DAYS     = (typeof NS.LOOKBACK_DAYS !== 'undefined') ? NS.LOOKBACK_DAYS : 400;
  NS.FUTURE_DAYS       = (typeof NS.FUTURE_DAYS !== 'undefined') ? NS.FUTURE_DAYS : 365;
  NS.DEFAULT_PRICE     = (typeof NS.DEFAULT_PRICE !== 'undefined') ? NS.DEFAULT_PRICE : 12500;  // Default for non-matching events (12.5k)
  NS.MANUAL_YES_VALUES = NS.MANUAL_YES_VALUES || new Set(['yes','y','true','1']);

  // ---- Public entrypoint (call this) ----
  NS.syncAndPrice_Rolling = function() {
    const sheet = getOrCreateSheet_(NS.SHEET_NAME);
    ensureHeaders_(sheet);

    const now   = new Date();
    const start = addDays_(new Date(now), -NS.LOOKBACK_DAYS);
    const end   = addDays_(new Date(now),  NS.FUTURE_DAYS);

    const syncStats   = syncWindow_(sheet, start, end);
    const keywordMap  = loadKeywordMap_();
    const priceStats  = recalcEarningsForWindow_(sheet, keywordMap, start, end);

    Logger.log(JSON.stringify({ syncStats, priceStats }));
  };

  // ---- Installable trigger helper (optional) ----
  NS.installTriggerHourly = function() {
    ScriptApp.newTrigger('syncAndPrice_Rolling').timeBased().everyHours(1).create();
  };

  // ---- Implementations (kept inside IIFE) ----
  function syncWindow_(sheet, start, end) {
    const cal = NS.CAL_ID ? CalendarApp.getCalendarById(NS.CAL_ID) : CalendarApp.getDefaultCalendar();
    const events = cal.getEvents(start, end);

    const currentIds   = new Set();
    const rowsToAppend = [];
    const idToRow      = buildRowIndex_(sheet);

    let updates = 0, inserts = 0, deletes = 0;

    for (const ev of events) {
      const id = ev.getId();
      currentIds.add(id);

      const rowValues = [
        id,
        ev.getTitle() || '',
        ev.getStartTime() || '',
        ev.getEndTime() || '',
        '', '', '' // Earnings/Manual/Selection left for pricing or user
      ];

      const row = idToRow.get(id);
      if (row) {
        sheet.getRange(row, 1, row, 4).setValues([rowValues.slice(0,4)]);
        updates++;
      } else {
        rowsToAppend.push(rowValues);
        inserts++;
      }
    }

    if (rowsToAppend.length) {
      const startRow = sheet.getLastRow() + 1;
      sheet.getRange(startRow, 1, startRow + rowsToAppend.length - 1, rowsToAppend[0].length).setValues(rowsToAppend);
    }

    // Delete rows for events that used to be in window but aren't anymore
    const lastRow = sheet.getLastRow();
    if (lastRow >= 2) {
      const startTimes = sheet.getRange(2, 3, lastRow, 3).getValues(); // C
      const ids        = sheet.getRange(2, 1, lastRow, 1).getValues(); // A

      const rowsToDelete = [];
      for (let i = 0; i < ids.length; i++) {
        const rowNum = i + 2;
        const id = ids[i][0];
        const st = startTimes[i][0];
        if (!id) continue;
        const inWindow = st instanceof Date && st >= start && st <= end;
        if (inWindow && !currentIds.has(id)) {
          rowsToDelete.push(rowNum);
        }
      }
      rowsToDelete.sort((a,b) => b - a).forEach(r => sheet.deleteRow(r));
      deletes = rowsToDelete.length;
    }

    return { inserts, updates, deletes };
  }

  // Effective-date pricing: keyword -> [{price, effectiveDate}, ...] sorted by effectiveDate asc.
  function loadKeywordMap_() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const mappingSheet = ss.getSheetByName(NS.MAPPING_SHEET);
    if (!mappingSheet) return {};
    const last = Math.max(2, mappingSheet.getLastRow());
    const numCols = mappingSheet.getLastColumn();
    const hasEffectiveDate = numCols >= 3;
    const range = hasEffectiveDate
      ? mappingSheet.getRange(2, 1, last, 3).getValues()
      : mappingSheet.getRange(2, 1, last, 2).getValues();
    const map = {};
    const epochStart = new Date(2020, 0, 1);
    for (const row of range) {
      const kw = (row[0] || '').toString().trim().toLowerCase();
      if (!kw) continue;
      const price = Number(row[1]) || 0;
      let effectiveDate = epochStart;
      if (hasEffectiveDate && row[2]) {
        const d = row[2];
        effectiveDate = d instanceof Date ? d : new Date(d);
        if (isNaN(effectiveDate.getTime())) effectiveDate = epochStart;
      }
      if (!map[kw]) map[kw] = [];
      map[kw].push({ price: price, effectiveDate: effectiveDate });
    }
    for (const k in map) {
      map[k].sort((a, b) => a.effectiveDate.getTime() - b.effectiveDate.getTime());
    }
    return map;
  }

  function getPriceForEventDate_(keywordMap, title, eventDate, defaultPrice) {
    const lowerTitle = title.toLowerCase();
    for (const keyword in keywordMap) {
      if (!keyword || !lowerTitle.includes(keyword)) continue;
      const entries = keywordMap[keyword];
      let best = null;
      for (let i = 0; i < entries.length; i++) {
        if (entries[i].effectiveDate <= eventDate) best = entries[i];
        else break;
      }
      if (best) return best.price;
    }
    return defaultPrice;
  }

  function recalcEarningsForWindow_(sheet, keywordMap, start, end) {
    const lastRow = sheet.getLastRow();
    if (lastRow < 2) return { checked: 0, changed: 0 };

    const num = lastRow - 1;
    const block = sheet.getRange(2, 1, lastRow, 6).getValues(); // A..F

    let changed = 0, checked = 0;
    const newEarningsCol = [];

    for (let i = 0; i < num; i++) {
      const row = block[i];
      const title = (row[1] || '').toString();
      const startTime = row[2];
      const currentE = row[4];
      const manual = (row[5] || '').toString().trim().toLowerCase();

      if (!(startTime instanceof Date) || startTime < start || startTime > end) {
        newEarningsCol.push(currentE);
        continue;
      }
      checked++;
      if (NS.MANUAL_YES_VALUES.has(manual)) {
        newEarningsCol.push(currentE); // locked
        continue;
      }

      const eventDate = startTime instanceof Date ? startTime : new Date(startTime);
      const price = getPriceForEventDate_(keywordMap, title, eventDate, NS.DEFAULT_PRICE);
      newEarningsCol.push(price);
      if (Number(currentE) !== price) changed++;
    }

    const twoD = newEarningsCol.map(v => [v]);
    if (twoD.length) sheet.getRange(2, 5, 2 + twoD.length - 1, 5).setValues(twoD); // write E
    return { checked, changed };
  }

  // ---- Helpers ----
  function getOrCreateSheet_(name) {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sh = ss.getSheetByName(name);
    if (!sh) sh = ss.insertSheet(name);
    return sh;
  }

  function ensureHeaders_(sheet) {
    const headers = ["Event ID", "Event Title", "Start Time", "End Time", "Earnings", "Manual Update", "Selection Status"];
    const existing = sheet.getRange(1,1,1,headers.length).getValues()[0];
    const need = headers.some((h,i) => existing[i] !== h);
    if (sheet.getLastRow() === 0 || need) {
      sheet.clear();
      sheet.appendRow(headers);
    }
  }

  function buildRowIndex_(sheet) {
    const map = new Map();
    const last = sheet.getLastRow();
    if (last < 2) return map;
    const ids = sheet.getRange(2,1,last,1).getValues();
    for (let i=0;i<ids.length;i++) {
      const id = ids[i][0];
      if (id) map.set(id, i+2);
    }
    return map;
  }

  function addDays_(d, days) {
    const x = new Date(d);
    x.setDate(x.getDate() + days);
    return x;
  }

})(CALSYNC);

// ---- Thin global wrappers (only these are global) ----
function syncAndPrice_Rolling()       { return CALSYNC.syncAndPrice_Rolling(); }
function installTriggerHourly()       { return CALSYNC.installTriggerHourly(); }
```

---

## Summary

| Step | In browser open this script | Replace with |
|------|----------------------------|--------------|
| 1 | **New_EarningIncremental.gs** (or **EarningILOpt.gs**) | Code block for Step 1 above |
| 2 | **Wrapper_Script.gs.gs** | Code block for Step 2 above |

After both: Save. Then run **calculateEarningsIL_Optimized** once from the Run menu to test.
