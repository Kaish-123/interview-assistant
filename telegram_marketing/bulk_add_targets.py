#!/usr/bin/env python3
"""
Bulk Add Targets - Add multiple groups/channels at once
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"


def add_targets_bulk(targets_list: list):
    """Add multiple targets to config."""
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    existing_usernames = {t.get('username') for t in config['targets']}
    
    added = 0
    for target in targets_list:
        if isinstance(target, str):
            target = {"name": target, "username": target, "enabled": True}
        
        if target.get('username') not in existing_usernames:
            config['targets'].append(target)
            existing_usernames.add(target.get('username'))
            added += 1
            print(f"✓ Added: {target['name']}")
        else:
            print(f"⚠ Skipped (duplicate): {target['name']}")
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"\n✓ Added {added} new targets")


if __name__ == "__main__":
    print("=" * 50)
    print("BULK ADD TARGETS")
    print("=" * 50)
    print("\nEnter group/channel usernames (one per line)")
    print("Format: @username or just username")
    print("Press Enter twice when done\n")
    
    targets = []
    while True:
        line = input().strip()
        if not line:
            break
        
        # Ensure @ prefix
        if not line.startswith('@') and not line.startswith('ID:'):
            line = '@' + line
        
        targets.append({
            "name": line.replace('@', ''),
            "username": line,
            "enabled": True
        })
    
    if targets:
        add_targets_bulk(targets)
    else:
        print("No targets entered.")

