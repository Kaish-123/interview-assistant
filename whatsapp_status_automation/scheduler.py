#!/usr/bin/env python3
"""
Scheduler Setup Script
======================
Sets up launchd (macOS) to run the WhatsApp status automation on schedule.

This creates a LaunchAgent that:
- Runs on Saturday and Sunday
- At your specified time
- Updates your WhatsApp status automatically
"""

import os
import sys
import subprocess
from pathlib import Path

PLIST_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.whatsapp-status</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
        <string>--run</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <array>
        <!-- Saturday at {time} -->
        <dict>
            <key>Weekday</key>
            <integer>6</integer>
            <key>Hour</key>
            <integer>{hour}</integer>
            <key>Minute</key>
            <integer>{minute}</integer>
        </dict>
        <!-- Sunday at {time} -->
        <dict>
            <key>Weekday</key>
            <integer>0</integer>
            <key>Hour</key>
            <integer>{hour}</integer>
            <key>Minute</key>
            <integer>{minute}</integer>
        </dict>
    </array>
    
    <key>StandardOutPath</key>
    <string>{log_path}/whatsapp_status.log</string>
    
    <key>StandardErrorPath</key>
    <string>{log_path}/whatsapp_status_error.log</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
'''


def get_python_path() -> str:
    """Get the path to the Python interpreter in the venv."""
    script_dir = Path(__file__).parent.absolute()
    venv_python = script_dir / "venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def setup_launchd(schedule_time: str = "09:00"):
    """
    Create and load a launchd plist for scheduled execution.
    
    Args:
        schedule_time: Time to run in HH:MM format (24-hour)
    """
    hour, minute = map(int, schedule_time.split(":"))
    
    script_dir = Path(__file__).parent.absolute()
    script_path = script_dir / "whatsapp_status.py"
    
    # LaunchAgents directory
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    
    plist_path = launch_agents_dir / "com.user.whatsapp-status.plist"
    log_path = Path.home() / "Library" / "Logs"
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Generate plist content
    plist_content = PLIST_TEMPLATE.format(
        python_path=get_python_path(),
        script_path=script_path,
        hour=hour,
        minute=minute,
        time=schedule_time,
        log_path=log_path
    )
    
    print("📋 Creating LaunchAgent plist...")
    print(f"   Path: {plist_path}")
    print(f"   Schedule: Saturday & Sunday at {schedule_time}")
    
    # Write plist file
    with open(plist_path, "w") as f:
        f.write(plist_content)
    
    print("\n📦 Loading LaunchAgent...")
    
    # Unload if already loaded
    subprocess.run(
        ["launchctl", "unload", str(plist_path)],
        capture_output=True
    )
    
    # Load the new plist
    result = subprocess.run(
        ["launchctl", "load", str(plist_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ LaunchAgent loaded successfully!")
        print(f"\n📊 Status: launchctl list | grep whatsapp")
        
        # Show status
        status = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True
        )
        for line in status.stdout.split("\n"):
            if "whatsapp" in line.lower():
                print(f"   {line}")
    else:
        print(f"❌ Failed to load LaunchAgent: {result.stderr}")
    
    print("\n📝 Next steps:")
    print("   1. Grant Accessibility permissions to Terminal/Python")
    print("      System Preferences > Security & Privacy > Privacy > Accessibility")
    print("   2. Test with: python whatsapp_status.py --run")
    print("   3. Check logs at: ~/Library/Logs/whatsapp_status.log")


def unload_launchd():
    """Unload and remove the launchd plist."""
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.user.whatsapp-status.plist"
    
    if plist_path.exists():
        print("🗑️ Unloading LaunchAgent...")
        subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
        plist_path.unlink()
        print("✅ LaunchAgent removed")
    else:
        print("ℹ️ No LaunchAgent found")


def show_status():
    """Show current scheduler status."""
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.user.whatsapp-status.plist"
    
    print("📊 WhatsApp Status Automation - Scheduler Status")
    print("=" * 50)
    
    if plist_path.exists():
        print(f"✅ Plist exists: {plist_path}")
        
        # Check if loaded
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True
        )
        
        loaded = any("whatsapp-status" in line for line in result.stdout.split("\n"))
        print(f"{'✅' if loaded else '❌'} Loaded in launchctl: {loaded}")
        
        # Show plist content
        print("\n📄 Current schedule:")
        with open(plist_path) as f:
            content = f.read()
            if "<key>Hour</key>" in content:
                import re
                hours = re.findall(r"<key>Hour</key>\s*<integer>(\d+)</integer>", content)
                minutes = re.findall(r"<key>Minute</key>\s*<integer>(\d+)</integer>", content)
                if hours and minutes:
                    print(f"   Time: {hours[0]}:{minutes[0]:0>2}")
        
        # Show recent logs
        log_path = Path.home() / "Library" / "Logs" / "whatsapp_status.log"
        if log_path.exists():
            print(f"\n📜 Recent log entries:")
            with open(log_path) as f:
                lines = f.readlines()[-10:]
                for line in lines:
                    print(f"   {line.rstrip()}")
    else:
        print("❌ Scheduler not set up")
        print("   Run: python scheduler.py --setup")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup scheduler for WhatsApp Status Automation"
    )
    parser.add_argument(
        "--setup", "-s",
        action="store_true",
        help="Set up the launchd scheduler"
    )
    parser.add_argument(
        "--time", "-t",
        type=str,
        default="09:00",
        help="Time to run (HH:MM format, default: 09:00)"
    )
    parser.add_argument(
        "--unload", "-u",
        action="store_true",
        help="Unload and remove the scheduler"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current scheduler status"
    )
    
    args = parser.parse_args()
    
    if args.setup:
        setup_launchd(args.time)
    elif args.unload:
        unload_launchd()
    elif args.status:
        show_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

