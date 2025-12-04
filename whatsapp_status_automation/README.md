# WhatsApp Status Automation for macOS 📱

Automatically set your WhatsApp status on weekends (or any day you configure)!

## Features ✨

- 🤖 **Automated Status Updates**: Set your WhatsApp status without manual intervention
- 📅 **Scheduled Execution**: Runs automatically on configured days/times
- 🎲 **Multiple Captions**: Configure multiple status messages, use sequentially or randomly
- 🖥️ **GUI & CLI**: Both graphical and command-line interfaces
- ⏰ **macOS launchd Integration**: Native scheduling with launchd

## Quick Start 🚀

### 1. Setup (Already Done!)

The virtual environment is already created with all dependencies. Just use the helper scripts!

### 2. Grant Accessibility Permissions (REQUIRED!)

**This is essential for GUI automation to work!**

1. Open **System Preferences** → **Security & Privacy** → **Privacy** → **Accessibility**
2. Click the lock to make changes
3. Add **Terminal** (or your terminal app)
4. Check the boxes to enable

### 3. Configure Your Status Messages

Edit `config.json`:

```json
{
    "status_captions": [
        "Weekend vibes ✨",
        "Taking a break 🌴",
        "Your custom message here!"
    ],
    "schedule": {
        "days": ["saturday", "sunday"],
        "time": "09:00"
    }
}
```

### 4. Run the Automation

#### Easy Way (Recommended) - Use Shell Scripts:

```bash
# Run status update now
./run.sh --run

# Run with custom caption
./run.sh --run --caption "Hello World! 🌍"

# Test mode
./run.sh --test

# Open GUI
./run_gui.sh
```

#### Manual Way (with venv activation):

```bash
# Activate the virtual environment first
source venv/bin/activate

# Then run commands
python whatsapp_status.py --run
python whatsapp_status.py --test
python gui.py
```

### 5. Set Up Automatic Weekend Scheduling

```bash
# Activate venv first
source venv/bin/activate

# Set up launchd to run on weekends at 9:00 AM
python scheduler.py --setup --time 09:00

# Check status
python scheduler.py --status

# Remove scheduler
python scheduler.py --unload
```

## Usage Guide 📖

### GUI Mode

```bash
./run_gui.sh
```

1. **Add Captions**: Click "➕ Add Caption" to add status messages
2. **Configure Schedule**: Select days and time
3. **Test**: Click "🧪 Test Mode" to preview without executing
4. **Run**: Click "▶️ Run Now" to update status immediately
5. **Schedule**: Click "📅 Setup Scheduler" for automatic execution

### Command Line Options

```
./run.sh --help

Options:
  --run, -r       Run the status update immediately
  --caption, -c   Custom caption to use (overrides config)
  --schedule, -s  Run in scheduled mode (checks day/time)
  --daemon, -d    Run as daemon (keeps running and checks schedule)
  --test, -t      Test mode - just print what would happen
```

### Examples

```bash
# Update status now with default caption
./run.sh --run

# Update with specific caption
./run.sh --run --caption "Out for the weekend! 🏖️"

# Check if it would run (test mode)
./run.sh --test

# Run as background daemon
./run.sh --daemon
```

## Configuration ⚙️

### config.json Options

| Option | Description | Default |
|--------|-------------|---------|
| `status_captions` | List of status messages | `["Weekend vibes ✨"]` |
| `schedule.days` | Days to run (lowercase) | `["saturday", "sunday"]` |
| `schedule.time` | Time to run (24-hour) | `"09:00"` |
| `use_random_caption` | Random instead of sequential | `false` |
| `delay_between_actions` | Seconds between GUI clicks | `1.0` |
| `whatsapp_app_name` | Name of WhatsApp app | `"WhatsApp"` |

### Example Configurations

**Weekends only, morning:**
```json
{
    "schedule": {
        "days": ["saturday", "sunday"],
        "time": "09:00"
    }
}
```

**Every day at noon:**
```json
{
    "schedule": {
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "time": "12:00"
    }
}
```

**Friday evenings:**
```json
{
    "schedule": {
        "days": ["friday"],
        "time": "18:00"
    }
}
```

## Image-Based Navigation (Optional) 🖼️

For more reliable clicking, add reference screenshots to the `images/` folder:
- `status_tab.png` - The Status tab in WhatsApp
- `my_status.png` - "My status" button
- `add_status.png` - Add status button

## Troubleshooting 🔧

### "Permission denied" or automation doesn't work
- **Grant Accessibility permissions!**
- System Preferences → Security & Privacy → Privacy → Accessibility
- Add Terminal (or iTerm, etc.)

### WhatsApp doesn't open
- Check `whatsapp_app_name` in config matches your app
- Try `"WhatsApp"` or `"WhatsApp Desktop"`

### Status doesn't update correctly
- Increase `delay_between_actions` in config (try 2.0)
- Make sure WhatsApp window is visible (not minimized)
- The automation clicks on specific screen positions

### Scheduler not running
- Run `source venv/bin/activate && python scheduler.py --status`
- Check logs: `~/Library/Logs/whatsapp_status.log`
- Ensure Mac doesn't sleep at scheduled time

## Files 📁

```
whatsapp_status_automation/
├── whatsapp_status.py    # Main automation script
├── scheduler.py          # launchd setup script
├── gui.py                # GUI interface
├── config.json           # Your settings
├── run.sh                # Quick run script (CLI)
├── run_gui.sh            # Quick run script (GUI)
├── venv/                 # Virtual environment (dependencies)
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── images/               # Optional reference images
```

## Re-installing Dependencies

If you need to reinstall:

```bash
cd /Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac/whatsapp_status_automation
python3 -m venv venv
source venv/bin/activate
pip install pyautogui pillow schedule pyobjc-framework-Quartz
```

## License 📄

MIT License - Feel free to modify and share!
