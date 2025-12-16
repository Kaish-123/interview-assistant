#!/usr/bin/env python3
"""Step 1: Request verification code from Telegram"""
import asyncio
from telethon import TelegramClient

async def request_code():
    client = TelegramClient('techyera_marketing', 34298736, '3281aec7ae61b330628f4d29c47a4cdf')
    await client.connect()
    
    if not await client.is_user_authorized():
        result = await client.send_code_request('+917987460954')
        print("="*50)
        print("✅ CODE SENT TO YOUR TELEGRAM APP!")
        print("="*50)
        print(f"\nPhone hash: {result.phone_code_hash}")
        print("\n👉 Check your Telegram app for the code")
        print("👉 Then run: python login_step2.py YOUR_CODE")
        print("\nExample: python login_step2.py 12345")
        
        # Save phone_code_hash for step 2
        with open('phone_hash.txt', 'w') as f:
            f.write(result.phone_code_hash)
    else:
        me = await client.get_me()
        print(f"✅ Already logged in as: {me.first_name}")
    
    await client.disconnect()

asyncio.run(request_code())
