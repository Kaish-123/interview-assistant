#!/bin/bash
# Telegram Marketing Automation Runner
# Usage: ./run.sh [command]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Run the marketer with all arguments passed
python telegram_marketer.py "$@"
