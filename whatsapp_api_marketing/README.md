# 📱 WhatsApp Business API Marketing

Automated marketing message sender for WhatsApp using the official **WhatsApp Business Cloud API**.

## Features

- ✅ **API-based messaging** - No GUI automation, works headlessly
- ✅ **Broadcast lists** - Send to multiple recipients efficiently
- ✅ **Message templates** - Use Meta-approved templates
- ✅ **Text & Image messages** - Rich content support
- ✅ **Scheduled automation** - Configurable frequency
- ✅ **Rate limiting** - Stay within API limits
- ✅ **Message rotation** - Rotate between multiple messages
- ✅ **Personalization** - Use {{name}} placeholders
- ✅ **Active hours** - Only send during specified times
- ✅ **LaunchAgent support** - Background automation on macOS

## Prerequisites

1. **WhatsApp Business Account** - Register at [Facebook Business](https://business.facebook.com/)
2. **Meta Developer App** - Create at [developers.facebook.com](https://developers.facebook.com/)
3. **WhatsApp Business API** access - Add WhatsApp product to your app

## Quick Start

### 1. Set Up Virtual Environment

```bash
cd whatsapp_api_marketing
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Get API Credentials

1. Go to [Meta Developers](https://developers.facebook.com/apps/)
2. Create a Business App or select existing one
3. Add **WhatsApp** product
4. Go to WhatsApp > API Setup
5. Copy your:
   - **Phone Number ID**
   - **Access Token** (generate a permanent one)
   - **WABA ID** (WhatsApp Business Account ID)

### 3. Run Setup Wizard

```bash
python whatsapp_api_marketer.py --setup
```

This will guide you through:
- Entering API credentials
- Setting schedule preferences
- Adding marketing messages

### 4. Edit Configuration

Edit `config.json` to add your targets and broadcasts:

```json
{
    "targets": [
        {
            "name": "John Doe",
            "phone": "919876543210",
            "enabled": true
        }
    ],
    "broadcasts": [
        {
            "name": "Marketing List",
            "enabled": true,
            "recipients": [
                {"phone": "919876543210", "name": "Contact 1"},
                {"phone": "919876543211", "name": "Contact 2"}
            ]
        }
    ]
}
```

### 5. Verify & Test

```bash
# Verify API credentials
python whatsapp_api_marketer.py --verify

# Send test message to specific number
python whatsapp_api_marketer.py --send-to 919876543210 --message "Test message"

# Send to all targets once
python whatsapp_api_marketer.py --send-once
```

### 6. Start Automation

```bash
# Run continuous scheduler
python whatsapp_api_marketer.py --start

# Or install as background service (macOS)
chmod +x install_launchd.sh
./install_launchd.sh
```

## Usage

```bash
# Setup & Configuration
python whatsapp_api_marketer.py --setup        # Run setup wizard
python whatsapp_api_marketer.py --status       # Show config status

# API Operations
python whatsapp_api_marketer.py --verify       # Verify API credentials
python whatsapp_api_marketer.py --templates    # List message templates

# Sending Messages
python whatsapp_api_marketer.py --send-once    # Send to all targets once
python whatsapp_api_marketer.py --start        # Start automated scheduler
python whatsapp_api_marketer.py --send-to PHONE --message "Text"

# Add Targets
python whatsapp_api_marketer.py --add-target "John" "919876543210"
python whatsapp_api_marketer.py --add-broadcast "VIP List" "91..." "91..."
python whatsapp_api_marketer.py --add-message "msg1" "Your message text"
```

## Configuration Reference

### config.json Structure

```json
{
    "phone_number_id": "YOUR_PHONE_NUMBER_ID",
    "access_token": "YOUR_ACCESS_TOKEN",
    "waba_id": "YOUR_WABA_ID",
    
    "targets": [...],      // Individual contacts
    "broadcasts": [...],   // Broadcast lists
    "messages": [...],     // Message templates/texts
    
    "schedule": {
        "enabled": true,
        "interval_minutes": 60,         // Send every X minutes
        "random_delay_minutes": 10,     // Add randomness
        "active_hours": {"start": 9, "end": 21},  // 9am-9pm
        "active_days": [0,1,2,3,4,5,6]  // 0=Monday, 6=Sunday
    },
    
    "settings": {
        "rotate_messages": true,        // Cycle through messages
        "personalize": true,            // Replace {{name}}
        "max_messages_per_day": 1000,   // Daily limit
        "delay_between_messages_seconds": 3
    }
}
```

### Message Types

**Text Message:**
```json
{
    "id": "promo1",
    "type": "text",
    "text": "Hello {{name}}, check out our services!",
    "enabled": true
}
```

**Template Message (for non-opted-in users):**
```json
{
    "id": "template1",
    "type": "template",
    "template_name": "hello_world",
    "language": "en",
    "enabled": true
}
```

**Image Message:**
```json
{
    "id": "image1",
    "type": "image",
    "image_url": "https://example.com/image.jpg",
    "text": "Check this out!",
    "enabled": true
}
```

## Background Automation

### Install LaunchAgent (macOS)

```bash
chmod +x install_launchd.sh
./install_launchd.sh
```

### Check Service Status

```bash
launchctl list | grep whatsapp
tail -f logs/cron_messages.log
```

### Uninstall

```bash
./uninstall_launchd.sh
```

## Logs

Logs are stored in `logs/` directory:
- `whatsapp_marketing.log` - Main application log
- `cron_messages.log` - Cron job execution log
- `launchd_output.log` - LaunchAgent stdout
- `launchd_error.log` - LaunchAgent stderr

## API Rate Limits

WhatsApp Business API has rate limits:
- **Tier 1**: 1,000 conversations/day (new accounts)
- **Tier 2**: 10,000 conversations/day
- **Tier 3**: 100,000 conversations/day
- **Tier 4**: Unlimited

The tool respects `max_messages_per_day` setting to stay within limits.

## Important Notes

⚠️ **24-Hour Window**: You can only send free-form messages to users who have messaged you in the last 24 hours. For others, use **template messages**.

⚠️ **Template Approval**: Marketing templates need Meta approval before use.

⚠️ **Business Verification**: Complete business verification for higher limits.

## Troubleshooting

**"Invalid OAuth access token"**
- Generate a new access token from Meta Developer Console
- For production, use a System User permanent token

**"Parameter recipient is not a valid whatsapp number"**
- Ensure phone numbers include country code (e.g., 919876543210)
- Remove + and spaces from numbers

**"Message failed to send because more than 24 hours have passed"**
- Use template messages for users outside 24-hour window

## Files

```
whatsapp_api_marketing/
├── whatsapp_api_marketer.py    # Main marketing tool
├── cron_send_messages.py       # Cron job script
├── config.json                 # Configuration file
├── requirements.txt            # Python dependencies
├── install_launchd.sh          # Install background service
├── uninstall_launchd.sh        # Uninstall service
├── run.sh                      # Quick run script
├── com.techyera.whatsapp.api.plist  # LaunchAgent config
├── logs/                       # Log files
└── README.md                   # This file
```

## Author

TechyEra Marketing Suite

---

📧 For support, contact the TechyEra team.
