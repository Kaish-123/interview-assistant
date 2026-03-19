/**
 * INCREMENTAL (IL) calendar sync — counterpart to fetchCalendarFLEventsOptimized.
 * Does NOT clear the sheet. One read, merge in memory, one write.
 * Preserves Earnings, Manual Update, Selection Status for existing events; new events get blank E,F,G.
 * Removes rows for events no longer in the calendar.
 * Run this from a trigger or manually; no wrapper required.
 */
function fetchCalendarILEventsOptimized() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('CallCalendarSheet');
  if (!sheet) return;

  var startDate = new Date(2024, 0, 1);
  var endDate = new Date(2026, 4, 4);
  var headers = ['Event ID', 'Event Title', 'Start Time', 'End Time', 'Earnings', 'Manual Update', 'Selection Status'];

  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, 7).setValues([headers]);
  }

  var lastRow = sheet.getLastRow();
  var existingMap = {};
  if (lastRow >= 2) {
    var existingData = sheet.getRange(2, 1, lastRow, 7).getValues();
    for (var i = 0; i < existingData.length; i++) {
      var id = (existingData[i][0] || '').toString();
      if (id) existingMap[id] = existingData[i];
    }
  }

  var calendar = CalendarApp.getDefaultCalendar();
  var events = calendar.getEvents(startDate, endDate);
  if (!events || events.length === 0) return;

  var merged = [];
  for (var e = 0; e < events.length; e++) {
    var ev = events[e];
    var id = (ev.getId() || '').toString();
    var title = ev.getTitle() || '';
    var start = ev.getStartTime() || null;
    var end = ev.getEndTime() || null;
    var row = existingMap[id];
    if (row) {
      merged.push([id, title, start, end, row[4], row[5], row[6]]);
    } else {
      merged.push([id, title, start, end, '', '', '']);
    }
  }

  merged.sort(function(a, b) {
    var t1 = a[2] ? (a[2].getTime ? a[2].getTime() : new Date(a[2]).getTime()) : 0;
    var t2 = b[2] ? (b[2].getTime ? b[2].getTime() : new Date(b[2]).getTime()) : 0;
    return t1 - t2;
  });

  var numRows = merged.length;
  var numCols = 7;
  sheet.getRange(2, 1, numRows, numCols).setValues(merged);

  if (lastRow > 1 && numRows < lastRow - 1) {
    var clearFromRow = 2 + numRows;
    var rowsToClear = lastRow - clearFromRow + 1;
    sheet.getRange(clearFromRow, 1, rowsToClear, numCols).clearContent();
  }
}
