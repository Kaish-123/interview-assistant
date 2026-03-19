#!/bin/bash
# Install LaunchAgent to sync Mac Contacts and rebuild broadcast lists every 6 hours.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PLIST="com.broadcast.marketing.sync.plist"

echo "Installing Broadcast Marketing scheduled sync..."
mkdir -p "$LAUNCH_AGENTS"
launchctl unload "$LAUNCH_AGENTS/$PLIST" 2>/dev/null
sed "s|__BROADCAST_MARKETING_DIR__|$SCRIPT_DIR|g" "$SCRIPT_DIR/$PLIST" > "$LAUNCH_AGENTS/$PLIST"
launchctl load "$LAUNCH_AGENTS/$PLIST"
echo "Done. Contacts will sync and lists rebuild every 6 hours."
echo "Log: $SCRIPT_DIR/sync_and_build.log"
echo "To stop: launchctl unload ~/Library/LaunchAgents/$PLIST"
