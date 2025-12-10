#!/usr/bin/env python3
"""Step 2: Complete login with the verification code"""
import asyncio
import sys
from telethon import TelegramClient

async def complete_login(code):
    client = TelegramClient('techyera_marketing', 34298736, '3281aec7ae61b330628f4d29c47a4cdf')
    await client.connect()
    
    # Read phone_code_hash
    try:
        with open('phone_hash.txt', 'r') as f:
            phone_code_hash = f.read().strip()
    except FileNotFoundError:
        print("❌ Run login_step1.py first!")
        return
    
    try:
        await client.sign_in('+917987460954', code, phone_code_hash=phone_code_hash)
        me = await client.get_me()
        print("="*50)
        print("✅ LOGIN SUCCESSFUL!")
        print("="*50)
        print(f"\nLogged in as: {me.first_name} {me.last_name or ''}")
        print(f"Username: @{me.username}")
        print(f"Phone: {me.phone}")
        print("\n🎉 You can now use the marketing tool!")
        print("Run: python telegram_marketer.py --list")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        if "password" in str(e).lower():
            print("\n⚠️ You have 2FA enabled. Run: python login_2fa.py YOUR_CODE YOUR_PASSWORD")
    
    await client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python login_step2.py YOUR_CODE")
        print("Example: python login_step2.py 12345")
        sys.exit(1)
    
    code = sys.argv[1]
    asyncio.run(complete_login(code))
