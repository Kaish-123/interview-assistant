#!/bin/bash
# Run WhatsApp Marketing - CLI

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check for venv
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Pass all arguments to the script
python whatsapp_marketing.py "$@"

