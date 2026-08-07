#!/usr/bin/env python3
"""
Aggressive group growth for Telegram Marketing
Finds and joins new groups using multiple strategies
"""

import asyncio
import json
import os
import random
import logging
import time
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError, UserAlreadyParticipantError, ChatAdminRequiredError
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel, Chat, ChannelParticipantsSearch

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
LOCK_FILE = BASE_DIR / "telegram_cli.lock"

def acquire_lock(timeout_sec=120):
    for _ in range(timeout_sec):
        if not LOCK_FILE.exists():
            LOCK_FILE.write_text(str(os.getpid()))
            return True
        try:
            pid = int(LOCK_FILE.read_text().strip())
            if pid == os.getpid():
                return True
            try:
                os.kill(pid, 0)
            except (OSError, ProcessLookupError):
                LOCK_FILE.unlink(missing_ok=True)
                continue
        except Exception:
            LOCK_FILE.unlink(missing_ok=True)
            continue
        time.sleep(1)
    return False

def release_lock():
    try:
        if LOCK_FILE.exists() and LOCK_FILE.read_text().strip() == str(os.getpid()):
            LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass

# Expanded keyword list for better discovery
GROWTH_KEYWORDS = [
    # Core proxy/interview keywords
    "proxy interview", "interview support", "proxy support",
    "job support", "work support", "interview help",
    
    # Tech job keywords
    "data engineer", "data analyst", "fullstack developer",
    "python developer", "java developer", "react developer",
    "software engineer", "backend developer", "frontend developer",
    "devops engineer", "cloud engineer", "AWS jobs",
    
    # Remote/Freelance keywords
    "remote jobs", "remote work", "freelance developer",
    "IT jobs USA", "IT jobs India", "tech jobs",
    "software jobs", "developer jobs", "coding jobs",
    
    # Consultancy keywords
    "IT consultancy", "tech consultancy", "IT training",
    "job placement", "IT placement", "tech placement",
    
    # Specific tech keywords
    "python jobs", "java jobs", "javascript jobs",
    "react jobs", "node jobs", "angular jobs",
    "sql jobs", "database jobs", "ETL jobs",
    "power bi", "tableau jobs", "data science",
    
    # Interview specific
    "mock interview", "technical interview", "coding interview",
    "interview preparation", "interview tips",
    
    # Regional keywords
    "USA IT", "Canada IT", "UK IT jobs",
    "H1B jobs", "OPT jobs", "visa sponsorship"
]

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

async def can_post_to_group(client, entity):
    """Check if we can post to this group"""
    try:
        from telethon.tl.types import Channel, Chat
        
        if isinstance(entity, Channel):
            if entity.broadcast and not entity.megagroup:
                # It's a channel, not a group - check admin rights
                if not entity.admin_rights or not entity.admin_rights.post_messages:
                    return False
            # For megagroups (supergroups), check if we can send
            if hasattr(entity, 'default_banned_rights'):
                if entity.default_banned_rights and entity.default_banned_rights.send_messages:
                    return False
        return True
    except Exception:
        return False

async def grow_groups():
    config = load_config()
    
    if not config.get('growth', {}).get('enabled', False):
        logger.info("Growth is disabled in config")
        return
    
    if not acquire_lock():
        logger.warning("Another CLI script is using Telegram; skipping this run.")
        return
    
    # Single shared session (same as send) - prevents AuthKeyDuplicatedError
    client = TelegramClient(
        str(BASE_DIR / "techyera_cli_session"),
        config['api_id'],
        config['api_hash']
    )
    
    try:
        await client.start(phone=config['phone'])
    except Exception as e:
        release_lock()
        raise
    
    if not await client.is_user_authorized():
        logger.error("Not authorized! Please run login first.")
        release_lock()
        return
    
    logger.info("Starting aggressive group growth...")
    
    # Get existing usernames
    existing_usernames = {t['username'].lower().replace('@', '') for t in config['targets']}
    logger.info(f"Currently have {len(existing_usernames)} groups")
    
    max_joins = random.randint(5, 10)  # Increased from 3-5
    joined_count = 0
    checked_count = 0
    
    # Combine config keywords with expanded list
    config_keywords = config['growth'].get('keywords', [])
    all_keywords = list(set(GROWTH_KEYWORDS + config_keywords))
    random.shuffle(all_keywords)
    
    # Track groups we've already checked this session
    checked_groups = set()
    
    for keyword in all_keywords:
        if joined_count >= max_joins:
            logger.info(f"Reached max joins ({max_joins}), stopping.")
            break
        
        logger.info(f"🔍 Searching: '{keyword}'")
        
        try:
            # Search with higher limit
            result = await client(SearchRequest(
                q=keyword,
                limit=50  # Increased from 20
            ))
            
            found_new = 0
            for chat in result.chats:
                if joined_count >= max_joins:
                    break
                
                username = getattr(chat, 'username', None)
                if not username:
                    continue
                
                username_lower = username.lower()
                
                # Skip if already have or already checked
                if username_lower in existing_usernames:
                    continue
                if username_lower in checked_groups:
                    continue
                
                checked_groups.add(username_lower)
                checked_count += 1
                
                # Check if it's a group we can post to
                try:
                    # Get full entity info
                    entity = await client.get_entity(username)
                    
                    # Skip channels (broadcasts), only want groups
                    if isinstance(entity, Channel):
                        if entity.broadcast and not entity.megagroup:
                            logger.debug(f"Skipping channel @{username}")
                            continue
                    
                    # Try to join
                    try:
                        await client(JoinChannelRequest(entity))
                        await asyncio.sleep(2)  # Wait a bit after joining
                        
                        # Re-fetch to check permissions
                        entity = await client.get_entity(username)
                        
                        # Verify we can post
                        if await can_post_to_group(client, entity):
                            # Add to targets
                            config['targets'].append({
                                "username": username,
                                "enabled": True,
                                "source": "auto_growth",
                                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            existing_usernames.add(username_lower)
                            joined_count += 1
                            found_new += 1
                            logger.info(f"✅ Joined @{username} ({joined_count}/{max_joins})")
                            
                            # Save after each successful join
                            save_config(config)
                            
                            # Delay to avoid rate limits
                            await asyncio.sleep(random.randint(15, 30))
                        else:
                            logger.info(f"⚠️ Cannot post to @{username}, leaving...")
                            try:
                                await client(LeaveChannelRequest(entity))
                            except:
                                pass
                            
                    except UserAlreadyParticipantError:
                        # Already in group, add to targets if not there
                        if username_lower not in existing_usernames:
                            if await can_post_to_group(client, entity):
                                config['targets'].append({
                                    "username": username,
                                    "enabled": True,
                                    "source": "existing_member",
                                    "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                                })
                                existing_usernames.add(username_lower)
                                joined_count += 1
                                logger.info(f"✅ Added existing @{username}")
                                save_config(config)
                                
                    except ChannelPrivateError:
                        logger.debug(f"Private: @{username}")
                    except FloodWaitError as e:
                        logger.warning(f"⏳ Flood wait: {e.seconds}s - waiting...")
                        await asyncio.sleep(e.seconds + 5)
                    except Exception as e:
                        error_msg = str(e)
                        if "request to join" in error_msg.lower():
                            logger.info(f"📩 Join request sent to @{username}")
                        else:
                            logger.debug(f"Error with @{username}: {e}")
                            
                except Exception as e:
                    logger.debug(f"Error checking @{username}: {e}")
                    continue
            
            if found_new > 0:
                logger.info(f"Found {found_new} new groups from '{keyword}'")
                
        except FloodWaitError as e:
            logger.warning(f"⏳ Search flood wait: {e.seconds}s")
            await asyncio.sleep(e.seconds + 5)
        except Exception as e:
            logger.error(f"Search error for '{keyword}': {e}")
        
        # Small delay between searches
        await asyncio.sleep(random.randint(3, 8))
    
    await client.disconnect()
    release_lock()
    
    logger.info(f"="*50)
    logger.info(f"🎯 Growth complete!")
    logger.info(f"   Checked: {checked_count} groups")
    logger.info(f"   Joined: {joined_count} new groups")
    logger.info(f"   Total groups now: {len(config['targets'])}")
    logger.info(f"="*50)


async def grow_groups_with_client(client, config):
    """Run growth logic using an already-connected client (for unified runner). No lock."""
    if not client.is_connected():
        await client.connect()
    if not config.get("growth", {}).get("enabled", False):
        logger.info("Growth disabled; skipping.")
        return
    existing_usernames = {t["username"].lower().replace("@", "") for t in config["targets"]}
    max_joins = random.randint(5, 10)
    joined_count = 0
    config_keywords = config["growth"].get("keywords", [])
    all_keywords = list(set(GROWTH_KEYWORDS + config_keywords))
    random.shuffle(all_keywords)
    checked_groups = set()
    for keyword in all_keywords:
        if joined_count >= max_joins:
            break
        logger.info(f"🔍 Searching: '{keyword}'")
        try:
            result = await client(SearchRequest(q=keyword, limit=50))
            for chat in result.chats:
                if joined_count >= max_joins:
                    break
                username = getattr(chat, "username", None)
                if not username or username.lower() in existing_usernames or username.lower() in checked_groups:
                    continue
                checked_groups.add(username.lower())
                try:
                    entity = await client.get_entity(username)
                    if isinstance(entity, Channel) and entity.broadcast and not entity.megagroup:
                        continue
                    try:
                        await client(JoinChannelRequest(entity))
                        await asyncio.sleep(2)
                        entity = await client.get_entity(username)
                        if await can_post_to_group(client, entity):
                            config["targets"].append({
                                "username": username,
                                "enabled": True,
                                "source": "auto_growth",
                                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            })
                            existing_usernames.add(username.lower())
                            joined_count += 1
                            logger.info(f"✅ Joined @{username}")
                            save_config(config)
                            await asyncio.sleep(random.randint(15, 30))
                        else:
                            try:
                                await client(LeaveChannelRequest(entity))
                            except Exception:
                                pass
                    except UserAlreadyParticipantError:
                        if username.lower() not in existing_usernames and await can_post_to_group(client, entity):
                            config["targets"].append({
                                "username": username,
                                "enabled": True,
                                "source": "existing_member",
                                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            })
                            existing_usernames.add(username.lower())
                            joined_count += 1
                            logger.info(f"✅ Added existing @{username}")
                            save_config(config)
                    except (ChannelPrivateError, FloodWaitError):
                        pass
                    except Exception as e:
                        if "request to join" not in str(e).lower():
                            logger.debug("Error joining @%s: %s", username, e)
                except Exception:
                    pass
        except FloodWaitError as e:
            await asyncio.sleep(min(e.seconds + 5, 3600))
        except Exception as e:
            logger.error("Search '%s': %s", keyword, e)
        await asyncio.sleep(random.randint(3, 8))
    logger.info("Growth complete: %d joined, %d total groups", joined_count, len(config["targets"]))


if __name__ == "__main__":
    asyncio.run(grow_groups())
