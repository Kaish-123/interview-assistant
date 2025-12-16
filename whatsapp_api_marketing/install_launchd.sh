#!/bin/bash
# WhatsApp API Marketing - Install LaunchAgent
# This script installs the launchd service for scheduled automation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.techyera.whatsapp.api"
PLIST_SOURCE="$SCRIPT_DIR/$PLIST_NAME.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       WhatsApp API Marketing - Install Service           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if plist source exists
if [ ! -f "$PLIST_SOURCE" ]; then
    echo "❌ Error: Plist file not found at $PLIST_SOURCE"
    exit 1
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Unload existing if any
if [ -f "$PLIST_DEST" ]; then
    echo "🔄 Unloading existing service..."
    launchctl unload "$PLIST_DEST" 2>/dev/null
fi

# Copy plist to LaunchAgents
echo "📋 Installing plist..."
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Update paths in plist to use correct Python
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    echo "   Using venv Python: $VENV_PYTHON"
else
    VENV_PYTHON=$(which python3)
    echo "   Using system Python: $VENV_PYTHON"
fi

# Replace paths in plist
sed -i '' "s|/Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac/whatsapp_api_marketing|$SCRIPT_DIR|g" "$PLIST_DEST"

# Load the service
echo "🚀 Loading service..."
launchctl load "$PLIST_DEST"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Service installed successfully!"
    echo ""
    echo "📋 Service Details:"
    echo "   Name: $PLIST_NAME"
    echo "   Interval: Every 60 minutes"
    echo "   Logs: $SCRIPT_DIR/logs/"
    echo ""
    echo "📌 Commands:"
    echo "   Check status:  launchctl list | grep whatsapp"
    echo "   View logs:     tail -f $SCRIPT_DIR/logs/cron_messages.log"
    echo "   Uninstall:     ./uninstall_launchd.sh"
    echo ""
else
    echo "❌ Failed to load service"
    exit 1
fi
