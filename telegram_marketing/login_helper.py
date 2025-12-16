#!/usr/bin/env python3
"""
Login Helper - Login to Telegram with verification code
Usage: python login_helper.py [code]
"""

import asyncio
import sys
import json
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"


async def login(code=None):
    """Login to Telegram."""
    
    # Load config
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    api_id = config['api_id']
    api_hash = config['api_hash']
    phone = config['phone_number']
    session_name = config.get('session_name', 'marketing_session')
    
    session_path = SCRIPT_DIR / session_name
    client = TelegramClient(str(session_path), api_id, api_hash)
    
    await client.connect()
    
    if not await client.is_user_authorized():
        print(f"📱 Sending code to {phone}...")
        await client.send_code_request(phone)
        
        if code:
            print(f"🔑 Using provided code: {code}")
        else:
            print("\n✅ Code sent to your Telegram app!")
            print("Check your Telegram for the login code.\n")
            code = input("Enter the code: ").strip()
        
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            print("\n🔐 Two-factor authentication enabled!")
            password = input("Enter your 2FA password: ").strip()
            await client.sign_in(password=password)
    
    me = await client.get_me()
    print(f"\n✅ Successfully logged in as: {me.first_name} (@{me.username})")
    print(f"📁 Session saved to: {session_path}.session")
    print("\n🎉 You can now use the marketing tool!")
    
    await client.disconnect()


if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(login(code))

