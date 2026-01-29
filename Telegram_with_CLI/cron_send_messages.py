#!/usr/bin/env python3
"""
Cron-based message sender for Telegram Marketing
Sends messages to all enabled groups
"""

import asyncio
import json
import random
import logging
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChatWriteForbiddenError, ChannelPrivateError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('send_messages.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

async def send_messages():
    config = load_config()
    
    # Check active hours
    now = datetime.now()
    start_hour = config['schedule']['active_hours']['start']
    end_hour = config['schedule']['active_hours']['end']
    
    if not (start_hour <= now.hour < end_hour):
        logger.info(f"Outside active hours ({start_hour}:00 - {end_hour}:00). Skipping...")
        return
    
    # Initialize client with separate session
    client = TelegramClient(
        str(BASE_DIR / "cron_session"),
        config['api_id'],
        config['api_hash']
    )
    
    await client.start(phone=config['phone'])
    
    if not await client.is_user_authorized():
        logger.error("Not authorized! Please run login first.")
        return
    
    logger.info("Starting message broadcast...")
    
    # Get enabled targets
    targets = [t for t in config['targets'] if t.get('enabled', True)]
    message = random.choice(config['messages'])
    delay = config['settings']['delay_between_groups_seconds']
    
    sent_count = 0
    error_count = 0
    
    for target in targets:
        username = target['username']
        try:
            entity = await client.get_entity(username)
            await client.send_message(entity, message)
            sent_count += 1
            logger.info(f"✓ Sent to @{username}")
            
            # Add random delay
            await asyncio.sleep(delay + random.randint(0, 10))
            
        except FloodWaitError as e:
            logger.warning(f"Flood wait: {e.seconds}s. Stopping for now.")
            break
        except ChatWriteForbiddenError:
            logger.warning(f"✗ Cannot write to @{username} - disabling")
            target['enabled'] = False
            error_count += 1
        except ChannelPrivateError:
            logger.warning(f"✗ Channel @{username} is private - disabling")
            target['enabled'] = False
            error_count += 1
        except Exception as e:
            logger.error(f"✗ Error sending to @{username}: {e}")
            error_count += 1
    
    # Save updated config if any targets were disabled
    save_config(config)
    
    await client.disconnect()
    logger.info(f"Broadcast complete: {sent_count} sent, {error_count} errors")

if __name__ == "__main__":
    asyncio.run(send_messages())
