/**
 * COMBINED FULL LOAD: Calendar + Earnings in one go.
 *
 * 1. Calendar FL: Clears CallCalendarSheet, adds headers, fetches events (2024-01-01 to 2026-05-04),
 *    writes Event ID, Title, Start, End, and blank Earnings, Manual Update, Selection Status.
 * 2. Earnings FL: Applies date-based keyword mapping (KeywordMapping with Start Effective Date),
 *    exception clients (10,000), default 10,000 before 01/01/2026 and 12,500 from 01/01/2026.
 *    Skips rows outside date range (2024-01-01 to 2026-03-10) and Manual Update = Yes.
 *
 * Run this once for a full refresh (e.g. after first deploy or when you want to rebuild everything).
 */
var EXCEPTION_CLIENT_PHRASES = [
  'consultancy name here',
  'acme corp'
];
var EXCEPTION_CLIENT_EARNINGS = 10000;

function runFullLoadCalendarAndEarnings_DateBased() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('CallCalendarSheet');
  var mappingSheet = ss.getSheetByName('KeywordMapping');
  if (!sheet || !mappingSheet) return;

  // —— 1. Calendar full load ——
  sheet.clearContents();
  var headers = ['Event ID', 'Event Title', 'Start Time', 'End Time', 'Earnings', 'Manual Update', 'Selection Status'];
  sheet.appendRow(headers);

  var calendar = CalendarApp.getDefaultCalendar();
  var calendarStart = new Date(2024, 0, 1);
  var calendarEnd = new Date(2026, 4, 4);
  var events = calendar.getEvents(calendarStart, calendarEnd);

  if (!events || events.length === 0) return;

  var data = [];
  for (var i = 0; i < events.length; i++) {
    var ev = events[i];
    data.push([
      ev.getId(),
      ev.getTitle() || '',
      ev.getStartTime() || null,
      ev.getEndTime() || null,
      '', '', ''
    ]);
  }

  // —— 2. Apply earnings in memory (same logic as calculateEarningsFL_DateBased) ——
  var keywordMap = buildKeywordMapWithEffectiveDate_(mappingSheet);
  var earningsStart = new Date(2024, 0, 1);
  var earningsEnd = new Date(2026, 2, 10);

  for (var r = 0; r < data.length; r++) {
    var row = data[r];
    var title = (row[1] || '').toString();
    var start = row[2];
    var manualUpdate = (row[5] || '').toString().toLowerCase().trim();
    var eventDate = start instanceof Date ? start : new Date(start);

    if (eventDate < earningsStart || eventDate > earningsEnd) continue;
    if (manualUpdate === 'yes') continue;

    row[4] = getEarningsForDate_(keywordMap, title, eventDate);
  }

  // —— 3. Write once ——
  sheet.getRange(2, 1, data.length, 7).setValues(data);
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

function getEarningsForDate_(keywordMap, title, eventDate) {
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
  for (var e = 0; e < EXCEPTION_CLIENT_PHRASES.length; e++) {
    var phrase = (EXCEPTION_CLIENT_PHRASES[e] || '').toString().trim().toLowerCase();
    if (phrase && lowerTitle.indexOf(phrase) !== -1) return EXCEPTION_CLIENT_EARNINGS;
  }
  var defaultCutoff = new Date(2026, 0, 1);
  return eventDate >= defaultCutoff ? 12500 : 10000;
}
