#!/bin/bash
# Easy WhatsApp Marketing - Quick Start

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "╔══════════════════════════════════════════════════════════╗"
echo "║         📱 EASY WHATSAPP MARKETING - FREE                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Run with arguments
python easy_whatsapp.py "$@"

