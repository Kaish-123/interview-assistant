#!/bin/bash
# Uninstall TechyEra LaunchAgents

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "🛑 Stopping and uninstalling TechyEra LaunchAgents..."

launchctl unload "$LAUNCH_AGENTS_DIR/com.techyera.telegram.send.plist" 2>/dev/null
launchctl unload "$LAUNCH_AGENTS_DIR/com.techyera.telegram.growth.plist" 2>/dev/null

rm -f "$LAUNCH_AGENTS_DIR/com.techyera.telegram.send.plist"
rm -f "$LAUNCH_AGENTS_DIR/com.techyera.telegram.growth.plist"

echo "✅ LaunchAgents removed!"
echo ""
echo "The automation is now stopped and will not run on restart."
