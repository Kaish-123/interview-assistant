#!/usr/bin/env python3
"""
Unified Telegram automation: group broadcast (batched, on schedule), growth, DM auto-reply.
One process, one session. Intervals read from config.json (schedule.interval_minutes, growth).
"""

import asyncio
import json
import logging
import sys
import time
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import FloodWaitError

from cron_send_messages import load_config, send_messages_with_client
from cron_growth import load_config as load_config_growth, grow_groups_with_client
from dm_auto_reply import register_dm_handler

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
SESSION_FILE = BASE_DIR / "techyera_cli_session"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        # Rotating instead of plain FileHandler: caps growth at 20MB x 5 backups
        # instead of the unbounded 250MB+ files this was producing before.
        RotatingFileHandler(
            BASE_DIR / "unified_runner.log", maxBytes=20 * 1024 * 1024, backupCount=5
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

DEFAULT_SEND_INTERVAL_SEC = 30 * 60
DEFAULT_GROWTH_INTERVAL_SEC = 2 * 3600


def send_interval_sec(config: dict) -> int:
    mins = int(config.get("schedule", {}).get("interval_minutes", 30))
    return max(60, mins * 60)


def growth_interval_sec(config: dict) -> int:
    hours = float(config.get("growth", {}).get("check_interval_hours", 2))
    return max(300, int(hours * 3600))


async def send_loop(client, client_lock: asyncio.Lock):
    """
    Cadence: next batch starts ~interval_minutes after THIS batch *started* (not after it ends).
    So you get steady ~30 min ticks even when each batch is short. If a batch runs longer than
    the interval, we only pause min_pause seconds (avoids stacking delays forever).
    """
    while True:
        interval = DEFAULT_SEND_INTERVAL_SEC
        min_pause = 60
        try:
            cfg = load_config()
            interval = send_interval_sec(cfg)
            min_pause = max(30, int(cfg.get("schedule", {}).get("min_pause_between_batches_seconds", 60)))
        except Exception:
            pass

        t_start = time.monotonic()
        try:
            logger.info(
                "Starting send round (target cadence: every %s min from batch start)...",
                interval // 60,
            )
            async with client_lock:
                await send_messages_with_client(client, load_config())
        except Exception as e:
            logger.error("Send loop error: %s\n%s", e, traceback.format_exc())
            try:
                health_path = BASE_DIR / "marketing_health.json"
                data = {}
                if health_path.exists():
                    with open(health_path) as f:
                        data = json.load(f)
                data["last_send_error"] = str(e)
                data["last_send_error_trace"] = traceback.format_exc()[:2000]
                data["last_send_loop_crash_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                with open(health_path, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass

        elapsed = time.monotonic() - t_start
        sleep_sec = max(min_pause, interval - elapsed)
        try:
            health_path = BASE_DIR / "marketing_health.json"
            data = {}
            if health_path.exists():
                with open(health_path) as f:
                    data = json.load(f)
            data["last_send_cadence_sleep_sec"] = round(sleep_sec, 1)
            data["last_send_batch_duration_sec"] = round(elapsed, 1)
            data["last_send_interval_sec"] = interval
            with open(health_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

        logger.info(
            "Send cadence: batch took %.1f s → sleeping %.1f s (~%.1f min until next batch start)",
            elapsed,
            sleep_sec,
            sleep_sec / 60.0,
        )
        await asyncio.sleep(sleep_sec)


def _growth_pause_remaining(cfg: dict) -> float:
    """Seconds remaining on a flood-wait cooldown pause, or 0 if not paused.
    Set by growth_loop itself when Telegram returns an account-wide flood wait,
    and checked here so growth auto-resumes with no manual intervention."""
    paused_until = cfg.get("growth", {}).get("paused_until_epoch")
    if not paused_until:
        return 0.0
    return max(0.0, float(paused_until) - time.time())


def _set_growth_pause(seconds: float):
    """Persist a pause window to config.json so it survives restarts."""
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        cfg.setdefault("growth", {})["paused_until_epoch"] = time.time() + seconds
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
        logger.warning(
            "Growth auto-paused for %.1f h (flood-wait cooldown) — will resume automatically.",
            seconds / 3600.0,
        )
    except Exception as e:
        logger.error("Could not persist growth pause: %s", e)


async def growth_loop(client, client_lock: asyncio.Lock):
    """Growth on a fixed period from cycle start (same cadence idea as send)."""
    await asyncio.sleep(120)
    while True:
        interval = DEFAULT_GROWTH_INTERVAL_SEC
        min_pause = 120
        cfg = {}
        try:
            cfg = load_config_growth()
            interval = growth_interval_sec(cfg)
            min_pause = max(60, int(cfg.get("growth", {}).get("min_pause_after_cycle_seconds", 120)))
        except Exception:
            pass

        remaining = _growth_pause_remaining(cfg)
        if remaining > 0:
            check_in = min(interval, max(300, remaining + 60))
            logger.info(
                "Growth paused (flood-wait cooldown) — %.1f h remaining, checking again in %.1f min",
                remaining / 3600.0,
                check_in / 60.0,
            )
            await asyncio.sleep(check_in)
            continue

        t_start = time.monotonic()
        try:
            logger.info("Starting growth cycle...")
            async with client_lock:
                await grow_groups_with_client(client, load_config_growth())
        except FloodWaitError as e:
            # Account-wide flood wait: back off growth automatically (with a
            # buffer) instead of hammering Telegram again next cycle. Clears
            # itself once the pause window elapses — no manual step needed.
            logger.error("Growth hit FloodWaitError (%ss) — auto-pausing growth.", e.seconds)
            _set_growth_pause(e.seconds + 600)
        except Exception as e:
            logger.error("Growth loop error: %s\n%s", e, traceback.format_exc())

        elapsed = time.monotonic() - t_start
        sleep_sec = max(min_pause, interval - elapsed)
        logger.info(
            "Growth cadence: cycle took %.1f s → sleeping %.1f s until next growth",
            elapsed,
            sleep_sec,
        )
        await asyncio.sleep(sleep_sec)


async def run_session():
    """One connected session: DM + send loop + growth loop until disconnect.

    IMPORTANT: every path out of this function (normal disconnect OR any
    exception) must cancel the send/growth tasks and disconnect the client
    before returning. Previously the tasks + client from each reconnect were
    left running/open forever, so every reconnect over the runner's uptime
    leaked a full TelegramClient (socket + SQLite handle) and two infinite
    loops stuck retrying against a dead connection. That's what exhausted
    the process's file descriptors after ~17 days uptime.
    """
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    client = TelegramClient(
        str(SESSION_FILE),
        config["api_id"],
        config["api_hash"],
    )
    tasks = []
    try:
        await client.start(phone=config["phone"])
        if not await client.is_user_authorized():
            logger.error("Not authorized. Run login first.")
            return
        sm = config.get("schedule", {}).get("interval_minutes", 30)
        gh = config.get("growth", {}).get("check_interval_hours", 2)
        logger.info(
            "Unified runner: send every %s min (batched rounds), growth every %s h, DM auto-reply on.",
            sm,
            gh,
        )
        client_lock = asyncio.Lock()
        register_dm_handler(client, config, client_lock)
        tasks = [
            asyncio.create_task(send_loop(client, client_lock)),
            asyncio.create_task(growth_loop(client, client_lock)),
        ]
        await client.run_until_disconnected()
    finally:
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        try:
            if client.is_connected():
                await client.disconnect()
        except Exception:
            pass


async def main():
    """
    Never stay down: if Telegram disconnects or the process errors, wait and reconnect.
    Keeps 30-minute send cadence and DM/growth running across network blips.
    """
    backoff = 15
    while True:
        try:
            await run_session()
            logger.warning(
                "Session ended (disconnect). Reconnecting in %s s (backoff max 300s)...",
                backoff,
            )
            await asyncio.sleep(backoff)
            backoff = min(int(backoff * 1.5), 300)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("Runner error: %s — restarting in 30s", e)
            try:
                health_path = BASE_DIR / "marketing_health.json"
                data = {}
                if health_path.exists():
                    with open(health_path) as f:
                        data = json.load(f)
                data["last_runner_fatal"] = str(e)
                data["last_runner_fatal_trace"] = traceback.format_exc()[:2000]
                with open(health_path, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass
            await asyncio.sleep(30)
            backoff = 15


if __name__ == "__main__":
    asyncio.run(main())
