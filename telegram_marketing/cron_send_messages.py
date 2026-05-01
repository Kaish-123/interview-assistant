#!/usr/bin/env python3
"""
CRON: Send Messages - Run this via launchd every hour
This script sends messages to all enabled groups once and exits.

FIXED:
- Clears stale SQLite journal before connecting (prevents "database is locked")
- Tracks permanently failing targets and auto-disables them after 3 consecutive fails
- Handles FloodWait gracefully (waits if short, skips if long)
- Saves failure state to config so watchdog can pick it up
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
FAIL_TRACK_FILE = SCRIPT_DIR / "fail_tracker.json"

# After this many consecutive failures, a target is auto-disabled
MAX_CONSECUTIVE_FAILS = 3

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


def load_fail_tracker():
    """Load consecutive failure counts per target username."""
    if FAIL_TRACK_FILE.exists():
        try:
            with open(FAIL_TRACK_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_fail_tracker(tracker):
    with open(FAIL_TRACK_FILE, 'w') as f:
        json.dump(tracker, f, indent=2)


def clear_stale_journal(session_path):
    """Remove stale SQLite journal file that causes 'database is locked' errors."""
    journal = Path(str(session_path) + ".session-journal")
    if journal.exists():
        try:
            journal.unlink()
            logger.info(f"Cleared stale journal: {journal.name}")
        except Exception as e:
            logger.warning(f"Could not clear journal: {e}")


def is_permanent_error(error_str):
    """Returns True if this error means we should never retry this target."""
    permanent_keywords = [
        "no permission",
        "chatwriteforbidden",
        "private and you lack perm",
        "you were banned",
        "could not find the input entity",
        "channelprivateerror",
        "userbannedinchannel",
    ]
    err_lower = error_str.lower()
    return any(kw in err_lower for kw in permanent_keywords)


async def send_messages():
    """Send messages to all groups."""

    logger.info("=" * 50)
    logger.info("CRON JOB: Send Messages Started")
    logger.info(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # Load config and fail tracker
    config = load_config()
    fail_tracker = load_fail_tracker()

    session_path = SCRIPT_DIR / "cron_session"
    clear_stale_journal(session_path)

    client = TelegramClient(
        str(session_path),
        config['api_id'],
        config['api_hash']
    )

    config_changed = False

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

        # Get targets (only enabled ones)
        targets = [t for t in config['targets'] if t.get('enabled', True)]
        delay = config['settings'].get('delay_between_groups_seconds', 30)

        logger.info(f"Sending to {len(targets)} enabled targets...")

        success = 0
        failed = 0
        auto_disabled = 0

        for i, target in enumerate(targets):
            target_id = target.get('username', '')
            target_name = target.get('name', target_id)

            try:
                if target_id.startswith('@'):
                    entity = await client.get_entity(target_id)
                elif target_id.startswith('ID:'):
                    entity = await client.get_entity(int(target_id[3:]))
                else:
                    entity = await client.get_entity(target_id)

                await client.send_message(entity, message)
                success += 1
                logger.info(f"✓ Sent to: {target_name}")

                # Reset fail counter on success
                if target_id in fail_tracker:
                    del fail_tracker[target_id]

            except errors.FloodWaitError as e:
                logger.warning(f"Flood wait: {e.seconds}s for {target_name}")
                if e.seconds <= 120:
                    await asyncio.sleep(e.seconds)
                    # Retry once after flood wait
                    try:
                        await client.send_message(entity, message)
                        success += 1
                        logger.info(f"✓ Sent to (retry): {target_name}")
                        continue
                    except Exception:
                        pass
                failed += 1

            except errors.ChatWriteForbiddenError:
                logger.warning(f"No permission: {target_name}")
                fail_tracker[target_id] = fail_tracker.get(target_id, 0) + 1
                failed += 1

            except Exception as e:
                err_str = str(e)
                logger.error(f"Error {target_name}: {err_str[:80]}")

                if is_permanent_error(err_str):
                    fail_tracker[target_id] = fail_tracker.get(target_id, 0) + 1
                    logger.warning(f"  → Permanent error type. Fail count: {fail_tracker[target_id]}/{MAX_CONSECUTIVE_FAILS}")
                failed += 1

            # Auto-disable targets that keep permanently failing
            if fail_tracker.get(target_id, 0) >= MAX_CONSECUTIVE_FAILS:
                for t in config['targets']:
                    if t.get('username') == target_id and t.get('enabled', True):
                        t['enabled'] = False
                        config_changed = True
                        auto_disabled += 1
                        logger.warning(f"AUTO-DISABLED: {target_name} (failed {MAX_CONSECUTIVE_FAILS}x in a row)")
                        break

            # Delay between sends
            if i < len(targets) - 1:
                wait = delay + random.randint(0, 10)
                await asyncio.sleep(wait)

        summary = (f"Completed: {success}/{len(targets)} successful, "
                   f"{failed} failed, {auto_disabled} auto-disabled")
        logger.info(summary)

        # Save updated config if targets were disabled
        if config_changed:
            save_config(config)
            logger.info("Config saved with auto-disabled targets.")

        save_fail_tracker(fail_tracker)

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
    asyncio.run(send_messages())
