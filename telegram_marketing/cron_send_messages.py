#!/usr/bin/env python3
"""
CRON: Send Messages - Run this via cron every hour
This script sends messages to all groups once and exits.
Perfect for cron scheduling.
"""

import asyncio
import json
import random
import logging
from datetime import datetime
from pathlib import Path

from telethon import TelegramClient, errors

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
LOG_FILE = SCRIPT_DIR / "cron_messages.log"

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


async def send_messages():
    """Send messages to all groups."""
    
    logger.info("=" * 50)
    logger.info("CRON JOB: Send Messages Started")
    logger.info("=" * 50)
    
    # Load config
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    # Connect
    client = TelegramClient(
        str(SCRIPT_DIR / "cron_session"),
        config['api_id'],
        config['api_hash']
    )
    
    try:
        await client.start(phone=config['phone_number'])
        me = await client.get_me()
        logger.info(f"Connected as: {me.first_name}")
        
        # Get message
        enabled_msgs = [m for m in config['messages'] if m.get('enabled', True)]
        if not enabled_msgs:
            logger.error("No enabled messages!")
            return
        
        message = random.choice(enabled_msgs)['text']
        
        # Get targets
        targets = [t for t in config['targets'] if t.get('enabled', True)]
        delay = config['settings'].get('delay_between_groups_seconds', 30)
        
        logger.info(f"Sending to {len(targets)} targets...")
        
        success = 0
        failed = 0
        
        for i, target in enumerate(targets):
            target_id = target.get('username')
            try:
                if target_id.startswith('@'):
                    entity = await client.get_entity(target_id)
                elif target_id.startswith('ID:'):
                    entity = await client.get_entity(int(target_id[3:]))
                else:
                    entity = await client.get_entity(target_id)
                
                await client.send_message(entity, message)
                success += 1
                logger.info(f"✓ Sent to: {target['name']}")
                
            except errors.FloodWaitError as e:
                logger.warning(f"Flood wait: {e.seconds}s for {target['name']}")
                if e.seconds < 60:
                    await asyncio.sleep(e.seconds)
                else:
                    failed += 1
                    
            except errors.ChatWriteForbiddenError:
                logger.warning(f"No permission: {target['name']}")
                failed += 1
                
            except Exception as e:
                logger.error(f"Error {target['name']}: {str(e)[:50]}")
                failed += 1
            
            # Delay between messages
            if i < len(targets) - 1:
                await asyncio.sleep(delay + random.randint(0, 10))
        
        logger.info(f"Completed: {success}/{len(targets)} successful, {failed} failed")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await client.disconnect()
        logger.info("Disconnected")


if __name__ == "__main__":
    asyncio.run(send_messages())
