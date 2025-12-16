#!/bin/bash
# WhatsApp API Marketing - Uninstall LaunchAgent

PLIST_NAME="com.techyera.whatsapp.api"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       WhatsApp API Marketing - Uninstall Service         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

if [ -f "$PLIST_PATH" ]; then
    echo "🔄 Unloading service..."
    launchctl unload "$PLIST_PATH" 2>/dev/null
    
    echo "🗑️  Removing plist..."
    rm "$PLIST_PATH"
    
    echo ""
    echo "✅ Service uninstalled successfully!"
else
    echo "ℹ️  Service was not installed"
fi
