/**
 * One-time setup: creates the required sheets and headers in the ACTIVE spreadsheet.
 * Run this once after creating a new Google Sheet and attaching this script project.
 *
 * In Apps Script: Run → setupSpreadsheet
 *
 * This will:
 * - Create or reset "CallCalendarSheet" (calendar events + earnings)
 * - Create or reset "KeywordMapping" (keyword, price, start effective date)
 * You can then add your keywords in KeywordMapping and run runFullLoad().
 */
function setupSpreadsheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  var calendarSheetName = 'CallCalendarSheet';
  var mappingSheetName = 'KeywordMapping';

  var sheet = ss.getSheetByName(calendarSheetName);
  if (!sheet) {
    sheet = ss.insertSheet(calendarSheetName);
  }
  sheet.clear();
  sheet.appendRow([
    'Event ID',
    'Event Title',
    'Start Time',
    'End Time',
    'Earnings',
    'Manual Update',
    'Selection Status'
  ]);
  sheet.setFrozenRows(1);

  var mappingSheet = ss.getSheetByName(mappingSheetName);
  if (!mappingSheet) {
    mappingSheet = ss.insertSheet(mappingSheetName);
  }
  var mappingLastRow = mappingSheet.getLastRow();
  if (mappingLastRow === 0) {
    mappingSheet.appendRow(['Keyword', 'Price', 'Start Effective Date']);
    mappingSheet.setFrozenRows(1);
  } else {
    var headers = mappingSheet.getRange(1, 1, 1, 3).getValues()[0];
    if (String(headers[0]).toLowerCase().indexOf('keyword') === -1) {
      mappingSheet.insertRowBefore(1);
      mappingSheet.getRange(1, 1, 1, 3).setValues([['Keyword', 'Price', 'Start Effective Date']]);
      mappingSheet.setFrozenRows(1);
    }
  }

  Logger.log('Setup done. CallCalendarSheet and KeywordMapping are ready.');
  SpreadsheetApp.getUi().alert('Setup complete. Add keywords in the KeywordMapping sheet, then run runFullLoad() from the Apps Script Run menu.');
}
