/**
 * Date-based earnings from KeywordMapping for CallCalendarSheet.
 *
 * KEYWORD MAPPING (3 columns):
 *   A = Keyword, B = Earnings, C = Start Effective Date (optional)
 *
 * RULES:
 * - If a keyword has only one row (no C or empty C): that earnings apply to all call dates.
 * - If a keyword has multiple rows (e.g. second row with C = 2026-01-01):
 *   - For calls ON or AFTER that Start Effective Date → use the NEW earnings from that row.
 *   - For calls BEFORE that date → use the earnings from the previous row (no-date or earlier row).
 * - First matching keyword in the title wins (same as before).
 * - Default earnings when no keyword matches: 10,000 before 01/01/2026; 12,500 from 01/01/2026 onward.
 *
 * EXCEPTION CLIENTS: If the call title contains any phrase below (case-insensitive) and no keyword
 * matches, earnings are always 10,000 (ignoring the 12,500 default from 01/01/26). Add your client's
 * company name or any text that always appears in their slot invites.
 */
var EXCEPTION_CLIENT_PHRASES = [
  'consultancy name here',   // Replace with your client's name or a phrase from their invites
  'acme corp'                // Add more phrases if needed (e.g. calendar sender name)
];
var EXCEPTION_CLIENT_EARNINGS = 10000;

function calculateEarningsFL_DateBased() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('CallCalendarSheet');
  const mappingSheet = ss.getSheetByName('KeywordMapping');

  if (!sheet || !mappingSheet) return;

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  // Exclude last row (e.g. totals row), same as original script
  const data = sheet.getRange(2, 1, lastRow - 1, 6).getValues();
  const keywordMap = buildKeywordMapWithEffectiveDate_(mappingSheet);

  const startDate = new Date(2024, 0, 1);
  const endDate = new Date(2026, 2, 10);

  const updatedData = data.map(function(row) {
    let eventId = row[0], title = row[1], start = row[2], end = row[3], earnings = row[4], manualUpdate = row[5];

    const eventDate = start instanceof Date ? start : new Date(start);
    if (eventDate < startDate || eventDate > endDate) return row;
    if (manualUpdate && (manualUpdate + '').toLowerCase().trim() === 'yes') return row;

    let updatedEarnings = getEarningsForDate_(keywordMap, (title || '') + '', eventDate);
    row[4] = updatedEarnings;
    return row;
  });

  // getRange(row, column, numRows, numColumns) — numRows must match data length
  if (updatedData.length > 0) {
    sheet.getRange(2, 1, updatedData.length, updatedData[0].length).setValues(updatedData);
  }
}

/**
 * Build map: keyword (lowercase) -> array of { effectiveDate: Date, earnings: number }
 * sorted by effectiveDate ascending.
 * - Empty or missing "Start Effective Date" (column C) = treat as very old date so it applies to all past calls.
 */
function buildKeywordMapWithEffectiveDate_(mappingSheet) {
  const last = Math.max(2, mappingSheet.getLastRow());
  const numCols = mappingSheet.getLastColumn();
  const hasDateCol = numCols >= 3;
  const range = hasDateCol
    ? mappingSheet.getRange(2, 1, last, 3).getValues()
    : mappingSheet.getRange(2, 1, last, 2).getValues();

  const map = {};
  const veryOldDate = new Date(1970, 0, 1);

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

/**
 * For a given title and event date, return the applicable earnings.
 * Uses the first keyword that appears in the title; for that keyword, uses the row
 * with the latest Start Effective Date that is on or before the event date.
 * When no keyword matches: 10,000 before 01/01/2026; 12,500 from 01/01/2026 onward.
 * Exception: if title contains any EXCEPTION_CLIENT_PHRASES, return EXCEPTION_CLIENT_EARNINGS (10,000).
 */
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
  // Exception client: title contains a phrase that identifies this consultancy → always 10,000
  for (var e = 0; e < EXCEPTION_CLIENT_PHRASES.length; e++) {
    var phrase = (EXCEPTION_CLIENT_PHRASES[e] || '').toString().trim().toLowerCase();
    if (phrase && lowerTitle.indexOf(phrase) !== -1) return EXCEPTION_CLIENT_EARNINGS;
  }
  // Default: 12,500 from 01/01/2026 onward, 10,000 before that
  var defaultCutoff = new Date(2026, 0, 1);
  return eventDate >= defaultCutoff ? 12500 : 10000;
}
