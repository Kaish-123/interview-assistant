#!/bin/bash
# Broadcast Marketing CLI (Mac Contacts + WhatsApp)
# Usage: ./run.sh [sync|build|sync-build|send|send-dry-run|install-schedule|help]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
PYTHON="${PYTHON:-python3}"

case "${1:-help}" in
  setup)
    echo "Installing Python dependencies for WhatsApp send..."
    $PYTHON -m pip install -q -r requirements.txt
    echo "Building broadcast lists from contacts..."
    if ! $PYTHON build_broadcast_lists.py; then
      echo ""
      echo "Load your contacts first: ./run.sh load-contacts"
      exit 1
    fi
    echo "Done. Edit message.txt then run ./run.sh send-dry-run and ./run.sh send"
    ;;
  load-contacts)
    echo "Exporting contacts from Mac Contacts and loading into contacts.csv..."
    $PYTHON export_and_load_contacts.py
    ;;
  sync)
    echo "Syncing contacts from Mac Contacts app..."
    $PYTHON sync_contacts_from_mac.py
    ;;
  build)
    echo "Building broadcast lists from contacts and keywords..."
    $PYTHON build_broadcast_lists.py
    ;;
  sync-build)
    echo "Syncing from Mac Contacts, then building lists..."
    $PYTHON sync_contacts_from_mac.py
    $PYTHON build_broadcast_lists.py
    ;;
  send)
    echo "Sending broadcasts (WhatsApp Web will open)..."
    $PYTHON send_broadcasts.py
    ;;
  send-dry-run)
    $PYTHON send_broadcasts.py --dry-run
    ;;
  send-list)
    if [ -z "$2" ]; then
      echo "Usage: ./run.sh send-list <ListName>"
      echo "Example: ./run.sh send-list Clients_1"
      exit 1
    fi
    $PYTHON send_broadcasts.py --list "$2"
    ;;
  import-vcard)
    if [ -z "$2" ]; then
      echo "Usage: ./run.sh import-vcard <path-to-your-.vcf-file>"
      echo "Example: ./run.sh import-vcard ~/Desktop/contacts.vcf"
      echo "Export first: Contacts app → File → Export → Export vCard… → save the file."
      exit 1
    fi
    $PYTHON import_vcard.py "$2"
    ;;
  install-schedule)
    bash "$SCRIPT_DIR/install_schedule.sh"
    ;;
  install-send-schedule)
    bash "$SCRIPT_DIR/install_send_schedule.sh"
    ;;
  help|--help|-h)
    echo ""
    echo "Broadcast Marketing - Mac Contacts + WhatsApp broadcast lists"
    echo ""
    echo "  ./run.sh load-contacts  One step: export Mac Contacts → contacts.csv → build lists (recommended)"
    echo "  ./run.sh setup          One-time: install deps + build lists"
    echo "  ./run.sh sync           Sync contacts from Mac Contacts app → contacts.csv"
    echo "  ./run.sh build          Build lists from contacts.csv + config.json"
    echo "  ./run.sh sync-build     Sync from Mac, then build lists"
    echo "  ./run.sh send           Send message to all built lists (WhatsApp)"
    echo "  ./run.sh send-dry-run   Preview recipients and message, no send"
    echo "  ./run.sh send-list NAME Send only to one list (e.g. Clients_1)"
    echo "  ./run.sh import-vcard FILE  Load contacts from .vcf (Contacts → File → Export → vCard)"
    echo "  ./run.sh install-schedule  Run sync+build every 6 hours (LaunchAgent)"
    echo "  ./run.sh install-send-schedule  Send WhatsApp broadcasts every 30 min (LaunchAgent)"
    echo "  ./run.sh help           This help"
    echo ""
    echo "Easiest: ./run.sh load-contacts   (exports from Mac Contacts and builds lists in one go)"
    echo ""
    ;;
  *)
    echo "Unknown command: $1"
    ./run.sh help
    exit 1
    ;;
esac
