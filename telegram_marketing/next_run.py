#!/usr/bin/env python3
"""
⏰ NEXT RUN SCHEDULER INFO
Shows when the bot will run next and what it will do
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
LOG_FILE = SCRIPT_DIR / "cron_messages.log"

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def get_last_run_time():
    """Get the last time messages were sent from log."""
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        for line in reversed(lines):
            if 'Completed:' in line or 'CRON JOB: Send Messages Started' in line:
                # Extract timestamp: 2025-12-11 02:33:02,925
                parts = line.split(' - ')
                if parts:
                    timestamp_str = parts[0].split(',')[0]
                    return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    except:
        pass
    return None

def main():
    config = load_config()
    now = datetime.now()
    
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              ⏰ NEXT SCHEDULED RUNS                          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Calculate next message run (every hour at :00)
    next_msg = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    time_to_msg = next_msg - now
    mins_to_msg = int(time_to_msg.total_seconds() / 60)
    
    # Calculate next growth run (every 6 hours at :00)
    next_growth = now.replace(minute=0, second=0, microsecond=0)
    while next_growth.hour % 6 != 0:
        next_growth += timedelta(hours=1)
    if next_growth <= now:
        next_growth += timedelta(hours=6)
    time_to_growth = next_growth - now
    mins_to_growth = int(time_to_growth.total_seconds() / 60)
    hours_to_growth = mins_to_growth // 60
    mins_remainder = mins_to_growth % 60
    
    print("📤 NEXT MESSAGE BATCH:")
    print("─" * 60)
    print(f"   🕐 Time: {next_msg.strftime('%I:%M %p')} ({next_msg.strftime('%H:%M')})")
    print(f"   ⏳ In: {mins_to_msg} minutes")
    print()
    
    print("🌱 NEXT GROWTH CYCLE (Find & Join Groups):")
    print("─" * 60)
    print(f"   🕐 Time: {next_growth.strftime('%I:%M %p')} ({next_growth.strftime('%H:%M')})")
    print(f"   ⏳ In: {hours_to_growth} hours {mins_remainder} minutes")
    print()
    
    # Last run info
    last_run = get_last_run_time()
    if last_run:
        time_since = now - last_run
        mins_since = int(time_since.total_seconds() / 60)
        print("📊 LAST MESSAGE BATCH:")
        print("─" * 60)
        print(f"   🕐 Time: {last_run.strftime('%I:%M %p')} ({last_run.strftime('%H:%M')})")
        print(f"   ⏳ {mins_since} minutes ago")
        print()
    
    # Groups that will receive messages
    targets = config.get('targets', [])
    enabled_targets = [t for t in targets if t.get('enabled', True)]
    
    print("🎯 GROUPS THAT WILL RECEIVE MESSAGES:")
    print("─" * 60)
    print(f"   Total enabled: {len(enabled_targets)} groups")
    print()
    
    for i, target in enumerate(enabled_targets, 1):
        name = target.get('name', '')[:45]
        username = target.get('username', '')
        print(f"   {i:2}. {name:<45} {username}")
    
    print()
    print("─" * 60)
    print(f"📅 Current Time: {now.strftime('%Y-%m-%d %I:%M:%S %p')}")
    print()
    
    # Schedule summary
    print("📋 SCHEDULE SUMMARY:")
    print("─" * 60)
    print("   📤 Messages: Every hour at :00 (e.g., 3:00, 4:00, 5:00...)")
    print("   🌱 Growth:   Every 6 hours at :00 (e.g., 0:00, 6:00, 12:00, 18:00)")
    print()

if __name__ == "__main__":
    main()
