#!/bin/bash
# Setup WhatsApp Status Automation for Saturday & Sunday at 6 AM IST

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.whatsapp.autostatus"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
AUTO_SCRIPT="$SCRIPT_DIR/auto_status.py"

echo "=================================================="
echo "🔧 WhatsApp Status Automation Setup"
echo "=================================================="
echo ""

# Step 1: Set up wake schedule using pmset
echo "📅 Step 1: Setting up wake schedule..."
echo "   This will wake your Mac at 5:55 AM on Sat & Sun"
echo "   (Requires admin password)"
echo ""

# Remove existing wake schedule
sudo pmset repeat cancel 2>/dev/null

# Set wake schedule for Saturday and Sunday at 5:55 AM (5 mins before script runs)
# Format: pmset repeat wakeorpoweron MTWRFSU HH:MM:SS
# S=Saturday (index 6), U=Sunday (index 0)
sudo pmset repeat wakeorpoweron SU 05:55:00

echo "   ✅ Wake schedule set!"
echo ""

# Step 2: Create LaunchAgent plist
echo "📝 Step 2: Creating launch agent..."

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Create the plist file
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
    <array>
        <!-- Saturday at 6:00 AM -->
        <dict>
            <key>Weekday</key>
            <integer>6</integer>
            <key>Hour</key>
            <integer>6</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <!-- Sunday at 6:00 AM -->
        <dict>
            <key>Weekday</key>
            <integer>0</integer>
            <key>Hour</key>
            <integer>6</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
    
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/autostatus.log</string>
    
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/autostatus_error.log</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

echo "   ✅ Launch agent created at: $PLIST_PATH"
echo ""

# Step 3: Create logs directory
echo "📁 Step 3: Creating logs directory..."
mkdir -p "$SCRIPT_DIR/logs"
echo "   ✅ Logs will be saved to: $SCRIPT_DIR/logs/"
echo ""

# Step 4: Load the launch agent
echo "🚀 Step 4: Loading launch agent..."
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"
echo "   ✅ Launch agent loaded!"
echo ""

# Step 5: Verify setup
echo "=================================================="
echo "✅ SETUP COMPLETE!"
echo "=================================================="
echo ""
echo "📋 Summary:"
echo "   • Wake schedule: Sat & Sun at 5:55 AM"
echo "   • Script runs: Sat & Sun at 6:00 AM"
echo "   • Posts all images from: $SCRIPT_DIR/status_images/"
echo ""
echo "🔍 To verify wake schedule:"
echo "   pmset -g sched"
echo ""
echo "🔍 To verify launch agent:"
echo "   launchctl list | grep whatsapp"
echo ""
echo "🧪 To test NOW (without waiting):"
echo "   $VENV_PYTHON $AUTO_SCRIPT"
echo ""
echo "❌ To remove schedule:"
echo "   ./remove_schedule.sh"
echo ""

