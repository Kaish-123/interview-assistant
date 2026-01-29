# TechyEra Telegram Marketing - CLI Commands

## Quick Commands (using techyera.sh)

```bash
cd ~/Downloads/chatgpt_gui_mac/Telegram_with_CLI

# Show help
./techyera.sh help

# Check status and stats
./techyera.sh status

# Send messages now (manual trigger)
./techyera.sh send

# Run group growth now (manual trigger)
./techyera.sh grow

# List all target groups
./techyera.sh groups

# Show recent logs
./techyera.sh logs

# Show recent errors
./techyera.sh errors

# Show next scheduled runs
./techyera.sh next

# Start automation
./techyera.sh start

# Stop automation
./techyera.sh stop
```

## Direct Python Commands

```bash
cd ~/Downloads/chatgpt_gui_mac/Telegram_with_CLI

# Monitor stats
python3 monitor.py --stats

# Monitor logs
python3 monitor.py --logs --lines 50

# Monitor only send logs
python3 monitor.py --logs --type send

# Monitor only growth logs
python3 monitor.py --logs --type growth

# Show groups
python3 monitor.py --groups

# Show errors
python3 monitor.py --errors

# Show next run times
python3 next_run.py

# Send messages manually
python3 cron_send_messages.py

# Run growth manually
python3 cron_growth.py
```

## LaunchAgent Commands

```bash
# Check if automation is running
launchctl list | grep techyera

# Install/reinstall LaunchAgents
cd ~/Downloads/chatgpt_gui_mac/Telegram_with_CLI
./install_launchd.sh

# Stop message sending
launchctl unload ~/Library/LaunchAgents/com.techyera.telegram.send.plist

# Start message sending
launchctl load ~/Library/LaunchAgents/com.techyera.telegram.send.plist

# Stop growth
launchctl unload ~/Library/LaunchAgents/com.techyera.telegram.growth.plist

# Start growth
launchctl load ~/Library/LaunchAgents/com.techyera.telegram.growth.plist
```

## Log Files

- **Send logs:** `launchd_send.log`, `send_messages.log`
- **Growth logs:** `launchd_growth.log`, `growth.log`
- **Error logs:** `launchd_send_error.log`, `launchd_growth_error.log`

```bash
# View send log
tail -f ~/Downloads/chatgpt_gui_mac/Telegram_with_CLI/send_messages.log

# View growth log
tail -f ~/Downloads/chatgpt_gui_mac/Telegram_with_CLI/growth.log

# View launchd logs
tail -f ~/Downloads/chatgpt_gui_mac/Telegram_with_CLI/launchd_send.log
```

## Configuration

Edit `config.json` to modify:
- Target groups
- Marketing message
- Send frequency
- Active hours
- Growth keywords
- Delays and limits

## Schedule

- **Message Sending:** Every 1 hour
- **Group Growth:** Every 6 hours
- **Active Hours:** 24/7 (configurable)
