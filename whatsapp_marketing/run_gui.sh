#!/bin/bash
# Run WhatsApp Marketing GUI

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check for venv
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run GUI
python marketing_gui.py





