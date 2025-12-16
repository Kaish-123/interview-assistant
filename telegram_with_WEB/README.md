# 🚀 TechyEra Telegram Marketing - Web Dashboard

A professional web-based Telegram marketing automation tool with a beautiful, modern dashboard.

![Dashboard](https://img.shields.io/badge/Dashboard-Modern%20UI-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)

## ✨ Features

- 📊 **Real-time Dashboard** - Beautiful, responsive UI with live statistics
- 🎯 **Group Management** - Add, remove, enable/disable target groups easily
- 💬 **Message Management** - Create and manage marketing messages
- ⏰ **Auto-Send** - Automatic message sending with configurable intervals
- 🔧 **Dynamic Configuration** - Change any setting via the web interface
- 📈 **Activity Tracking** - Real-time activity log and statistics
- 🔐 **Secure Login** - Easy Telegram authentication with code verification
- 🌐 **Network Access** - Access from any device on your network

## 🚀 Quick Start

### 1. Start the Dashboard

```bash
cd ~/Downloads/chatgpt_gui_mac/telegram_with_WEB

# Interactive mode (shows logs in terminal)
./start.sh

# OR run in background
./start_background.sh
```

### 2. Open in Browser

```
http://localhost:8888
```

### 3. Configure Telegram API

1. Go to the **Configuration** tab
2. Enter your **API ID** and **API Hash** (from https://my.telegram.org)
3. Enter your **Phone Number**
4. Click **Get Code** and enter the verification code from Telegram

### 4. Add Groups & Messages

- Click **Add Group** to add target groups
- Click **Add Message** to create your marketing message
- Configure frequency and delays in **Settings**

### 5. Start Marketing!

- Click **Send Now** for immediate sending
- Toggle **Auto-Send** for automatic scheduling

## 📋 Commands

| Command | Description |
|---------|-------------|
| `./start.sh` | Start server (interactive) |
| `./start_background.sh` | Start server in background |
| `./stop.sh` | Stop the server |
| `tail -f server.log` | View server logs |

## ⚙️ Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| Send Interval | Minutes between auto-sends | 30 |
| Delay | Seconds between each group | 3 |
| Auto Growth | Auto-find new groups | Off |
| Growth Interval | Hours between growth cycles | 6 |

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/config` | GET/POST | API configuration |
| `/api/settings` | GET/POST | Automation settings |
| `/api/groups` | GET/POST | Manage groups |
| `/api/groups/{id}` | DELETE | Remove group |
| `/api/groups/{id}/toggle` | PUT | Toggle group |
| `/api/messages` | GET/POST | Manage messages |
| `/api/send/now` | POST | Trigger immediate send |
| `/api/auto-send/start` | POST | Start auto-send |
| `/api/auto-send/stop` | POST | Stop auto-send |
| `/api/activity` | GET | Activity log |

## 📁 Project Structure

```
telegram_with_WEB/
├── app.py                 # FastAPI backend
├── telegram_service.py    # Telegram API service
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
├── start.sh               # Start script
├── start_background.sh    # Background start script
├── stop.sh                # Stop script
├── templates/
│   └── dashboard.html     # Web dashboard
├── static/                # Static files
├── app.log                # Application logs
└── server.log             # Server logs
```

## 🔒 Security Notes

- API credentials are stored locally in `config.json`
- Session files are stored locally (never shared)
- The server only runs on your local network
- All data stays on your machine

## 🆘 Troubleshooting

### Port Already in Use
The script automatically finds an available port starting from 8888.

### Connection Issues
1. Make sure you have internet access
2. Check if Telegram API credentials are correct
3. Verify phone number format (+country code)

### Login Failed
1. Double-check the verification code
2. Make sure you're not logged in elsewhere
3. Try requesting a new code

## 📞 Support

For issues or questions, contact TechyEra:
- 🌐 Website: https://techyera.co
- 📱 WhatsApp: +91 7987460954

---

Made with ❤️ by TechyEra

