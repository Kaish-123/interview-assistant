#!/bin/bash
# Quick run script - activates venv and runs the automation

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Run with any passed arguments
python whatsapp_status.py "$@"

