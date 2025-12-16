#!/usr/bin/env python3
"""
Show all target groups with details including when they were added
"""

import json
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def add_timestamps_to_existing():
    """Add timestamps to groups that don't have them."""
    config = load_config()
    updated = False
    
    for target in config['targets']:
        if 'added_at' not in target:
            target['added_at'] = "2025-12-11"  # Date when tracking started
            updated = True
    
    if updated:
        save_config(config)
    
    return config

def main():
    config = add_timestamps_to_existing()
    targets = config.get('targets', [])
    
    print()
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                        🎯 TARGET GROUPS                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    enabled_count = sum(1 for t in targets if t.get('enabled', True))
    disabled_count = len(targets) - enabled_count
    
    print(f"  📊 Total: {len(targets)} groups ({enabled_count} enabled, {disabled_count} disabled)")
    print()
    print("─" * 85)
    print(f"  {'#':<3} {'Status':<6} {'Group Name':<40} {'Username':<25} {'Added':<12}")
    print("─" * 85)
    
    for i, target in enumerate(targets, 1):
        status = "✅" if target.get('enabled', True) else "❌"
        name = target.get('name', '')[:38]
        username = target.get('username', '')[:23]
        added_at = target.get('added_at', 'Unknown')
        
        # Format the date nicely
        if added_at and added_at != 'Unknown':
            try:
                if 'T' in added_at:
                    dt = datetime.fromisoformat(added_at.replace('Z', ''))
                    added_display = dt.strftime('%Y-%m-%d')
                else:
                    added_display = added_at
            except:
                added_display = added_at[:10] if len(added_at) > 10 else added_at
        else:
            added_display = "Unknown"
        
        print(f"  {i:<3} {status:<6} {name:<40} {username:<25} {added_display:<12}")
    
    print("─" * 85)
    print()
    
    # Show summary by date
    print("📅 GROUPS BY DATE ADDED:")
    print("─" * 40)
    
    date_counts = {}
    for target in targets:
        added = target.get('added_at', 'Unknown')
        if added and 'T' in added:
            added = added[:10]
        date_counts[added] = date_counts.get(added, 0) + 1
    
    for date, count in sorted(date_counts.items(), reverse=True):
        print(f"  {date}: {count} groups")
    
    print()

if __name__ == "__main__":
    main()

