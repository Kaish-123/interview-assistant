#!/usr/bin/env bash
# Backup your Google Apps Script project: pull latest from Google, then copy all .gs
# and appsscript.json to a timestamped folder so you never lose your script files.
#
# Prereqs: clasp installed (npm install -g @google/clasp), already logged in (./1_login.sh),
#          and this folder is a clasp project (e.g. you ran ./2_clone.sh).
#
# Usage: ./backup_appscript.sh
# Backup goes to: ../CallCalendarScript_Backup_YYYYMMDD_HHMM/

set -e
cd "$(dirname "$0")"
STAMP=$(date +%Y%m%d_%H%M)
BACKUP_DIR="../CallCalendarScript_Backup_${STAMP}"
mkdir -p "$BACKUP_DIR"

echo "=== Pulling latest from Google Apps Script ==="
clasp pull

echo "=== Saving backup to $BACKUP_DIR ==="
for f in ./*.gs; do
  [[ -f "$f" ]] && cp -v "$f" "$BACKUP_DIR/"
done
[[ -f appsscript.json ]] && cp -v appsscript.json "$BACKUP_DIR/"
[[ -f .clasp.json ]] && cp -v .clasp.json "$BACKUP_DIR/"
echo ""
echo "Backup done: $BACKUP_DIR"
echo "Contents: $(ls -la "$BACKUP_DIR")"
