#!/bin/bash
# Install LaunchAgents for TechyEra Telegram Marketing

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "🚀 Installing TechyEra Telegram Marketing LaunchAgents..."
echo ""

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Unload existing agents if they exist
launchctl unload "$LAUNCH_AGENTS_DIR/com.techyera.telegram.send.plist" 2>/dev/null
launchctl unload "$LAUNCH_AGENTS_DIR/com.techyera.telegram.growth.plist" 2>/dev/null

# Copy plist files
cp "$SCRIPT_DIR/com.techyera.telegram.send.plist" "$LAUNCH_AGENTS_DIR/"
cp "$SCRIPT_DIR/com.techyera.telegram.growth.plist" "$LAUNCH_AGENTS_DIR/"

# Load the agents
launchctl load "$LAUNCH_AGENTS_DIR/com.techyera.telegram.send.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.techyera.telegram.growth.plist"

echo "✓ LaunchAgents installed and loaded!"
echo ""
echo "📅 Schedule:"
echo "   • Message Sending: Every 1 hour"
echo "   • Group Growth: Every 6 hours"
echo ""
echo "📁 Log files:"
echo "   • $SCRIPT_DIR/launchd_send.log"
echo "   • $SCRIPT_DIR/launchd_growth.log"
echo ""
echo "🔧 Commands:"
echo "   • Check status: launchctl list | grep techyera"
echo "   • Stop: launchctl unload ~/Library/LaunchAgents/com.techyera.telegram.*.plist"
echo "   • Start: launchctl load ~/Library/LaunchAgents/com.techyera.telegram.*.plist"
echo ""

# Show status
echo "Current status:"
launchctl list | grep techyera
