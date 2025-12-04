#!/bin/bash
# Test WhatsApp Status Automation - Runs in 3 minutes

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.whatsapp.autostatus.test"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
AUTO_SCRIPT="$SCRIPT_DIR/auto_status.py"

# Calculate time - wake 1 min before run
WAKE_TIME=$(date -v+2M "+%H:%M:%S")
RUN_HOUR=$(date -v+3M "+%H")
RUN_MIN=$(date -v+3M "+%M")
RUN_TIME=$(date -v+3M "+%H:%M")

# Remove leading zeros for launchd (it needs integers)
RUN_HOUR=$((10#$RUN_HOUR))
RUN_MIN=$((10#$RUN_MIN))

echo "=================================================="
echo "🧪 TEST MODE - WhatsApp Status Automation"
echo "=================================================="
echo ""
echo "⏰ Current time: $(date '+%H:%M:%S')"
echo "💡 Wake time:    $WAKE_TIME (in 2 minutes)"
echo "🚀 Run time:     $RUN_TIME (in 3 minutes)"
echo ""

# Step 1: Cancel any existing schedules
echo "🗑️ Clearing existing test schedules..."
launchctl unload "$PLIST_PATH" 2>/dev/null
rm -f "$PLIST_PATH"
sudo pmset repeat cancel 2>/dev/null
echo "   ✅ Done"
echo ""

# Step 2: Set wake schedule for 2 minutes from now
echo "⏰ Setting wake schedule for $WAKE_TIME..."
# pmset schedule requires: type date time
WAKE_DATE=$(date -v+2M "+%m/%d/%Y %H:%M:%S")
sudo pmset schedule wakeorpoweron "$WAKE_DATE"
echo "   ✅ Wake scheduled!"
echo ""

# Step 3: Create test LaunchAgent
echo "📝 Creating test launch agent for $RUN_TIME..."

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$SCRIPT_DIR/logs"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON</string>
        <string>$AUTO_SCRIPT</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>$RUN_HOUR</integer>
        <key>Minute</key>
        <integer>$RUN_MIN</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/test_autostatus.log</string>
    
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/test_autostatus_error.log</string>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH"
echo "   ✅ Launch agent loaded!"
echo ""

# Verify
echo "📋 Verifying setup..."
echo ""
echo "Wake schedule:"
pmset -g sched
echo ""

echo "=================================================="
echo "✅ TEST READY!"
echo "=================================================="
echo ""
echo "🎯 WHAT TO DO NOW:"
echo ""
echo "   1. Make sure Mac is PLUGGED IN (charging)"
echo "   2. CLOSE THE LID now"
echo "   3. Wait until $RUN_TIME (~3 minutes)"
echo "   4. Mac will wake, unlock, and post status!"
echo ""
echo "📁 Check logs after: $SCRIPT_DIR/logs/test_autostatus.log"
echo ""
echo "❌ To cancel test: ./cancel_test.sh"
echo ""

