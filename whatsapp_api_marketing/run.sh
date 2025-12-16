#!/bin/bash
# WhatsApp API Marketing - Quick Run Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run the marketer
python whatsapp_api_marketer.py "$@"
