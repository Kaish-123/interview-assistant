#!/usr/bin/env python3
"""
Auto-reply to incoming Telegram DMs: only when someone sends a real message
to talk to you. Ignores service/notification messages (e.g. "X joined from contacts").
"""

import asyncio
import json
import logging
from pathlib import Path
from telethon import events
from telethon.tl.types import MessageService

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
REPLIED_TRACKER_FILE = BASE_DIR / "dm_replied.json"
# Reply at most once per user per 24 hours
REPLY_COOLDOWN_HOURS = 24

DEFAULT_REPLY = (
    "Thanks for reaching out! Please ping me on WhatsApp to discuss – "
    "I'm not active on Telegram.\n\n"
    "WhatsApp: https://wa.link/5vevla"
)


def _load_replied():
    if not REPLIED_TRACKER_FILE.exists():
        return {}
    try:
        with open(REPLIED_TRACKER_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_replied(data):
    try:
        with open(REPLIED_TRACKER_FILE, "w") as f:
            json.dump(data, f, indent=0)
    except Exception as e:
        logger.warning("Could not save DM replied tracker: %s", e)


def _should_reply(user_id: int) -> bool:
    import time
    data = _load_replied()
    now = time.time()
    cutoff = now - (REPLY_COOLDOWN_HOURS * 3600)
    last = data.get(str(user_id), 0)
    if last > cutoff:
        return False
    return True


def _mark_replied(user_id: int):
    import time
    data = _load_replied()
    data[str(user_id)] = time.time()
    _save_replied(data)


def get_reply_message(config: dict) -> str:
    """Get reply text from config or default."""
    dm = config.get("dm_auto_reply", {}) or {}
    return dm.get("reply_message", "").strip() or DEFAULT_REPLY


def register_dm_handler(client, config: dict, client_lock=None):
    """Register handler for incoming private messages. Only replies to real user messages.
    If client_lock is an asyncio.Lock, DM replies wait for send/growth to finish (same session)."""
    dm = config.get("dm_auto_reply", {}) or {}
    if not dm.get("enabled", True):
        logger.info("DM auto-reply is disabled in config.")
        return
    reply_text = get_reply_message(config)

    @client.on(events.NewMessage(incoming=True))
    async def on_new_message(event):
        # Only private (1-on-1) chats
        if not event.is_private:
            return
        # Only messages from users (not channels/bots)
        if not event.sender_id or event.sender_id < 0:
            return
        # Ignore service/notification messages (e.g. "X joined from your contacts", "X joined the group")
        if isinstance(event.message, MessageService):
            return
        # Must have actual text (user wrote something to talk to you)
        if not event.message.text or not event.message.text.strip():
            return
        # Optional: ignore messages from Telegram itself (e.g. "Login code")
        try:
            sender = await event.get_sender()
            if sender and getattr(sender, "bot", False):
                return
        except Exception:
            pass

        user_id = event.sender_id
        if not _should_reply(user_id):
            return

        try:
            if client_lock is not None:
                async with client_lock:
                    await event.respond(reply_text)
            else:
                await event.respond(reply_text)
            _mark_replied(user_id)
            name = getattr((await event.get_sender()), "first_name", "") or "User"
            logger.info("DM auto-reply sent to %s (id=%s)", name, user_id)
        except Exception as e:
            logger.error("DM auto-reply failed for user %s: %s", user_id, e)

    logger.info("DM auto-reply handler registered (reply once per user per %sh)", REPLY_COOLDOWN_HOURS)
