#!/usr/bin/env python3
"""
Monitor script for Telegram Marketing CLI
Shows stats, logs, and status
"""

import json
import argparse
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
SEND_LOG = BASE_DIR / "send_messages.log"
GROWTH_LOG = BASE_DIR / "growth.log"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def show_stats():
    """Show overall statistics"""
    config = load_config()
    
    print("\n" + "="*50)
    print("📊 TELEGRAM MARKETING STATS")
    print("="*50)
    
    targets = config.get('targets', [])
    enabled = [t for t in targets if t.get('enabled', True)]
    
    print(f"\n📌 Groups:")
    print(f"   Total: {len(targets)}")
    print(f"   Enabled: {len(enabled)}")
    print(f"   Disabled: {len(targets) - len(enabled)}")
    
    # Count auto-growth groups
    auto_groups = [t for t in targets if t.get('source') == 'auto_growth']
    print(f"   From Auto-Growth: {len(auto_groups)}")
    
    print(f"\n⏰ Schedule:")
    print(f"   Interval: Every {config['schedule']['interval_minutes']} minutes")
    print(f"   Active Hours: {config['schedule']['active_hours']['start']}:00 - {config['schedule']['active_hours']['end']}:00")
    
    print(f"\n⚙️ Settings:")
    print(f"   Delay between groups: {config['settings']['delay_between_groups_seconds']}s")
    print(f"   Max messages/day: {config['settings']['max_messages_per_day']}")
    
    if config.get('growth', {}).get('enabled'):
        print(f"\n🌱 Growth:")
        print(f"   Status: Enabled")
        print(f"   Keywords: {', '.join(config['growth']['keywords'][:5])}...")
        print(f"   Max groups/day: {config['growth']['max_groups_per_day']}")

def show_recent_logs(log_type='all', lines=20):
    """Show recent log entries"""
    print("\n" + "="*50)
    print(f"📜 RECENT LOGS (last {lines} entries)")
    print("="*50)
    
    if log_type in ['all', 'send']:
        if SEND_LOG.exists():
            print("\n--- Send Messages Log ---")
            with open(SEND_LOG, 'r') as f:
                log_lines = f.readlines()[-lines:]
                for line in log_lines:
                    print(line.strip())
    
    if log_type in ['all', 'growth']:
        if GROWTH_LOG.exists():
            print("\n--- Growth Log ---")
            with open(GROWTH_LOG, 'r') as f:
                log_lines = f.readlines()[-lines:]
                for line in log_lines:
                    print(line.strip())

def show_groups():
    """Show all target groups"""
    config = load_config()
    
    print("\n" + "="*50)
    print("📋 TARGET GROUPS")
    print("="*50)
    
    for i, target in enumerate(config['targets'], 1):
        status = "✓" if target.get('enabled', True) else "✗"
        source = f" [{target.get('source', 'manual')}]" if target.get('source') else ""
        print(f"{i:3}. {status} @{target['username']}{source}")

def show_errors():
    """Show recent errors from logs"""
    print("\n" + "="*50)
    print("❌ RECENT ERRORS")
    print("="*50)
    
    for log_file in [SEND_LOG, GROWTH_LOG]:
        if log_file.exists():
            print(f"\n--- From {log_file.name} ---")
            with open(log_file, 'r') as f:
                for line in f:
                    if 'ERROR' in line or '✗' in line:
                        print(line.strip())

def main():
    parser = argparse.ArgumentParser(description='Telegram Marketing Monitor')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--logs', action='store_true', help='Show recent logs')
    parser.add_argument('--groups', action='store_true', help='Show all groups')
    parser.add_argument('--errors', action='store_true', help='Show errors')
    parser.add_argument('--lines', type=int, default=20, help='Number of log lines')
    parser.add_argument('--type', choices=['all', 'send', 'growth'], default='all')
    
    args = parser.parse_args()
    
    if args.stats:
        show_stats()
    elif args.logs:
        show_recent_logs(args.type, args.lines)
    elif args.groups:
        show_groups()
    elif args.errors:
        show_errors()
    else:
        # Default: show everything
        show_stats()
        show_recent_logs(lines=10)

if __name__ == "__main__":
    main()
