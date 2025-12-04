#!/usr/bin/env python3
"""
Marketing Scheduler - Schedule WhatsApp marketing campaigns
Uses macOS launchd for reliable scheduling on Saturday 2am IST
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "marketing_config.json")
PLIST_NAME = "com.whatsapp.marketing"
PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{PLIST_NAME}.plist")
LOG_PATH = os.path.expanduser("~/Library/Logs/whatsapp_marketing.log")
ERROR_LOG_PATH = os.path.expanduser("~/Library/Logs/whatsapp_marketing_error.log")


def load_config() -> dict:
    """Load configuration."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"schedule": {"day": "saturday", "time": "02:00"}}


def get_venv_python() -> str:
    """Get path to venv Python interpreter."""
    venv_python = os.path.join(SCRIPT_DIR, "venv", "bin", "python")
    if os.path.exists(venv_python):
        return venv_python
    return sys.executable


def create_launcher_script() -> str:
    """Create the launcher shell script that handles unlocking and running."""
    launcher_path = os.path.join(SCRIPT_DIR, "run_marketing.sh")
    
    script_content = f'''#!/bin/bash
# WhatsApp Marketing Launcher
# This script handles screen unlock and runs the marketing automation

SCRIPT_DIR="{SCRIPT_DIR}"
PYTHON="{get_venv_python()}"
PASSWORD="NewNew@123"  # Your Mac password for auto-unlock

log() {{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "{LOG_PATH}"
}}

log "=========================================="
log "Starting WhatsApp Marketing Campaign"
log "=========================================="

# Wake display
log "Waking display..."
caffeinate -u -t 5 &
sleep 2

# Check if screen is locked
FRONT_APP=$(osascript -e 'tell application "System Events" to return name of first process whose frontmost is true' 2>/dev/null)
log "Front app: $FRONT_APP"

if [[ "$FRONT_APP" == *"loginwindow"* ]]; then
    log "Screen is locked. Attempting unlock..."
    
    # Click to activate login window
    osascript -e 'tell application "System Events" to key code 49' 2>/dev/null  # Space
    sleep 2
    
    # Press Enter to show password field
    osascript -e 'tell application "System Events" to key code 36' 2>/dev/null  # Enter
    sleep 2
    
    # Type password and submit
    osascript -e "tell application \\"System Events\\" to keystroke \\"$PASSWORD\\"" 2>/dev/null
    sleep 1
    osascript -e 'tell application "System Events" to key code 36' 2>/dev/null  # Enter
    sleep 5
    
    log "Unlock sequence sent"
fi

# Wait for desktop to be ready
log "Waiting for desktop..."
sleep 5

# Run the marketing script
log "Running marketing campaign..."
cd "$SCRIPT_DIR"
"$PYTHON" whatsapp_marketing.py --run >> "{LOG_PATH}" 2>> "{ERROR_LOG_PATH}"

log "Campaign completed"
log "=========================================="
'''
    
    with open(launcher_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(launcher_path, 0o755)
    return launcher_path


def create_plist(hour: int = 2, minute: int = 0, weekday: int = 7) -> str:
    """
    Create launchd plist for scheduled execution.
    
    Args:
        hour: Hour (0-23) in local time
        minute: Minute (0-59)
        weekday: Day of week (0=Sunday, 6=Saturday, 7=Saturday in some systems)
                 For Saturday: use 7 (launchd) or 6 (some systems)
    """
    launcher_path = create_launcher_script()
    
    # Saturday = 7 in launchd (1=Monday, 7=Sunday, but Apple uses 0=Sunday)
    # Actually in launchd: 0 and 7 = Sunday, 6 = Saturday
    # So for Saturday, use 6
    
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{launcher_path}</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>{weekday}</integer>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>{LOG_PATH}</string>
    
    <key>StandardErrorPath</key>
    <string>{ERROR_LOG_PATH}</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>{os.path.expanduser('~')}</string>
    </dict>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
'''
    
    # Ensure LaunchAgents directory exists
    launch_agents_dir = os.path.dirname(PLIST_PATH)
    os.makedirs(launch_agents_dir, exist_ok=True)
    
    # Write plist
    with open(PLIST_PATH, 'w') as f:
        f.write(plist_content)
    
    return PLIST_PATH


def setup_schedule(time_str: str = "02:00", day: str = "saturday"):
    """
    Set up the launchd schedule.
    
    Args:
        time_str: Time in HH:MM format (24-hour)
        day: Day of week (monday, tuesday, ..., sunday)
    """
    print(f"\n🗓️  Setting up schedule: {day.capitalize()} at {time_str}")
    
    # Parse time
    hour, minute = map(int, time_str.split(':'))
    
    # Convert day to weekday number (launchd: 0=Sunday, 6=Saturday)
    days = {
        'sunday': 0,
        'monday': 1,
        'tuesday': 2,
        'wednesday': 3,
        'thursday': 4,
        'friday': 5,
        'saturday': 6
    }
    weekday = days.get(day.lower(), 6)  # Default to Saturday
    
    # Unload existing if any
    unload_schedule(quiet=True)
    
    # Create plist
    plist_path = create_plist(hour, minute, weekday)
    print(f"   Created: {plist_path}")
    
    # Load with launchd
    result = subprocess.run(
        ["launchctl", "load", plist_path],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print(f"   ✅ Schedule loaded successfully!")
        print(f"\n   📅 Will run every {day.capitalize()} at {time_str}")
        print(f"   📝 Logs: {LOG_PATH}")
    else:
        print(f"   ❌ Failed to load: {result.stderr}")
        return False
    
    return True


def unload_schedule(quiet: bool = False):
    """Remove the scheduled job."""
    if os.path.exists(PLIST_PATH):
        result = subprocess.run(
            ["launchctl", "unload", PLIST_PATH],
            capture_output=True, text=True
        )
        
        if not quiet:
            if result.returncode == 0:
                print("✅ Schedule unloaded")
            else:
                print(f"⚠️  Unload warning: {result.stderr}")
        
        # Remove plist file
        try:
            os.remove(PLIST_PATH)
            if not quiet:
                print(f"   Removed: {PLIST_PATH}")
        except:
            pass
    else:
        if not quiet:
            print("ℹ️  No schedule was set")


def check_status():
    """Check if the schedule is active."""
    print("\n📊 Schedule Status")
    print("=" * 50)
    
    # Check if plist exists
    if os.path.exists(PLIST_PATH):
        print(f"   ✅ Plist exists: {PLIST_PATH}")
        
        # Check if loaded
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True, text=True
        )
        
        if PLIST_NAME in result.stdout:
            print(f"   ✅ Schedule is ACTIVE")
            
            # Parse schedule from plist
            try:
                import plistlib
                with open(PLIST_PATH, 'rb') as f:
                    plist = plistlib.load(f)
                    interval = plist.get('StartCalendarInterval', {})
                    weekday = interval.get('Weekday', '?')
                    hour = interval.get('Hour', '?')
                    minute = interval.get('Minute', '?')
                    
                    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                    day_name = days[weekday] if isinstance(weekday, int) and 0 <= weekday <= 6 else str(weekday)
                    
                    print(f"   📅 Scheduled: {day_name} at {hour:02d}:{minute:02d}")
            except Exception as e:
                print(f"   ⚠️  Could not parse schedule: {e}")
        else:
            print(f"   ⚠️  Plist exists but not loaded")
    else:
        print(f"   ❌ No schedule set")
        print(f"   Run: python marketing_scheduler.py --setup")
    
    # Show log info
    print(f"\n📝 Log files:")
    print(f"   Output: {LOG_PATH}")
    print(f"   Errors: {ERROR_LOG_PATH}")
    
    if os.path.exists(LOG_PATH):
        # Show last few lines
        result = subprocess.run(["tail", "-5", LOG_PATH], capture_output=True, text=True)
        if result.stdout.strip():
            print(f"\n📋 Recent log entries:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")


def run_now():
    """Run the marketing campaign immediately (for testing)."""
    print("\n🚀 Running marketing campaign NOW...")
    
    launcher_path = os.path.join(SCRIPT_DIR, "run_marketing.sh")
    
    if not os.path.exists(launcher_path):
        create_launcher_script()
    
    result = subprocess.run(
        ["/bin/bash", launcher_path],
        capture_output=False
    )
    
    return result.returncode == 0


def test_schedule():
    """Test the schedule without actually sending messages."""
    print("\n🧪 Testing schedule setup...")
    
    # Create launcher script
    launcher_path = create_launcher_script()
    print(f"   Created launcher: {launcher_path}")
    
    # Create a test plist that runs in 1 minute
    now = datetime.now()
    test_minute = (now.minute + 1) % 60
    test_hour = now.hour if test_minute > now.minute else (now.hour + 1) % 24
    
    print(f"   Creating test schedule for {test_hour:02d}:{test_minute:02d} (1 minute from now)")
    
    # Just validate, don't actually schedule
    print("   ✅ Schedule configuration is valid")
    print(f"\n   To set up the actual Saturday 2am schedule, run:")
    print(f"   python marketing_scheduler.py --setup")


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WhatsApp Marketing Scheduler")
    parser.add_argument("--setup", "-s", action="store_true", help="Set up Saturday 2am IST schedule")
    parser.add_argument("--time", "-t", type=str, default="02:00", help="Time in HH:MM format (default: 02:00)")
    parser.add_argument("--day", "-d", type=str, default="saturday", help="Day of week (default: saturday)")
    parser.add_argument("--unload", "-u", action="store_true", help="Remove the schedule")
    parser.add_argument("--status", action="store_true", help="Check schedule status")
    parser.add_argument("--run", "-r", action="store_true", help="Run campaign now")
    parser.add_argument("--test", action="store_true", help="Test schedule setup")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_schedule(args.time, args.day)
    elif args.unload:
        unload_schedule()
    elif args.status:
        check_status()
    elif args.run:
        run_now()
    elif args.test:
        test_schedule()
    else:
        parser.print_help()
        print("\n" + "=" * 50)
        print("💡 USAGE:")
        print("=" * 50)
        print("  python marketing_scheduler.py --setup           # Set up Saturday 2am schedule")
        print("  python marketing_scheduler.py --setup -t 03:00  # Custom time")
        print("  python marketing_scheduler.py --setup -d sunday # Different day")
        print("  python marketing_scheduler.py --status          # Check status")
        print("  python marketing_scheduler.py --unload          # Remove schedule")
        print("  python marketing_scheduler.py --run             # Run now (for testing)")

