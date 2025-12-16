#!/usr/bin/env python3
"""Login with 2FA (Two-Factor Authentication) enabled"""
import asyncio
import sys
from telethon import TelegramClient

async def login_with_2fa(code, password):
    client = TelegramClient('techyera_marketing', 34298736, '3281aec7ae61b330628f4d29c47a4cdf')
    await client.connect()
    
    try:
        with open('phone_hash.txt', 'r') as f:
            phone_code_hash = f.read().strip()
    except FileNotFoundError:
        print("❌ Run login_step1.py first!")
        return
    
    try:
        await client.sign_in('+917987460954', code, phone_code_hash=phone_code_hash)
    except Exception as e:
        if "password" in str(e).lower():
            # 2FA required
            await client.sign_in(password=password)
            me = await client.get_me()
            print("="*50)
            print("✅ LOGIN SUCCESSFUL (with 2FA)!")
            print("="*50)
            print(f"\nLogged in as: {me.first_name}")
            print(f"Username: @{me.username}")
        else:
            print(f"❌ Error: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python login_2fa.py YOUR_CODE YOUR_2FA_PASSWORD")
        sys.exit(1)
    
    code = sys.argv[1]
    password = sys.argv[2]
    asyncio.run(login_with_2fa(code, password))
