#!/usr/bin/env python3
"""
CRON: Growth - Run this via cron every 6 hours
This script finds new groups, joins them, and adds to config.

FIXED:
- Startup stagger delay (avoids SQLite "database is locked" when both jobs launch together)
- Retry logic for database locked errors
- Skips already-joined groups gracefully
"""

import asyncio
import json
import random
import logging
import time
import os
from datetime import datetime
from pathlib import Path

from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
LOG_FILE = SCRIPT_DIR / "cron_growth.log"

# Search keywords — covers proxy/interview, IT jobs, cloud, data, USA work support
SEARCH_KEYWORDS = [
    # Core business — proxy & interview support
    "proxy interview", "interview proxy", "proxy job support", "interview support USA",
    "proxy interview support", "proxy job USA", "interview coaching IT",
    "remote interview support", "online interview proxy", "live interview support",

    # Data & cloud roles
    "data engineer", "data analyst", "data science jobs", "data engineering jobs",
    "big data jobs", "cloud data engineer", "ETL developer", "SQL developer",
    "database developer", "snowflake developer", "databricks jobs",
    "machine learning jobs", "AI jobs", "MLOps jobs", "data warehouse jobs",

    # Development roles
    "full stack developer", "python developer", "java developer",
    "nodejs developer", "react developer", "angular developer",
    "backend developer", "frontend developer", "web developer",
    "mobile developer", "flutter developer", "android developer",

    # Cloud & DevOps
    "aws jobs", "azure jobs", "cloud jobs", "devops jobs", "kubernetes jobs",
    "cloud architect", "GCP jobs", "cloud engineer", "terraform jobs",
    "site reliability engineer", "platform engineer",

    # Salesforce & enterprise
    "salesforce developer", "salesforce jobs", "salesforce proxy",
    "SAP jobs", "ServiceNow jobs",

    # IT general & fresher
    "IT jobs USA", "software developer", "tech jobs", "fresher IT jobs",
    "IT placement", "developer jobs", "IT recruitment", "coding jobs",
    "software jobs", "software engineering", "tech interview", "coding interview",

    # USA visa / international workers
    "H1B jobs", "OPT jobs", "CPT jobs", "L1 visa jobs", "USA work permit IT",
    "job support H1B", "IT job support", "work from home IT",

    # Community & networking
    "IT professionals group", "tech community", "developer community",
    "software engineer group", "remote work IT", "freelance developer",
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


def clear_stale_journal(session_path):
    """Remove stale SQLite journal file that causes 'database is locked' errors."""
    journal = Path(str(session_path) + ".session-journal")
    if journal.exists():
        try:
            journal.unlink()
            logger.info(f"Cleared stale journal: {journal.name}")
        except Exception as e:
            logger.warning(f"Could not clear journal: {e}")


async def connect_with_retry(session_path, api_id, api_hash, phone, max_retries=3):
    """Connect to Telegram with retry on database-locked errors."""
    for attempt in range(max_retries):
        try:
            clear_stale_journal(session_path)
            client = TelegramClient(str(session_path), api_id, api_hash)
            await client.start(phone=phone)
            return client
        except Exception as e:
            err = str(e).lower()
            if "database is locked" in err or "sqlite" in err:
                wait = 30 * (attempt + 1)
                logger.warning(f"DB locked on attempt {attempt+1}/{max_retries}, retrying in {wait}s...")
                await asyncio.sleep(wait)
            else:
                raise
    raise RuntimeError("Could not acquire session after multiple retries (database locked)")


async def run_growth():
    """Find and join new groups."""

    logger.info("=" * 50)
    logger.info("CRON JOB: Growth Started")
    logger.info("=" * 50)

    # ── STAGGER DELAY ──────────────────────────────────────────────────────────
    # Both launchd jobs fire at the same time when MacOS boots or jobs are loaded.
    # This delay ensures the send-messages job gets the DB first and we don't collide.
    stagger = random.randint(90, 150)
    logger.info(f"Startup stagger: waiting {stagger}s to avoid session collision with send job...")
    await asyncio.sleep(stagger)
    # ──────────────────────────────────────────────────────────────────────────

    config = load_config()

    # Get existing usernames
    existing = {t.get('username', '').lower() for t in config['targets']}
    logger.info(f"Current targets: {len(existing)}")

    session_path = SCRIPT_DIR / "cron_growth_session"

    try:
        client = await connect_with_retry(session_path, config['api_id'], config['api_hash'], config['phone_number'])
        me = await client.get_me()
        logger.info(f"Connected as: {me.first_name}")

        # Search for groups
        found_groups = []
        keywords = random.sample(SEARCH_KEYWORDS, min(15, len(SEARCH_KEYWORDS)))

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
            except errors.FloodWaitError as e:
                logger.warning(f"Flood wait during search: {e.seconds}s")
                await asyncio.sleep(min(e.seconds, 60))
            except Exception as e:
                logger.error(f"Search error for '{keyword}': {e}")

        # Sort by members
        found_groups.sort(key=lambda x: x.get('members', 0), reverse=True)
        logger.info(f"Found {len(found_groups)} new groups")

        # Join top 3-5 groups
        joined = 0
        max_joins = random.randint(5, 8)

        for group in found_groups[:max_joins]:
            try:
                logger.info(f"Joining {group['username']} ({group.get('members', '?')} members)...")
                entity = await client.get_entity(group['username'])
                await client(JoinChannelRequest(entity))

                # Add to config
                config['targets'].append({
                    'name': f"{group['title'][:35]} ({group.get('members', '?')})",
                    'username': group['username'],
                    'enabled': True
                })
                # Update existing set so we don't double-add
                existing.add(group['username'].lower())
                joined += 1
                logger.info(f"✓ Joined: {group['title']}")

                await asyncio.sleep(random.randint(20, 40))

            except errors.FloodWaitError as e:
                logger.warning(f"Rate limited during join: {e.seconds}s - stopping joins")
                break
            except errors.UserAlreadyParticipantError:
                logger.info(f"Already member: {group['username']}")
            except errors.ChannelsTooMuchError:
                logger.warning("Joined too many channels - Telegram limit hit, stopping growth")
                break
            except Exception as e:
                logger.error(f"Join failed for {group['username']}: {e}")

        if joined > 0:
            save_config(config)
            logger.info(f"Config updated! Added {joined} groups. Total: {len(config['targets'])}")
        else:
            logger.info("No new groups joined this cycle.")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        try:
            await client.disconnect()
            logger.info("Disconnected")
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(run_growth())
