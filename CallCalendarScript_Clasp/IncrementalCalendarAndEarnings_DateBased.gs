/**
 * COMBINED INCREMENTAL: Calendar merge + Earnings in one go.
 *
 * 1. Calendar IL: One read of existing sheet, merge with calendar events by Event ID.
 *    New events → add row with blank E,F,G. Existing → update A–D, keep E,F,G. Deleted in calendar → remove row.
 * 2. Sort merged data by Start Time (date/time) ASC.
 * 3. Apply date-based earnings (KeywordMapping + Start Effective Date, exception clients, 10k/12.5k default)
 *    for rows in date range (2024-01-01 to 2026-05-04 end-of-day) and not Manual Update = Yes.
 * 4. One write to sheet; clear trailing rows if result is shorter.
 *
 * Use from trigger (e.g. Calendar – Changed) or run manually. No sheet clear; minimal reads/writes.
 */
var EXCEPTION_CLIENT_PHRASES_IL = [
  'consultancy name here',
  'acme corp'
];
var EXCEPTION_CLIENT_EARNINGS_IL = 10000;

function runIncrementalCalendarAndEarnings_DateBased() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('CallCalendarSheet');
  var mappingSheet = ss.getSheetByName('KeywordMapping');
  if (!sheet || !mappingSheet) return;

  ensureHeaders_(sheet);

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
  var calendarStart = new Date(2024, 0, 1);
  var calendarEnd = new Date(2026, 4, 4);
  var events = calendar.getEvents(calendarStart, calendarEnd);
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

  sortByStartTime_(merged);

  var keywordMap = buildKeywordMapWithEffectiveDate_(mappingSheet);
  var earningsStart = new Date(2024, 0, 1);
  // End of day so events ON 3/10 and through calendar range get earnings (was midnight 3/10, which excluded 3/10 21:00 and 3/11+)
  var earningsEnd = new Date(2026, 4, 4, 23, 59, 59, 999);

  for (var r = 0; r < merged.length; r++) {
    var row = merged[r];
    var title = (row[1] || '').toString();
    var start = row[2];
    var manualUpdate = (row[5] || '').toString().toLowerCase().trim();
    
    // Ensure eventDate is a proper Date object
    var eventDate = null;
    if (start instanceof Date) {
      eventDate = new Date(start.getTime());
    } else if (start) {
      eventDate = new Date(start);
    }

    // Skip if Manual Update = Yes (preserve existing earnings)
    if (manualUpdate === 'yes') continue;

    // Clear earnings for invalid dates or outside earnings date range
    if (!eventDate || isNaN(eventDate.getTime()) || eventDate < earningsStart || eventDate > earningsEnd) {
      row[4] = '';
      continue;
    }

    // Recalculate earnings using current rules (12,500 default from Jan 2026)
    row[4] = getEarningsForDateIL_(keywordMap, title, eventDate);
  }

  var numRows = merged.length;
  var numCols = 7;
  sheet.getRange(2, 1, numRows, numCols).setValues(merged);

  if (lastRow > 1 && numRows < lastRow - 1) {
    var clearFromRow = 2 + numRows;
    var rowsToClear = lastRow - clearFromRow + 1;
    sheet.getRange(clearFromRow, 1, rowsToClear, numCols).clearContent();
  }
}

function ensureHeaders_(sheet) {
  var headers = ['Event ID', 'Event Title', 'Start Time', 'End Time', 'Earnings', 'Manual Update', 'Selection Status'];
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
}

function sortByStartTime_(rows) {
  rows.sort(function(a, b) {
    var t1 = a[2] ? (a[2].getTime ? a[2].getTime() : new Date(a[2]).getTime()) : 0;
    var t2 = b[2] ? (b[2].getTime ? b[2].getTime() : new Date(b[2]).getTime()) : 0;
    return t1 - t2;
  });
}

function buildKeywordMapWithEffectiveDate_(mappingSheet) {
  var last = Math.max(2, mappingSheet.getLastRow());
  var numCols = mappingSheet.getLastColumn();
  var hasDateCol = numCols >= 3;
  var range = hasDateCol
    ? mappingSheet.getRange(2, 1, last, 3).getValues()
    : mappingSheet.getRange(2, 1, last, 2).getValues();

  var map = {};
  var veryOldDate = new Date(1970, 0, 1);

  for (var i = 0; i < range.length; i++) {
    var row = range[i];
    var kw = (row[0] || '').toString().trim().toLowerCase();
    if (!kw || kw === '----------') continue;

    var earningsVal = row[1];
    var price = typeof earningsVal === 'number' && !isNaN(earningsVal)
      ? earningsVal
      : parseFloat(String(earningsVal).replace(/,/g, '')) || 0;

    var effectiveDate = veryOldDate;
    if (hasDateCol && row[2]) {
      var d = row[2];
      effectiveDate = d instanceof Date ? d : new Date(d);
      if (isNaN(effectiveDate.getTime())) effectiveDate = veryOldDate;
    }

    if (!map[kw]) map[kw] = [];
    map[kw].push({ effectiveDate: effectiveDate, earnings: price });
  }

  for (var k in map) {
    map[k].sort(function(a, b) { return a.effectiveDate.getTime() - b.effectiveDate.getTime(); });
  }
  return map;
}

function getEarningsForDateIL_(keywordMap, title, eventDate) {
  var lowerTitle = title.toLowerCase();
  for (var keyword in keywordMap) {
    if (!keyword || lowerTitle.indexOf(keyword) === -1) continue;
    var entries = keywordMap[keyword];
    var best = null;
    for (var j = 0; j < entries.length; j++) {
      if (entries[j].effectiveDate <= eventDate) best = entries[j];
      else break;
    }
    if (best) return best.earnings;
  }
  for (var e = 0; e < EXCEPTION_CLIENT_PHRASES_IL.length; e++) {
    var phrase = (EXCEPTION_CLIENT_PHRASES_IL[e] || '').toString().trim().toLowerCase();
    if (phrase && lowerTitle.indexOf(phrase) !== -1) return EXCEPTION_CLIENT_EARNINGS_IL;
  }
  // Default: 12,500 from Jan 1, 2026 onwards, 10,000 before
  var defaultCutoff = new Date(2026, 0, 1);
  defaultCutoff.setHours(0, 0, 0, 0);
  var normalizedEventDate = new Date(eventDate);
  normalizedEventDate.setHours(0, 0, 0, 0);
  return normalizedEventDate >= defaultCutoff ? 12500 : 10000;
}