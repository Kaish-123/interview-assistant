#!/usr/bin/env python3
"""
Cron-based group growth for Telegram Marketing
Finds and joins new groups based on keywords
"""

import asyncio
import json
import random
import logging
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError, UserAlreadyParticipantError
from telethon.tl.functions.channels import JoinChannelRequest

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('growth.log'),
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

async def grow_groups():
    config = load_config()
    
    if not config.get('growth', {}).get('enabled', False):
        logger.info("Growth is disabled in config")
        return
    
    # Initialize client with separate session
    client = TelegramClient(
        str(BASE_DIR / "cron_growth_session"),
        config['api_id'],
        config['api_hash']
    )
    
    await client.start(phone=config['phone'])
    
    if not await client.is_user_authorized():
        logger.error("Not authorized! Please run login first.")
        return
    
    logger.info("Starting group growth...")
    
    keywords = config['growth'].get('keywords', [])
    existing_usernames = {t['username'].lower() for t in config['targets']}
    
    max_joins = random.randint(3, 5)
    joined_count = 0
    
    # Shuffle keywords for variety
    random.shuffle(keywords)
    
    for keyword in keywords:
        if joined_count >= max_joins:
            break
            
        logger.info(f"Searching for: {keyword}")
        
        try:
            from telethon.tl.functions.contacts import SearchRequest
            result = await client(SearchRequest(
                q=keyword,
                limit=20
            ))
            
            for chat in result.chats:
                if joined_count >= max_joins:
                    break
                    
                username = getattr(chat, 'username', None)
                if not username:
                    continue
                    
                if username.lower() in existing_usernames:
                    continue
                
                try:
                    # Try to join
                    await client(JoinChannelRequest(chat))
                    
                    # Verify we can post
                    try:
                        full = await client.get_entity(username)
                        # Add to targets
                        config['targets'].append({
                            "username": username,
                            "enabled": True,
                            "source": "auto_growth"
                        })
                        existing_usernames.add(username.lower())
                        joined_count += 1
                        logger.info(f"✓ Joined @{username}")
                        
                        await asyncio.sleep(random.randint(20, 40))
                        
                    except Exception as e:
                        logger.warning(f"Cannot post to @{username}, leaving...")
                        
                except UserAlreadyParticipantError:
                    logger.info(f"Already in @{username}")
                except ChannelPrivateError:
                    logger.warning(f"@{username} is private")
                except FloodWaitError as e:
                    logger.warning(f"Flood wait: {e.seconds}s")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    logger.error(f"Error joining @{username}: {e}")
                    
        except Exception as e:
            logger.error(f"Error searching '{keyword}': {e}")
            
        await asyncio.sleep(random.randint(5, 10))
    
    # Save updated config
    save_config(config)
    
    await client.disconnect()
    logger.info(f"Growth complete: {joined_count} new groups joined")

if __name__ == "__main__":
    asyncio.run(grow_groups())
