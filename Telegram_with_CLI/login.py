#!/usr/bin/env python3
"""
Login script for Telegram CLI
Run this once to authenticate
"""

import asyncio
import json
from pathlib import Path
from telethon import TelegramClient

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

async def login():
    config = load_config()
    
    print("\n" + "="*50)
    print("🔐 TELEGRAM LOGIN")
    print("="*50)
    
    # Create client for cron_session (main session used by send)
    client = TelegramClient(
        str(BASE_DIR / "cron_session"),
        config['api_id'],
        config['api_hash']
    )
    
    await client.start(phone=config['phone'])
    
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"\n✓ Logged in as: {me.first_name} (@{me.username})")
        print(f"  Phone: {me.phone}")
    else:
        print("\n✗ Login failed!")
        await client.disconnect()
        return
    
    await client.disconnect()
    
    # Copy to growth session
    import shutil
    shutil.copy(
        str(BASE_DIR / "cron_session.session"),
        str(BASE_DIR / "cron_growth_session.session")
    )
    
    print("\n✓ Session files created:")
    print(f"  - cron_session.session")
    print(f"  - cron_growth_session.session")
    print("\n✓ You can now use the CLI automation!")

if __name__ == "__main__":
    asyncio.run(login())
