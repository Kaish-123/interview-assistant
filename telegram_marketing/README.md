# 📱 Telegram Marketing Automation

Automated message sender for Telegram groups and channels. Send your marketing messages to multiple groups with configurable schedules.

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
cd telegram_marketing
pip install -r requirements.txt
```

### Step 2: Get Telegram API Credentials
1. Go to https://my.telegram.org
2. Log in with your phone number
3. Click "API development tools"
4. Create a new application
5. Copy your **api_id** and **api_hash**

### Step 3: Run Setup Wizard
```bash
python telegram_marketer.py --setup
```
Follow the prompts to enter your API credentials and create messages.

### Step 4: Login to Telegram
```bash
python telegram_marketer.py --login
```
Enter the verification code sent to your Telegram.

### Step 5: Find Your Groups
```bash
python telegram_marketer.py --list
```
This shows all your groups and channels. Copy the usernames to add to config.

### Step 6: Start Automation
```bash
python telegram_marketer.py --start
```

---

## 📋 All Commands

| Command | Description |
|---------|-------------|
| `--setup` | Interactive setup wizard |
| `--login` | Authenticate with Telegram |
| `--list` | List all your groups/channels |
| `--start` | Start automated scheduler |
| `--send-once` | Send to all targets once |
| `--send-to @group` | Send to specific target |
| `--status` | Show current configuration |
| `--add-target NAME @username` | Add new target |
| `--add-message ID "text"` | Add new message |

---

## ⚙️ Configuration (config.json)

### Targets
Add groups/channels to send messages to:
```json
"targets": [
    {
        "name": "My Marketing Group",
        "username": "@mygroup",
        "enabled": true
    },
    {
        "name": "Tech Channel",
        "username": "@techchannel",
        "enabled": true
    }
]
```

### Messages
Add your marketing messages:
```json
"messages": [
    {
        "id": "promo1",
        "text": "🚀 Check out our services!\n\nVisit: https://yoursite.com",
        "enabled": true
    }
]
```

### Schedule
Configure when and how often to send:
```json
"schedule": {
    "enabled": true,
    "interval_minutes": 60,
    "random_delay_minutes": 5,
    "active_hours": {
        "start": 9,
        "end": 21
    },
    "active_days": [0, 1, 2, 3, 4, 5, 6]
}
```

- **interval_minutes**: Time between message batches
- **random_delay_minutes**: Random variance to avoid detection
- **active_hours**: Only send during these hours (24h format)
- **active_days**: 0=Monday, 6=Sunday

### Settings
```json
"settings": {
    "rotate_messages": true,
    "delay_between_groups_seconds": 30,
    "max_messages_per_day": 50,
    "log_file": "telegram_marketing.log"
}
```

---

## 🔧 Helper Scripts

### Quick Send
Send a single message quickly:
```bash
python quick_send.py "@groupname" "Your message here"
```

### Bulk Add Targets
Add multiple groups at once:
```bash
python bulk_add_targets.py
```

---

## 📝 Example Workflow

1. **Morning Setup**
   ```bash
   python telegram_marketer.py --status  # Check config
   python telegram_marketer.py --start   # Start automation
   ```

2. **Add New Groups**
   ```bash
   python telegram_marketer.py --list    # Find groups
   python telegram_marketer.py --add-target "New Group" "@newgroup"
   ```

3. **Manual Send**
   ```bash
   python telegram_marketer.py --send-once
   ```

---

## ⚠️ Important Notes

1. **Rate Limits**: Telegram has rate limits. The tool includes:
   - Automatic delays between messages
   - Random timing variance
   - Daily message limits

2. **Permissions**: You must have permission to post in groups/channels

3. **Session File**: After login, a `.session` file is created. Keep it safe!

4. **Logs**: Check `telegram_marketing.log` for history and errors

---

## 🛡️ Best Practices

- Start with low frequency (1-2 hours between sends)
- Use different messages (rotation is enabled by default)
- Only target groups where you have permission
- Monitor the logs for any issues
- Don't spam! Respect community guidelines

---

## 🔑 Getting API Credentials (Detailed)

1. Open https://my.telegram.org in your browser
2. Enter your phone number (with country code)
3. Enter the verification code from Telegram
4. Click "API development tools"
5. Fill in the form:
   - App title: "Marketing Tool" (or anything)
   - Short name: "marketing" (or anything)
   - Platform: Desktop
   - Description: "Personal marketing automation"
6. Click "Create application"
7. Copy:
   - **api_id** (a number like 12345678)
   - **api_hash** (a long string of letters and numbers)

---

## 📞 Support

For issues or questions, check the logs first:
```bash
cat telegram_marketing.log
```

---

Made with ❤️ by TechyEra
