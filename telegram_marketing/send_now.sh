#!/bin/bash
BASE="/Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac/telegram_marketing"
echo "Sending messages to all groups now..."
"$BASE/venv/bin/python" "$BASE/cron_send_messages.py"
