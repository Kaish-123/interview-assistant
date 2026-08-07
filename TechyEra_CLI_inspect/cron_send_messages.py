#!/usr/bin/env python3
"""
Cron-based message sender for Telegram Marketing
Sends messages to all enabled groups
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
LOCK_FILE = BASE_DIR / "telegram_cli.lock"
STATE_FILE = BASE_DIR / "marketing_state.json"
HEALTH_FILE = BASE_DIR / "marketing_health.json"


def load_state():
    default = {"send_cursor": 0}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return {**default, **json.load(f)}
        except Exception:
            pass
    return default.copy()


def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.warning("Could not save marketing state: %s", e)


def write_health(**kwargs):
    """Last run status for debugging (why sends stopped, etc.)."""
    try:
        data = {}
        if HEALTH_FILE.exists():
            with open(HEALTH_FILE) as f:
                data = json.load(f)
        data.update(kwargs)
        data["updated_at"] = datetime.now().isoformat()
        with open(HEALTH_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


async def ensure_client_connected(client):
    if not client.is_connected():
        await client.connect()

def acquire_lock(timeout_sec=90):
    """Ensure only one CLI script uses Telegram at a time."""
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
    
    if not acquire_lock():
        logger.warning("Another CLI script is using Telegram; skipping this run.")
        return
    
    # Single shared session - do not use same session from two processes at once
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
    
    logger.info("Starting message broadcast...")
    
    # Get enabled targets
    targets = [t for t in config['targets'] if t.get('enabled', True)]
    message = random.choice(config['messages'])
    
    sent_count = 0
    error_count = 0
    
    for target in targets:
        username = target['username']
        try:
            entity = await client.get_entity(username)
            await client.send_message(entity, message)
            sent_count += 1
            logger.info(f"✓ Sent to @{username}")
            
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
    release_lock()
    logger.info(f"Broadcast complete: {sent_count} sent, {error_count} errors")


async def send_messages_with_client(client, config):
    """
    Run send using an already-connected client (unified runner).
    Uses round-robin batches so each run finishes quickly and the next 30-min tick can fire.
    """
    await ensure_client_connected(client)
    now = datetime.now()
    start_hour = config["schedule"]["active_hours"]["start"]
    end_hour = config["schedule"]["active_hours"]["end"]
    if not (start_hour <= now.hour < end_hour):
        logger.info("Outside active hours; skipping send.")
        write_health(last_send_skipped="outside_active_hours", last_send_ok=False)
        return

    enabled = [t for t in config["targets"] if t.get("enabled", True)]
    n = len(enabled)
    if n == 0:
        logger.warning("No enabled targets.")
        write_health(last_send_skipped="no_targets", last_send_ok=False)
        return

    write_health(
        last_batch_started_at=datetime.now().isoformat(),
        last_send_skipped=None,
    )

    settings = config.get("settings", {})
    max_per = int(settings.get("max_groups_per_broadcast_round", 30))
    max_per = max(1, min(max_per, n))
    delay_sec = max(0, float(settings.get("delay_between_groups_seconds", 3)))

    message = random.choice(config["messages"])
    state = load_state()
    cursor = int(state.get("send_cursor", 0)) % n

    batch = [enabled[(cursor + i) % n] for i in range(max_per)]
    new_cursor = (cursor + max_per) % n
    state["send_cursor"] = new_cursor
    save_state(state)

    logger.info(
        "Send round: batch %s/%s groups (cursor %s→%s, total enabled=%s)",
        len(batch),
        max_per,
        cursor,
        new_cursor,
        n,
    )

    sent_count = 0
    error_count = 0
    for target in batch:
        username = target["username"]
        try:
            await ensure_client_connected(client)
            entity = await client.get_entity(username)
            await client.send_message(entity, message)
            sent_count += 1
            logger.info(f"✓ Sent to @{username}")
            if delay_sec:
                await asyncio.sleep(delay_sec)
        except FloodWaitError as e:
            need = int(e.seconds)
            # Long waits = usually account-wide limit; do not hit every chat in the batch.
            max_wait_batch = int(settings.get("max_flood_wait_seconds_per_chat", 120))
            if need > max_wait_batch:
                logger.warning(
                    "Flood wait %ss (account-wide). Stopping this batch; retry on next ~30 min tick.",
                    need,
                )
                write_health(
                    global_flood_wait_seconds=need,
                    global_flood_stopped_batch_at=datetime.now().isoformat(),
                    last_flood_username=username,
                )
                error_count += 1
                break
            logger.warning("Flood wait %ss; waiting %ss then retry once...", need, need)
            await asyncio.sleep(need)
            try:
                await ensure_client_connected(client)
                entity = await client.get_entity(username)
                await client.send_message(entity, message)
                sent_count += 1
                logger.info(f"✓ Sent to @{username} (after flood wait)")
                if delay_sec:
                    await asyncio.sleep(delay_sec)
            except Exception as retry_e:
                logger.error(f"✗ @{username} after flood wait: {retry_e}")
                error_count += 1
        except ChatWriteForbiddenError:
            target["enabled"] = False
            error_count += 1
            logger.warning(f"✗ Cannot write @{username} — disabled")
        except ChannelPrivateError:
            target["enabled"] = False
            error_count += 1
        except Exception as e:
            err = str(e)
            el = err.lower()
            if "no user has" in el:
                target["enabled"] = False
            if (
                "chat_send" in el
                or "forbidden" in el
                or "admin privileges" in el
                or "topic_closed" in el
            ):
                target["enabled"] = False
            logger.error(f"✗ @{username}: {e}")
            error_count += 1

    save_config(config)
    logger.info(f"Round complete: {sent_count} sent, {error_count} errors (next batch in schedule)")
    write_health(
        last_send_ok=True,
        last_batch_completed_at=datetime.now().isoformat(),
        last_send_count=sent_count,
        last_send_errors=error_count,
        last_send_batch_size=len(batch),
        total_enabled_groups=n,
        send_cursor=new_cursor,
    )


if __name__ == "__main__":
    asyncio.run(send_messages())
