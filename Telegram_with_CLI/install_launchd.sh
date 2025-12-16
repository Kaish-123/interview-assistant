#!/bin/bash
# Install macOS LaunchAgents for Telegram Marketing
# This makes the automation run automatically, even after restarts!

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "🚀 Installing TechyEra Telegram Marketing LaunchAgents..."
echo ""

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Stop existing agents if running
launchctl unload "$LAUNCH_AGENTS_DIR/com.techyera.telegram.send.plist" 2>/dev/null
launchctl unload "$LAUNCH_AGENTS_DIR/com.techyera.telegram.growth.plist" 2>/dev/null

# Copy plist files
cp "$SCRIPT_DIR/com.techyera.telegram.send.plist" "$LAUNCH_AGENTS_DIR/"
cp "$SCRIPT_DIR/com.techyera.telegram.growth.plist" "$LAUNCH_AGENTS_DIR/"

# Load the agents
launchctl load "$LAUNCH_AGENTS_DIR/com.techyera.telegram.send.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.techyera.telegram.growth.plist"

echo "✅ LaunchAgents installed and started!"
echo ""
echo "📋 What's running:"
echo "   • Send Messages: Every 30 minutes (runs immediately + every 30 min)"
echo "   • Growth: Every 6 hours (runs immediately + every 6 hours)"
echo ""
echo "🔄 These will:"
echo "   • Start automatically when you log in"
echo "   • Survive system restarts"
echo "   • Run in background forever"
echo ""
echo "📂 Log files:"
echo "   • $SCRIPT_DIR/cron_messages.log"
echo "   • $SCRIPT_DIR/cron_growth.log"
echo ""
echo "🔍 Check status:"
echo "   launchctl list | grep techyera"
echo ""
echo "❌ To stop and uninstall:"
echo "   launchctl unload ~/Library/LaunchAgents/com.techyera.telegram.send.plist"
echo "   launchctl unload ~/Library/LaunchAgents/com.techyera.telegram.growth.plist"
echo ""
