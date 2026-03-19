#!/bin/bash
# Install LaunchAgent to send WhatsApp broadcasts every 30 minutes.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PLIST="com.broadcast.marketing.send.plist"

echo "Installing Broadcast Marketing send schedule (every 30 minutes)..."
mkdir -p "$LAUNCH_AGENTS"
launchctl unload "$LAUNCH_AGENTS/$PLIST" 2>/dev/null
sed "s|__BROADCAST_MARKETING_DIR__|$SCRIPT_DIR|g" "$SCRIPT_DIR/$PLIST" > "$LAUNCH_AGENTS/$PLIST"
launchctl load "$LAUNCH_AGENTS/$PLIST"
echo "Done. WhatsApp broadcasts will run every 30 minutes."
echo "Logs: $SCRIPT_DIR/send_launchd.log"
echo "To stop: launchctl unload ~/Library/LaunchAgents/$PLIST"
launchctl list | grep com.broadcast.marketing.send || true
