#!/usr/bin/env python3
"""
CRON: Growth - Run this via cron every 6 hours
This script finds new groups, joins them, and adds to config.
"""

import asyncio
import json
import random
import logging
from datetime import datetime
from pathlib import Path

from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
LOG_FILE = SCRIPT_DIR / "cron_growth.log"

# Search keywords
SEARCH_KEYWORDS = [
    "proxy interview", "interview proxy", "job support", "interview support",
    "data engineer", "data analyst", "full stack developer", "python developer",
    "java developer", "devops jobs", "IT jobs USA", "software developer",
    "tech jobs", "fresher IT jobs", "IT placement", "developer jobs",
    "aws jobs", "azure jobs", "cloud jobs", "remote developer",
    "web developer", "backend developer", "frontend developer",
    "IT recruitment", "coding jobs", "software jobs"
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


async def run_growth():
    """Find and join new groups."""
    
    logger.info("=" * 50)
    logger.info("CRON JOB: Growth Started")
    logger.info("=" * 50)
    
    config = load_config()
    
    # Get existing usernames
    existing = {t.get('username', '').lower() for t in config['targets']}
    logger.info(f"Current targets: {len(existing)}")
    
    # Connect
    client = TelegramClient(
        str(SCRIPT_DIR / "cron_growth_session"),
        config['api_id'],
        config['api_hash']
    )
    
    try:
        await client.start(phone=config['phone_number'])
        me = await client.get_me()
        logger.info(f"Connected as: {me.first_name}")
        
        # Search for groups
        found_groups = []
        keywords = random.sample(SEARCH_KEYWORDS, min(8, len(SEARCH_KEYWORDS)))
        
        for keyword in keywords:
            try:
                logger.info(f"Searching: {keyword}")
                result = await client(SearchRequest(q=keyword, limit=25))
                
                for chat in result.chats:
                    if isinstance(chat, Channel) and chat.megagroup:
                        username = f"@{chat.username}" if chat.username else None
                        if username and username.lower() not in existing:
                            if username.lower() not in [g['username'].lower() for g in found_groups]:
                                members = getattr(chat, 'participants_count', 0) or 0
                                found_groups.append({
                                    'title': chat.title,
                                    'username': username,
                                    'members': members
                                })
                
                await asyncio.sleep(1.5)
            except Exception as e:
                logger.error(f"Search error: {e}")
        
        # Sort by members
        found_groups.sort(key=lambda x: x.get('members', 0), reverse=True)
        logger.info(f"Found {len(found_groups)} new groups")
        
        # Join top 3-5 groups
        joined = 0
        max_joins = random.randint(3, 5)
        
        for group in found_groups[:max_joins]:
            try:
                logger.info(f"Joining {group['username']}...")
                entity = await client.get_entity(group['username'])
                await client(JoinChannelRequest(entity))
                
                # Add to config
                config['targets'].append({
                    'name': f"{group['title'][:35]} ({group.get('members', '?')})",
                    'username': group['username'],
                    'enabled': True
                })
                joined += 1
                logger.info(f"✓ Joined: {group['title']}")
                
                await asyncio.sleep(random.randint(20, 40))
                
            except errors.FloodWaitError as e:
                logger.warning(f"Rate limited: {e.seconds}s")
                break
            except errors.UserAlreadyParticipantError:
                logger.info(f"Already member: {group['username']}")
            except Exception as e:
                logger.error(f"Join failed: {e}")
        
        if joined > 0:
            save_config(config)
            logger.info(f"Config updated! Added {joined} groups. Total: {len(config['targets'])}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await client.disconnect()
        logger.info("Disconnected")


if __name__ == "__main__":
    asyncio.run(run_growth())
