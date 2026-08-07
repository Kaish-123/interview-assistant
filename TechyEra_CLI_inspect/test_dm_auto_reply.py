#!/usr/bin/env python3
"""
Quick test: verify DM auto-reply config and tracker.
Run: python3 test_dm_auto_reply.py
"""
import json
from pathlib import Path

BASE = Path(__file__).parent
CONFIG = BASE / "config.json"
TRACKER = BASE / "dm_replied.json"

def main():
    print("=== DM auto-reply verification ===\n")
    
    # 1. Config
    with open(CONFIG) as f:
        config = json.load(f)
    dm = config.get("dm_auto_reply", {}) or {}
    enabled = dm.get("enabled", True)
    msg = (dm.get("reply_message", "") or "").strip() or "Thanks for reaching out! Please ping me on WhatsApp..."
    
    print(f"1. Config: enabled={enabled}")
    print(f"   Reply message (first 60 chars): {msg[:60]}...")
    
    # 2. Tracker
    if TRACKER.exists():
        with open(TRACKER) as f:
            data = json.load(f)
        print(f"\n2. Replied users: {len(data)}")
        for uid, ts in list(data.items())[:5]:
            print(f"   - user_id={uid}, last_reply_ts={ts}")
    else:
        print("\n2. Replied users: 0 (no DMs replied yet)")
    
    # 3. Log evidence
    log_path = BASE / "unified_runner_error.log"
    if log_path.exists():
        with open(log_path) as f:
            lines = f.readlines()
        dm_sent = [l for l in lines if "DM auto-reply sent to" in l]
        if dm_sent:
            print(f"\n3. Last DM auto-reply from log:")
            print(f"   {dm_sent[-1].strip()}")
        else:
            print("\n3. No 'DM auto-reply sent' lines in log yet (send a test DM from another account to trigger).")
    
    print("\n=== To test live: send a DM to your Telegram from another account; you should get the WhatsApp reply. ===")

if __name__ == "__main__":
    main()
