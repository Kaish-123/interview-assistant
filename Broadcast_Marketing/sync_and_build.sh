#!/bin/bash
# Run by LaunchAgent: sync contacts from Mac, then rebuild broadcast lists.
# Install with: ./run.sh install-schedule

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
LOG="$SCRIPT_DIR/sync_and_build.log"
PYTHON="${PYTHON:-python3}"

echo "$(date '+%Y-%m-%d %H:%M:%S') Sync and build started" >> "$LOG"
$PYTHON sync_contacts_from_mac.py >> "$LOG" 2>&1
$PYTHON build_broadcast_lists.py >> "$LOG" 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') Sync and build finished" >> "$LOG"
