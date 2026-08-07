#!/usr/bin/env python3
"""
Shows next scheduled run times for Telegram Marketing
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def main():
    config = load_config()
    now = datetime.now()
    
    print("\n" + "="*50)
    print("⏰ NEXT SCHEDULED RUNS")
    print("="*50)
    print(f"\nCurrent time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Message sending (every hour at :00)
    next_msg = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    print(f"\n📨 Next Message Send:")
    print(f"   {next_msg.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   (Every {config['schedule']['interval_minutes']} minutes)")
    
    # Growth (every 6 hours)
    growth_interval = config.get('growth', {}).get('check_interval_hours', 6)
    next_growth_hour = ((now.hour // growth_interval) + 1) * growth_interval
    if next_growth_hour >= 24:
        next_growth = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        next_growth = now.replace(hour=next_growth_hour, minute=0, second=0, microsecond=0)
    
    print(f"\n🌱 Next Growth Check:")
    print(f"   {next_growth.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   (Every {growth_interval} hours)")
    
    # Active hours
    start = config['schedule']['active_hours']['start']
    end = config['schedule']['active_hours']['end']
    print(f"\n📅 Active Hours: {start}:00 - {end}:00")
    
    if start <= now.hour < end:
        print("   Status: ✓ Currently ACTIVE")
    else:
        print("   Status: ✗ Currently INACTIVE")

if __name__ == "__main__":
    main()
