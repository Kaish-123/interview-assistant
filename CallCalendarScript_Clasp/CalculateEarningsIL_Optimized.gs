/**
 * Calculate earnings from KeywordMapping for CallCalendarSheet.
 *
 * EFFECTIVE-DATE PRICING:
 * - KeywordMapping: A = Keyword, B = Price, C = Start Effective Date (optional).
 * - If C is blank: that price applies from "way back" (used for events before any dated row).
 * - If C is set (e.g. 2026-01-01): that price applies from that date onward.
 * - For each event we use the event's Start Time: we pick the latest keyword row whose
 *   Start Effective Date is on or before the event date. So changing a consultancy's
 *   charge from a date only affects events on/after that date; before that, the
 *   previous (no-date or earlier-date) amount is kept.
 *
 * DEFAULT PRICE: Events whose title matches no keyword get 12,500 (configurable below).
 *
 * INCREMENTAL vs FULL LOAD:
 * - calculateEarningsIL_Optimized (used by trigger): only fills rows where Earnings is
 *   empty; leaves already-filled and Manual Update rows unchanged. Use for "on calendar
 *   change" to save time.
 * - calculateEarningsIL_FullLoad (run manually): recalculates earnings for all rows in
 *   the date range (except Manual Update). Run once after deploying or when you want
 *   a full refresh.
 *
 * Sheet/table names (change if your spreadsheet differs):
 */
var CALENDAR_SHEET_NAME = 'CallCalendarSheet';
var KEYWORD_TABLE_NAME = 'KeywordMapping';

var DEFAULT_PRICE = 12500;   // Events matching no keyword get this (12.5k)

var MANUAL_YES_VALUES = ['yes', 'y', 'true', '1'];

function calculateEarningsIL_Optimized() {
  runEarnings_(true);   // incremental: only fill empty earnings
}

/**
 * Full load: recalculate earnings for ALL rows in date range (except Manual Update).
 * Run this manually once after first deploy, or when you want a full refresh.
 * In Triggers, keep using syncCalendarAndCalculateEarnings for incremental updates.
 */
function calculateEarningsIL_FullLoad() {
  runEarnings_(false);  // full: overwrite all non-manual earnings
}

function runEarnings_(incrementalOnly) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(CALENDAR_SHEET_NAME);
  var mappingSheet = ss.getSheetByName(KEYWORD_TABLE_NAME);
  if (!sheet || !mappingSheet) return;

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return;
  var data = sheet.getRange(2, 1, lastRow, 6).getValues();

  var keywordMap = loadKeywordMapWithEffectiveDate_(mappingSheet);

  var startDate = new Date(2024, 0, 1);
  var endDate = new Date(2026, 2, 1);

  var updatedData = data.map(function(row) {
    var eventId = row[0], title = row[1], start = row[2], end = row[3], earnings = row[4], manualUpdate = row[5];

    var eventDate = start instanceof Date ? start : new Date(start);
    if (eventDate < startDate || eventDate > endDate) return row;

    var manual = (manualUpdate || '').toString().trim().toLowerCase();
    if (MANUAL_YES_VALUES.indexOf(manual) !== -1) return row;

    // Incremental: only fill rows that don't have earnings yet
    if (incrementalOnly && (earnings !== '' && earnings !== null && earnings !== undefined || (typeof earnings === 'number' && !isNaN(earnings)))) return row;

    var updatedEarnings = getPriceForEventDate_(keywordMap, (title || '').toString(), eventDate, DEFAULT_PRICE);
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
