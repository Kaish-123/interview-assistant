#!/usr/bin/env python3
"""
Send the configured message to all contacts in built broadcast lists.
- Reads broadcast_lists/_index.json and each list JSON
- Message from message.txt (or per-list message_file in config)
- Uses PyWhatKit to open WhatsApp Web and send to each number (with delays)
Run build_broadcast_lists.py first.
"""

import argparse
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
BROADCAST_DIR = BASE_DIR / "broadcast_lists"
INDEX_FILE = BROADCAST_DIR / "_index.json"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_message_for_list(list_name: str, config: dict, list_data: dict) -> str:
    """Resolve message: list-specific file, or default message.txt."""
    for definition in config.get("broadcast_lists", []):
        def_name = definition.get("name", "")
        if def_name == list_name or list_name == def_name or list_name.startswith(def_name + "_"):
            msg_file = definition.get("message_file")
            if msg_file:
                path = BASE_DIR / msg_file
                if path.exists():
                    return path.read_text(encoding="utf-8").strip()
            break
    path = BASE_DIR / config.get("default_message_file", "message.txt")
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def send_via_whatsapp(phone: str, message: str, delay_seconds: int = 15, wait_after_open: int = 10) -> bool:
    """Send one message via PyWhatKit (opens WhatsApp Web). Phone with or without +."""
    try:
        import pywhatkit as kit
        number = phone.lstrip("+").replace(" ", "")
        kit.sendwhatmsg_instantly(number, message, wait_time=wait_after_open, tab_close=True)
        return True
    except Exception as e:
        print(f"  Error sending to {phone}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Send broadcast message to all built lists")
    parser.add_argument("--dry-run", action="store_true", help="Only print contacts and message, do not send")
    parser.add_argument("--list", type=str, help="Send only to this list name (e.g. 'Clients_1')")
    parser.add_argument("--message", type=str, help="Override message (or use message.txt / config)")
    args = parser.parse_args()

    if not INDEX_FILE.exists():
        print("Run build_broadcast_lists.py first. No _index.json found.")
        return 1

    config = load_config()
    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    default_message_file = index.get("default_message_file", "message.txt")
    default_message = (BASE_DIR / default_message_file).read_text(encoding="utf-8").strip() if (BASE_DIR / default_message_file).exists() else ""
    if args.message:
        message_to_send = args.message
    else:
        message_to_send = default_message

    if not message_to_send and not args.dry_run:
        print("No message set. Use message.txt, config message_file, or --message.")
        return 1

    send_settings = config.get("send_settings", {})
    delay = send_settings.get("delay_between_contacts_seconds", 15)
    wait_open = send_settings.get("wait_after_open_whatsapp_seconds", 10)

    lists_to_send = index.get("lists", [])
    if args.list:
        lists_to_send = [x for x in lists_to_send if x["name"] == args.list]
        if not lists_to_send:
            print(f"No list named '{args.list}'.")
            return 1

    total_contacts = 0
    for entry in lists_to_send:
        list_path = Path(entry["path"])
        if not list_path.exists():
            print(f"Skip (missing): {entry['name']}")
            continue
        list_data = json.loads(list_path.read_text(encoding="utf-8"))
        contacts = list_data.get("contacts", [])
        msg = args.message or get_message_for_list(list_data.get("name", ""), config, list_data) or message_to_send

        print(f"\n--- List: {entry['name']} ({len(contacts)} contacts) ---")
        if args.dry_run:
            for c in contacts:
                print(f"  Would send to: {c.get('phone')} ({c.get('name', '')})")
            print(f"  Message preview: {msg[:80]}...")
            total_contacts += len(contacts)
            continue

        for i, c in enumerate(contacts):
            phone = c.get("phone", "")
            name = c.get("name", "")
            if not phone:
                continue
            print(f"  [{i+1}/{len(contacts)}] Sending to {phone} ({name})...")
            ok = send_via_whatsapp(phone, msg, delay_seconds=delay, wait_after_open=wait_open)
            if ok:
                total_contacts += 1
            time.sleep(delay)

    print(f"\nDone. Sent to {total_contacts} contacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
