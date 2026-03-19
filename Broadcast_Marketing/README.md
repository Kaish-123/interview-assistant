# Broadcast Marketing – Mac Contacts + WhatsApp Broadcast Lists

This system **syncs contacts from your Mac Contacts app**, builds **keyword-based broadcast lists**, and sends a **single configurable message** via **WhatsApp**. It can run **on a schedule** so new contacts are added to lists automatically.

## How it works

1. **Mac Contacts** – Sync from the **Contacts** app: name, phone(s), and **Notes** (used as keywords). New contacts you add in Contacts are picked up on the next sync.
2. **Keywords** – Put comma-separated keywords in each contact’s **Notes** field (e.g. `client, vip`). Matching also uses the contact **name**.
3. **Broadcast lists** – In `config.json` you define lists by **keyword sets**. A contact is in a list if their name or notes contain **any** of that list’s keywords.
4. **Auto-chunking** – If a list exceeds 256 contacts (WhatsApp limit), extra lists are created (e.g. `Clients_1`, `Clients_2`).
5. **Message** – Set the message in `message.txt`; it is sent to every contact in every built list via WhatsApp Web.
6. **Scheduled sync** – Optional LaunchAgent runs sync + build every 6 hours so new contacts are added to lists automatically.

## Quick start (Mac) – use your own contacts

**There are no sample contacts.** Load your contacts first:

```bash
cd Broadcast_Marketing

# 1a. From Mac Contacts app (grant Contacts access when prompted)
./run.sh sync

# 1b. OR if sync fails: Contacts → File → Export → Export vCard… then:
./run.sh import-vcard ~/Desktop/contacts.vcf

# 2. Build lists and install sender
./run.sh build
./run.sh setup

# 3. Edit message.txt, then preview and send
./run.sh send-dry-run
./run.sh send
```

## Setup

### 1. Contacts – Mac Contacts app + `contacts.csv`

- **Sync from Mac:** Run `./run.sh sync` to pull all contacts (name, phone, Notes) into `contacts.csv`. Grant **Contacts** access when macOS prompts (System Settings → Privacy & Security → Contacts).
- **Keywords:** In the **Contacts** app, use the **Notes** field for each contact. Put comma- or semicolon-separated keywords (e.g. `client, vip` or `lead;interested`). Matching uses both **name** and **Notes**.
- **Re-sync:** Run `./run.sh sync` again after adding contacts or changing notes. Use `./run.sh install-schedule` to run sync + build every 6 hours so **new contacts are added to lists automatically**.

| contacts.csv column | Source |
|---------------------|--------|
| `name` | Contact name |
| `phone` | Phone number (with country code) |
| `keywords` | From Contact’s **Notes** (comma-separated) |

- **Replace vs merge:** `./run.sh sync` merges Mac contacts with any extra rows already in `contacts.csv`. To **replace** entirely with Mac data, run: `python3 sync_contacts_from_mac.py --replace`.
- **If sync fails (permission):** Grant **Contacts** to Terminal/Cursor in System Settings → Privacy & Security → Contacts. Or use **vCard export**: Contacts → File → Export → Export vCard…, then `./run.sh import-vcard path/to/file.vcf`.

### 2. Broadcast list definitions – `config.json`

- **`max_contacts_per_list`** – Max contacts per list (e.g. 256). If more contacts match, extra lists are created: `ListName_1`, `ListName_2`, …
- **`default_message_file`** – Default file for the message (e.g. `message.txt`).
- **`broadcast_lists`** – Array of list definitions:
  - **`name`** – List name (e.g. `Clients`, `Leads`).
  - **`keywords`** – List of keywords. Contacts matching **any** keyword go into this list.
  - **`message_file`** – Optional. If set, this file is used for this list instead of the default.

Example:

```json
{
  "max_contacts_per_list": 256,
  "default_message_file": "message.txt",
  "broadcast_lists": [
    { "name": "Clients", "keywords": ["client", "vip", "customer"] },
    { "name": "Leads", "keywords": ["lead", "interested", "prospect"] }
  ]
}
```

### 3. Message – `message.txt`

Put the exact text you want to send to all broadcast lists. You can change this file anytime and run `./run.sh send` again.

To use a **different message for one list**, set `message_file` in that list’s definition in `config.json` and create that file (e.g. `message_clients.txt`).

## Commands

| Command | Description |
|--------|-------------|
| `./run.sh sync` | Sync contacts from Mac **Contacts** app into `contacts.csv` (Notes → keywords). |
| `./run.sh build` | Build broadcast lists from `contacts.csv` and `config.json`. Writes `broadcast_lists/*.json`. |
| `./run.sh sync-build` | Sync from Mac Contacts, then build lists (recommended after adding contacts). |
| `./run.sh send` | Send the message to all contacts in all built lists (WhatsApp Web via PyWhatKit). |
| `./run.sh send-dry-run` | Show which contacts would receive the message; no messages sent. |
| `./run.sh send-list NAME` | Send only to the list named `NAME` (e.g. `Clients_1`). |
| `./run.sh install-schedule` | Install LaunchAgent: sync + build every **6 hours** so new contacts are added to lists automatically. |

## Sending (WhatsApp)

- **Requirement:** `pip install -r requirements.txt` (installs `pywhatkit`).
- Sending uses **WhatsApp Web**: a browser tab opens and the script sends to each number with a delay between contacts (see `config.json` → `send_settings.delay_between_contacts_seconds`).
- Keep the machine unlocked and don’t close the browser until the run finishes.

## File layout

```
Broadcast_Marketing/
├── contacts.csv              # Synced from Mac Contacts (name, phone, keywords from Notes)
├── config.json               # List definitions (keywords) + send settings
├── message.txt               # Default message for all lists
├── sync_contacts_from_mac.py # Sync from Contacts app via AppleScript
├── sync_and_build.sh         # Used by LaunchAgent: sync + build
├── install_schedule.sh       # Install 6-hour scheduled sync
├── com.broadcast.marketing.sync.plist  # LaunchAgent plist
├── build_broadcast_lists.py
├── send_broadcasts.py
├── run.sh
├── requirements.txt
├── README.md
├── sync_and_build.log        # Log from scheduled runs
└── broadcast_lists/          # Created by build (do not edit by hand)
    ├── _index.json
    ├── Clients_1.json
    └── ...
```

## Summary

- **Mac Contacts** – Sync name, phone, and Notes (keywords) from the Contacts app; new contacts are included when you run sync (or on schedule).
- **Keyword-based lists** – Define lists in `config.json` by keywords; contacts are selected by name or Notes.
- **Auto-chunking** – Lists over 256 contacts are split (e.g. `Clients_1`, `Clients_2`).
- **One message** – Set it in `message.txt`; send to all built lists via WhatsApp.
- **Regular updates** – Use `./run.sh install-schedule` to sync and rebuild lists every 6 hours so new contacts are added automatically.
