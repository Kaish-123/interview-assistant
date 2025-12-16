# 📋 TechyEra Telegram Marketing - Command Cheat Sheet
## All commands you need to monitor and manage your bot

---

## 📍 LOCATION
All files are stored at:
```
/Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac/telegram_marketing/
```

Quick access:
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing
```

---

## 🔍 CHECK IF BOT IS RUNNING

### Quick Status Check
```bash
launchctl list | grep techyera
```
**If you see 2 lines = Bot is running!**

### Detailed Status
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && python3 monitor.py
```

### Quick Stats Only
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && python3 monitor.py --stats
```

---

## ⏰ NEXT SCHEDULED RUN

### See When Bot Will Run Next
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && ./techyera.sh next
```
Or:
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && ./venv/bin/python3 next_run.py
```

This shows:
- ⏰ Next message time & countdown
- 🌱 Next growth cycle time
- 🎯 All groups that will receive messages
- 📊 Last run time

---

## 📊 MONITORING DASHBOARDS

### Terminal Dashboard (Full)
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && python3 monitor.py
```

### Live Auto-Refresh Dashboard (updates every 30 sec)
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && python3 monitor.py --live
```

### Web Dashboard (open in browser)
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && python3 web_dashboard.py
```
Then open: http://localhost:8080

### Today's Activity Only
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && python3 monitor.py --today
```

---

## 📜 VIEW LOGS

### See Last 20 Messages Sent
```bash
tail -20 ~/Downloads/chatgpt_gui_mac/telegram_marketing/cron_messages.log
```

### Watch Messages in Real-Time (Live)
```bash
tail -f ~/Downloads/chatgpt_gui_mac/telegram_marketing/cron_messages.log
```
Press Ctrl+C to stop

### See Growth Activity (Groups Joined)
```bash
tail -20 ~/Downloads/chatgpt_gui_mac/telegram_marketing/cron_growth.log
```

### Watch Growth in Real-Time
```bash
tail -f ~/Downloads/chatgpt_gui_mac/telegram_marketing/cron_growth.log
```

### See All Logs Combined
```bash
tail -f ~/Downloads/chatgpt_gui_mac/telegram_marketing/*.log
```

---

## ▶️ START / STOP / RESTART

### Start Automation
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && bash install_launchd.sh
```

### Stop Automation
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && bash uninstall_launchd.sh
```

### Restart Automation
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && bash uninstall_launchd.sh && bash install_launchd.sh
```

---

## ⚙️ CONFIGURATION

### View Current Config
```bash
cat ~/Downloads/chatgpt_gui_mac/telegram_marketing/config.json
```

### Edit Config (add groups, change message)
```bash
open ~/Downloads/chatgpt_gui_mac/telegram_marketing/config.json
```
Or use any text editor

### See All Target Groups with Added Date ⭐
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && ./techyera.sh groups
```
This shows:
- Total groups count
- Each group name & username
- ✅ Enabled / ❌ Disabled status
- 📅 Date when group was added
- Summary by date

### See Groups + Next Run Time
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && ./techyera.sh next
```

### Alternative Command (Python)
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && python3 -c "import json; c=json.load(open('config.json')); print(f'Total Groups: {len(c[\"targets\"])}'); [print(f\"  {t['name'][:40]} - {t['username']}\") for t in c['targets']]"
```

---

## 🚀 MANUAL ACTIONS

### Send Messages Now (don't wait for schedule)
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && source venv/bin/activate && python3 cron_send_messages.py
```

### Find & Join Groups Now
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && source venv/bin/activate && python3 cron_growth.py
```

### Send to Specific Group
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && source venv/bin/activate && python quick_send.py "@groupname" "Your message"
```

---

## 📁 FILE LOCATIONS

| File | Purpose |
|------|---------|
| `config.json` | Your settings (groups, message, schedule) |
| `cron_messages.log` | Log of all messages sent |
| `cron_growth.log` | Log of groups found/joined |
| `monitor.py` | Terminal dashboard |
| `web_dashboard.py` | Web dashboard |
| `cron_send_messages.py` | Message sender script |
| `cron_growth.py` | Growth/join script |
| `install_launchd.sh` | Start automation |
| `uninstall_launchd.sh` | Stop automation |
| `COMMANDS.md` | This file! |

---

## ⏰ SCHEDULE

| Task | When | What it does |
|------|------|--------------|
| Send Messages | Every hour (:00) | Sends your message to all groups |
| Growth | Every 6 hours | Finds new groups and joins them |

---

## 🆘 TROUBLESHOOTING

### Bot not running?
```bash
# Check status
launchctl list | grep techyera

# If empty, restart:
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && bash install_launchd.sh
```

### See errors?
```bash
tail -50 ~/Downloads/chatgpt_gui_mac/telegram_marketing/cron_messages.log | grep -i error
```

### Check if Python is working
```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing && source venv/bin/activate && python3 --version
```

### Clear logs (start fresh)
```bash
> ~/Downloads/chatgpt_gui_mac/telegram_marketing/cron_messages.log
> ~/Downloads/chatgpt_gui_mac/telegram_marketing/cron_growth.log
```

---

## 📱 QUICK REFERENCE

```
┌─────────────────────────────────────────────────────────┐
│                    MOST USED COMMANDS                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  CHECK STATUS:                                          │
│    launchctl list | grep techyera                       │
│                                                         │
│  VIEW DASHBOARD:                                        │
│    cd ~/Downloads/chatgpt_gui_mac/telegram_marketing    │
│    python3 monitor.py                                    │
│                                                         │
│  WATCH LIVE:                                            │
│    tail -f ~/Downloads/chatgpt_gui_mac/telegram_marketing/cron_messages.log │
│                                                         │
│  STOP BOT:                                              │
│    bash ~/Downloads/chatgpt_gui_mac/telegram_marketing/uninstall_launchd.sh │
│                                                         │
│  START BOT:                                             │
│    bash ~/Downloads/chatgpt_gui_mac/telegram_marketing/install_launchd.sh │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 TIPS

1. **Bot runs automatically** - You don't need to do anything!
2. **Survives restarts** - Bot starts when you login
3. **Check once daily** - Just run `python3 monitor.py` to see stats
4. **Logs are your friend** - Check logs if something seems wrong

---

Created: December 11, 2025
Location: ~/Downloads/chatgpt_gui_mac/telegram_marketing/COMMANDS.md

