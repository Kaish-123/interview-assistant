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
