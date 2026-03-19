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

  ensureHeaders_(sheet);

  const startDate = new Date(2024, 0, 1);
  const endDate = new Date(2026, 2, 1);

  const calendar = CalendarApp.getDefaultCalendar();
  const events = calendar.getEvents(startDate, endDate);

  if (events.length === 0) {
    Logger.log('No events found in date range');
    return;
  }

  // Build map of existing Event IDs -> row number (include all data rows)
  const lastRow = sheet.getLastRow();
  const existingIds = new Map();
  if (lastRow >= 2) {
    const idColumn = sheet.getRange(2, 1, lastRow, 1).getValues();
    for (let i = 0; i < idColumn.length; i++) {
      const id = idColumn[i][0];
      if (id) existingIds.set(id.toString(), i + 2);
    }
  }

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
      rowsToUpdate.push({ row: rowNum, data: rowData });
    } else {
      rowsToInsert.push([
        eventId,
        event.getTitle() || '',
        event.getStartTime() || '',
        event.getEndTime() || '',
        '',
        '',
        ''
      ]);
    }
  }

  if (rowsToUpdate.length > 0) {
    for (const item of rowsToUpdate) {
      sheet.getRange(item.row, 1, item.row, 4).setValues([item.data]);
    }
    Logger.log('Updated ' + rowsToUpdate.length + ' existing events');
  }

  if (rowsToInsert.length > 0) {
    const startRow = sheet.getLastRow() + 1;
    const endRow = startRow + rowsToInsert.length - 1;
    sheet.getRange(startRow, 1, endRow, 7).setValues(rowsToInsert);
    Logger.log('Inserted ' + rowsToInsert.length + ' new events');
  }

  Logger.log('Sync complete: ' + events.length + ' events processed');
}

/**
 * Ensure headers exist in the sheet.
 */
function ensureHeaders_(sheet) {
  const headers = ['Event ID', 'Event Title', 'Start Time', 'End Time', 'Earnings', 'Manual Update', 'Selection Status'];
  const lastRow = sheet.getLastRow();

  if (lastRow === 0) {
    sheet.appendRow(headers);
  } else {
    const existingHeaders = sheet.getRange(1, 1, 1, headers.length).getValues()[0];
    const headersMatch = headers.every(function(h, i) { return existingHeaders[i] === h; });
    if (!headersMatch) {
      sheet.clear();
      sheet.appendRow(headers);
    }
  }
}
