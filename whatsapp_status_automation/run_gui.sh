#!/bin/bash
# Quick run script for GUI - activates venv and runs the GUI

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Run GUI
python gui.py

