#!/usr/bin/env python3
"""
Send one marketing batch immediately (same logic as unified runner).
Temporarily stops the unified LaunchAgent so the session file is not locked.
"""
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
PLIST = Path.home() / "Library/LaunchAgents/com.techyera.telegram.unified.plist"


def launchctl_load():
    subprocess.run(["launchctl", "load", str(PLIST)], check=False)


def launchctl_unload():
    subprocess.run(["launchctl", "unload", str(PLIST)], check=False)


async def run_one_batch():
    from telethon import TelegramClient

    from cron_send_messages import load_config, send_messages_with_client

    config = load_config()
    client = TelegramClient(
        str(BASE_DIR / "techyera_cli_session"),
        config["api_id"],
        config["api_hash"],
    )
    await client.start(phone=config["phone"])
    if not await client.is_user_authorized():
        print("Not authorized.", file=sys.stderr)
        return 1
    await send_messages_with_client(client, load_config())
    await client.disconnect()
    return 0


def main():
    if not PLIST.exists():
        print("Unified plist not found; running send without unload (may fail if runner is up).")
        return asyncio.run(run_one_batch())

    print("Stopping unified runner (briefly)...")
    launchctl_unload()
    time.sleep(4)
    try:
        code = asyncio.run(run_one_batch())
    finally:
        print("Starting unified runner again...")
        launchctl_load()
        time.sleep(2)
    print("Done. One batch sent; ~30 min cadence resumes with unified runner.")
    return code or 0


if __name__ == "__main__":
    sys.exit(main())
