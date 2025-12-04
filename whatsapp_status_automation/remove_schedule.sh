#!/bin/bash
# Remove WhatsApp Status Automation schedule

PLIST_NAME="com.whatsapp.autostatus"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

echo "🗑️ Removing WhatsApp Status Automation schedule..."
echo ""

# Unload launch agent
launchctl unload "$PLIST_PATH" 2>/dev/null
echo "   ✅ Launch agent unloaded"

# Remove plist file
rm -f "$PLIST_PATH"
echo "   ✅ Plist file removed"

# Cancel wake schedule
sudo pmset repeat cancel
echo "   ✅ Wake schedule cancelled"

echo ""
echo "✅ Schedule removed successfully!"

