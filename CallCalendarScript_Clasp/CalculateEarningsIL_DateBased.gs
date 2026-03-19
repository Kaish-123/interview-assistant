/**
 * INCREMENTAL (IL) — Date-based earnings for CallCalendarSheet.
 *
 * Only updates rows where Earnings (column E) is empty. Skips rows that already
 * have earnings, so new calendar events get filled without touching existing data.
 * Uses the same date-based keyword mapping and defaults as calculateEarningsFL_DateBased.
 *
 * Use this from triggers (e.g. after calendar sync). Run calculateEarningsFL_DateBased
 * manually when you need a full recalc (e.g. after changing KeywordMapping or date rules).
 *
 * Efficiency: one read of data, one write of column E only; earnings computed only for
 * rows that need it (empty + in date range + not manual).
 */
function calculateEarningsIL_DateBased() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('CallCalendarSheet');
  var mappingSheet = ss.getSheetByName('KeywordMapping');

  if (!sheet || !mappingSheet) return;

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  var dataStartRow = 2;
  var dataEndRow = Math.max(2, lastRow - 1);
  var numRows = dataEndRow - dataStartRow + 1;
  if (numRows <= 0) return;

  var data = sheet.getRange(dataStartRow, 1, dataEndRow, 6).getValues();
  var keywordMap = buildKeywordMapWithEffectiveDate_(mappingSheet);

  var startDate = new Date(2024, 0, 1);
  var endDate = new Date(2026, 2, 10);
  var manualYes = ['yes', 'y', 'true', '1'];

  var updatedCount = 0;
  var row, eventDate, manual, earningsVal, isEmpty, title, newEarnings;

  for (var i = 0; i < data.length; i++) {
    row = data[i];
    eventDate = row[2] instanceof Date ? row[2] : new Date(row[2]);
    if (eventDate < startDate || eventDate > endDate) continue;

    manual = (row[5] || '').toString().trim().toLowerCase();
    if (manualYes.indexOf(manual) !== -1) continue;

    earningsVal = row[4];
    isEmpty = earningsVal === '' || earningsVal === null || (typeof earningsVal === 'number' && isNaN(earningsVal));
    if (!isEmpty) continue;

    title = (row[1] || '').toString();
    newEarnings = getEarningsForDate_(keywordMap, title, eventDate);
    row[4] = newEarnings;
    updatedCount++;
  }

  if (updatedCount === 0) return;

  var colE = data.map(function(r) { return [r[4]]; });
  sheet.getRange(dataStartRow, 5, data.length, 1).setValues(colE);
}
