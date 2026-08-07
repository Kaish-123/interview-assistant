#!/bin/bash
# Double-click this file to reload Telegram marketing services
# macOS will open Terminal and run this automatically

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "🔄 Reloading TechyEra Telegram LaunchAgents..."
mkdir -p "$LAUNCH_AGENTS_DIR"

launchctl unload "$LAUNCH_AGENTS_DIR/com.techyera.telegram.send.plist" 2>/dev/null
launchctl unload "$LAUNCH_AGENTS_DIR/com.techyera.telegram.growth.plist" 2>/dev/null

cp "$SCRIPT_DIR/com.techyera.telegram.send.plist" "$LAUNCH_AGENTS_DIR/"
cp "$SCRIPT_DIR/com.techyera.telegram.growth.plist" "$LAUNCH_AGENTS_DIR/"

launchctl load "$LAUNCH_AGENTS_DIR/com.techyera.telegram.send.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.techyera.telegram.growth.plist"

echo ""
echo "✅ Done! Verifying..."
launchctl list | grep techyera
echo ""
echo "Services are now running. This window can be closed."
