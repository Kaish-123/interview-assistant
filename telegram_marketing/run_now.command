#!/bin/bash
cd ~/Downloads/chatgpt_gui_mac/telegram_marketing
bash run_growth.sh --no-stagger >> cron_growth.log 2>&1
echo "Done. Exit code: $?"
