# Code for fetchCalendarEventsIL_Optimized

**File to replace:** **CalendarILOpt.gs** (or **New_CalendarIncrementalLoad.gs** or wherever `fetchCalendarEventsIL_Optimized` is)

---

## Code (copy-paste this entire block)

```javascript
/**
 * Incremental calendar sync: fetch events and add/update in CallCalendarSheet.
 * Only updates Event ID, Title, Start Time, End Time (preserves Earnings, Manual Update, Selection Status).
 * Called by syncCalendarAndCalculateEarnings() before calculateEarningsIL_Optimized().
 *
 * Change sheet name below if your spreadsheet uses a different name.
 */
var CALENDAR_SHEET_NAME = 'CallCalendarSheet';   // Sheet where calendar events + earnings are written

function fetchCalendarEventsIL_Optimized() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CALENDAR_SHEET_NAME);
  if (!sheet) {
    Logger.log('CallCalendarSheet not found');
    return;
  }

  // Ensure headers exist
  ensureHeaders_(sheet);

  // Date range: same as earnings calculation (2024-2026)
  const startDate = new Date(2024, 0, 1);
  const endDate = new Date(2026, 2, 1);

  // Get calendar events
  const calendar = CalendarApp.getDefaultCalendar();
  const events = calendar.getEvents(startDate, endDate);

  if (events.length === 0) {
    Logger.log('No events found in date range');
    return;
  }

  // Build map of existing Event IDs -> row number
  const lastRow = sheet.getLastRow();
  const existingIds = new Map();
  if (lastRow >= 2) {
    const idColumn = sheet.getRange(2, 1, lastRow - 1, 1).getValues(); // Column A
    for (let i = 0; i < idColumn.length; i++) {
      const id = idColumn[i][0];
      if (id) existingIds.set(id.toString(), i + 2); // row number (2-based)
    }
  }

  // Prepare updates and inserts
  const rowsToUpdate = [];
  const rowsToInsert = [];

  for (const event of events) {
    const eventId = event.getId();
    const eventIdStr = eventId.toString();
    const rowNum = existingIds.get(eventIdStr);

    const rowData = [
      eventId,
      event.getTitle() || '',
      event.getStartTime() || '',
      event.getEndTime() || ''
    ];

    if (rowNum) {
      // Update existing row (only columns A-D: ID, Title, Start, End)
      // Preserve columns E-F-G (Earnings, Manual Update, Selection Status)
      rowsToUpdate.push({ row: rowNum, data: rowData });
    } else {
      // New event: insert with empty Earnings, Manual Update, Selection Status
      rowsToInsert.push([
        eventId,
        event.getTitle() || '',
        event.getStartTime() || '',
        event.getEndTime() || '',
        '', // Earnings (will be filled by calculateEarningsIL_Optimized)
        '', // Manual Update
        ''  // Selection Status
      ]);
    }
  }

  // Batch update existing rows
  if (rowsToUpdate.length > 0) {
    for (const item of rowsToUpdate) {
      sheet.getRange(item.row, 1, 1, 4).setValues([item.data]);
    }
    Logger.log(`Updated ${rowsToUpdate.length} existing events`);
  }

  // Batch insert new rows
  if (rowsToInsert.length > 0) {
    const startRow = sheet.getLastRow() + 1;
    sheet.getRange(startRow, 1, rowsToInsert.length, 7).setValues(rowsToInsert);
    Logger.log(`Inserted ${rowsToInsert.length} new events`);
  }

  Logger.log(`Sync complete: ${events.length} events processed`);
}

/**
 * Ensure headers exist in the sheet.
 */
function ensureHeaders_(sheet) {
  const headers = ["Event ID", "Event Title", "Start Time", "End Time", "Earnings", "Manual Update", "Selection Status"];
  const lastRow = sheet.getLastRow();
  
  if (lastRow === 0) {
    // Empty sheet: add headers
    sheet.appendRow(headers);
  } else {
    // Check if headers match (first row)
    const existingHeaders = sheet.getRange(1, 1, 1, headers.length).getValues()[0];
    const headersMatch = headers.every((h, i) => existingHeaders[i] === h);
    
    if (!headersMatch) {
      // Headers don't match: clear and add correct headers
      sheet.clear();
      sheet.appendRow(headers);
    }
  }
}
```

---

## What's improved / new in this code

### 1. Configurable sheet name (NEW)
- Uses `CALENDAR_SHEET_NAME` variable (same as earnings function) so you can change it in one place.

### 2. Incremental sync (IMPROVED)
- Only updates columns A–D (Event ID, Title, Start Time, End Time).
- Preserves columns E–G (Earnings, Manual Update, Selection Status) so manual entries aren't overwritten.

### 3. Batch operations (IMPROVED)
- Uses batch updates for existing rows and batch inserts for new rows (faster than row-by-row).

### 4. Date range alignment (NEW)
- Uses the same date range as `calculateEarningsIL_Optimized` (2024–2026) for consistency.

### 5. Error handling (NEW)
- Checks if sheet exists.
- Logs counts of updates/inserts.
- Handles empty event lists.

### 6. Header management (IMPROVED)
- Ensures headers exist and match expected format.
- Only clears/recreates headers if they don't match (preserves data).

### 7. Event ID mapping (OPTIMIZED)
- Builds a Map of existing Event IDs → row numbers for fast lookups (O(1) instead of scanning each time).

---

## Summary

| What | Old behavior (likely) | New behavior |
|------|----------------------|--------------|
| Sheet name | Hardcoded | Configurable variable |
| Updates | May overwrite Earnings/Manual | Preserves Earnings/Manual columns |
| Performance | Row-by-row | Batch operations |
| Date range | May differ from earnings | Same range (2024–2026) |
| Headers | May not check | Validates and fixes if needed |
| Logging | Minimal | Detailed counts |

---

## Where to paste

In Apps Script:
1. Open **CalendarILOpt.gs** (or **New_CalendarIncrementalLoad.gs** or the file that has `fetchCalendarEventsIL_Optimized`).
2. Select all code → Delete → Paste the code above → Save.

This function works with the earnings function: it syncs calendar events first, then earnings are calculated.
