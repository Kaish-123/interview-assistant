# Broadcast Marketing – Quick Commands

## Load your contacts (one command – automated)

```bash
cd Broadcast_Marketing
./run.sh load-contacts
```

This exports from Mac Contacts, fills contacts.csv, and rebuilds lists. Grant **Contacts** access when asked. Then run setup and send (below).

## First-time setup (run once)

```bash
./run.sh setup
```

Then edit **message.txt** with your WhatsApp message.

---

## Daily use

```bash
cd Broadcast_Marketing

# Preview who will get the message (no send)
./run.sh send-dry-run

# Send to all broadcast lists (opens WhatsApp Web)
./run.sh send
```

---

## All commands

| Command | Description |
|--------|-------------|
| `./run.sh setup` | Install dependencies + build lists (run first) |
| `./run.sh sync` | Sync contacts from Mac **Contacts** app → contacts.csv |
| `./run.sh build` | Rebuild lists from contacts.csv + config.json |
| `./run.sh sync-build` | Sync from Mac, then build lists |
| `./run.sh send` | Send message to all lists (WhatsApp Web) |
| `./run.sh send-dry-run` | Preview recipients, no send |
| `./run.sh send-list Clients_1` | Send only to list "Clients_1" |
| `./run.sh install-schedule` | Schedule sync+build every 6 hours |
| `./run.sh install-send-schedule` | **Send WhatsApp messages every 30 min** (automated) |
| `./run.sh help` | Show help |

---

## Automated send every 30 minutes

To stop manual runs and have messages go out automatically every 30 minutes:

```bash
./run.sh install-send-schedule
```

- Runs in the background (LaunchAgent). **Mac must be on and you logged in** so the browser can open for WhatsApp Web.
- Why 30 min? See **WHY_30MIN.md** – keeps your account safe from WhatsApp rate limits while staying frequent.
- Logs: `send_launchd.log`, `send_launchd_error.log`
- To stop: `launchctl unload ~/Library/LaunchAgents/com.broadcast.marketing.send.plist`

---

## What to edit

- **message.txt** – Text sent to everyone
- **config.json** – `broadcast_lists`: name + keywords for each list
- **contacts.csv** – Or use Mac Contacts Notes as keywords and run `./run.sh sync`

---

## Optional: sync from Mac Contacts

1. In **Contacts** app, add keywords in each contact’s **Notes** (e.g. `client, vip`).
2. Run: `./run.sh sync` (grant Contacts access when prompted).
3. Run: `./run.sh build` or `./run.sh sync-build`.

To add new contacts automatically every 6 hours: `./run.sh install-schedule`.
