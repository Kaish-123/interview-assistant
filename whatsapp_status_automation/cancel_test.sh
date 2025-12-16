#!/bin/bash
# Cancel test schedule

PLIST_PATH="$HOME/Library/LaunchAgents/com.whatsapp.autostatus.test.plist"

echo "🗑️ Cancelling test..."
launchctl unload "$PLIST_PATH" 2>/dev/null
rm -f "$PLIST_PATH"
sudo pmset schedule cancelall
echo "✅ Test cancelled!"





