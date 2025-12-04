# 📱 WhatsApp Marketing Automation

Automated WhatsApp marketing system that sends personalized messages with images to your contacts filtered by suffix keywords (client, proxy, interview).

## ✨ Features

- **🔄 Auto-sync contacts** from macOS Contacts app (synced via iCloud)
- **🏷️ Filter by suffix** - Only message contacts with specific keywords (client, proxy, interview)
- **📷 Bulk image sending** - Send up to 30 images per message
- **⏰ Scheduled campaigns** - Runs automatically every Saturday at 2am IST
- **👥 Contact management** - Exclude/include specific contacts via GUI
- **🛡️ Anti-spam protection** - Random delays between messages
- **📊 Progress tracking** - Track who received messages and when
- **🖥️ Beautiful GUI** - Easy-to-use graphical interface

## 🚀 Quick Start

### 1. Setup

```bash
cd whatsapp_marketing
chmod +x setup.sh run.sh run_gui.sh
./setup.sh
```

### 2. Grant Permissions (REQUIRED!)

**Contacts Access:**
- System Preferences → Security & Privacy → Privacy → Contacts
- Add Terminal (or your terminal app)

**Accessibility Access:**
- System Preferences → Security & Privacy → Privacy → Accessibility  
- Add Terminal (or your terminal app)

### 3. Add Your Images

Put your 25-30 marketing images in:
```
whatsapp_marketing/marketing_images/
```

### 4. Run the GUI

```bash
./run_gui.sh
```

## 📖 Usage

### GUI Mode (Recommended)

```bash
./run_gui.sh
```

**Dashboard Tab:**
- View statistics (total contacts, active, excluded, images)
- Quick actions (refresh, run campaign, test)

**Contacts Tab:**
- View all contacts with their status
- Filter by type (client/proxy/interview)
- Search contacts
- Double-click to exclude/include
- Bulk exclude/include selected

**Message Tab:**
- Edit your message template
- Configure delays and batch sizes
- Preview how the message looks

**Images Tab:**
- View all marketing images
- Add new images
- Open images folder

**Schedule Tab:**
- Set up Saturday 2am IST schedule
- View schedule status
- Remove schedule

**Logs Tab:**
- View campaign logs
- Clear old logs

### CLI Mode

```bash
# Refresh contacts from macOS
./run.sh --refresh

# Show statistics
./run.sh --stats

# List available images
./run.sh --images

# Test run (no actual sending)
./run.sh --run --dry-run

# Run campaign for all contacts
./run.sh --run

# Run only for 'client' contacts
./run.sh --run --suffix client

# Limit to 10 contacts
./run.sh --run --limit 10

# Test with single phone number
./run.sh --test +919876543210

# Setup click positions (calibration)
./run.sh --setup
```

### Scheduler Commands

```bash
# Set up Saturday 2am schedule
python marketing_scheduler.py --setup

# Custom day/time
python marketing_scheduler.py --setup --day sunday --time 03:00

# Check status
python marketing_scheduler.py --status

# Remove schedule
python marketing_scheduler.py --unload

# Run now (for testing)
python marketing_scheduler.py --run
```

## ⚙️ Configuration

Edit `marketing_config.json`:

```json
{
    "message_template": "Your message here...",
    "contact_suffixes": ["client", "proxy", "interview"],
    "delay_min_seconds": 45,
    "delay_max_seconds": 120,
    "batch_size": 50,
    "pause_between_batches_minutes": 30,
    "schedule": {
        "day": "saturday",
        "time": "02:00"
    }
}
```

### Settings Explained

| Setting | Description | Default |
|---------|-------------|---------|
| `message_template` | The message to send | Your referral message |
| `contact_suffixes` | Keywords to filter contacts | ["client", "proxy", "interview"] |
| `delay_min_seconds` | Minimum delay between messages | 45 |
| `delay_max_seconds` | Maximum delay between messages | 120 |
| `batch_size` | Messages per batch | 50 |
| `pause_between_batches_minutes` | Break between batches | 30 |

## ⚠️ Important Notes

### WhatsApp Ban Prevention

1. **Random delays** - The system waits 45-120 seconds between messages
2. **Batch processing** - Pauses for 30 minutes every 50 messages
3. **Don't send identical messages** - Slight variations help
4. **Don't exceed 200-300 messages/day** - WhatsApp may flag your account

### Contact Sync

Your iPhone contacts must be synced to Mac via iCloud:
1. On iPhone: Settings → [Your Name] → iCloud → Contacts → ON
2. On Mac: System Preferences → Apple ID → iCloud → Contacts → ON
3. Open Contacts app on Mac to verify sync

### Screen Unlock

For scheduled runs at 2am, the system will attempt to unlock your Mac automatically.
Update the password in `run_marketing.sh` if needed.

## 📁 Files

```
whatsapp_marketing/
├── marketing_gui.py          # GUI interface
├── whatsapp_marketing.py     # Main messaging script
├── contact_fetcher.py        # macOS Contacts integration
├── marketing_scheduler.py    # launchd scheduling
├── marketing_config.json     # Configuration
├── contacts_cache.db         # SQLite contact database
├── requirements.txt          # Python dependencies
├── setup.sh                  # Setup script
├── run.sh                    # CLI runner
├── run_gui.sh               # GUI runner
├── run_marketing.sh         # Scheduled runner (auto-created)
├── marketing_images/        # Put your images here
└── logs/                    # Campaign logs
```

## 🔧 Troubleshooting

### "Contacts access denied"
- Grant access in System Preferences → Privacy → Contacts

### "No contacts found"
- Check if contacts are synced from iPhone (open Contacts app)
- Make sure contact names include suffixes (client, proxy, interview)

### "Automation not working"
- Grant Accessibility access
- Ensure WhatsApp Desktop is logged in
- Run `./run.sh --setup` to calibrate click positions

### "Scheduled run not triggering"
- Check `python marketing_scheduler.py --status`
- Mac must be on (can be sleeping)
- Check logs: `~/Library/Logs/whatsapp_marketing.log`

## 📄 License

MIT License - Feel free to modify and use!

---

Made with ❤️ for efficient business marketing

