#!/usr/bin/env python3
"""
Quick Send Script - Send messages quickly without full setup
Usage: python quick_send.py "@group_name" "Your message here"
"""

import asyncio
import sys
import json
from pathlib import Path
from telethon import TelegramClient

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"


async def quick_send(target: str, message: str):
    """Quickly send a message to a target."""
    
    # Load config
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    api_id = config['api_id']
    api_hash = config['api_hash']
    phone = config['phone_number']
    session_name = config.get('session_name', 'marketing_session')
    
    session_path = SCRIPT_DIR / session_name
    client = TelegramClient(str(session_path), api_id, api_hash)
    
    await client.start(phone=phone)
    print(f"✓ Connected to Telegram")
    
    try:
        entity = await client.get_entity(target)
        await client.send_message(entity, message)
        print(f"✓ Message sent to {target}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python quick_send.py <@target> <message>")
        print("Example: python quick_send.py @mygroup 'Hello everyone!'")
        sys.exit(1)
    
    target = sys.argv[1]
    message = sys.argv[2]
    
    asyncio.run(quick_send(target, message))
