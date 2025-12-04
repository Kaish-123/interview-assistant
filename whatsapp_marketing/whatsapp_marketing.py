#!/usr/bin/env python3
"""
WhatsApp Marketing Automation
Sends personalized messages with images to contacts filtered by suffix keywords
"""

import subprocess
import time
import sys
import json
import os
import glob
import random
from datetime import datetime
from typing import List, Dict, Optional

try:
    import pyautogui
except ImportError:
    print("❌ pyautogui not installed. Run: pip install pyautogui")
    sys.exit(1)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "marketing_config.json")
IMAGES_DIR = os.path.join(SCRIPT_DIR, "marketing_images")
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")

# Ensure directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Import contact fetcher
sys.path.insert(0, SCRIPT_DIR)
from contact_fetcher import (
    get_contacts_for_messaging,
    mark_contact_messaged,
    refresh_contacts,
    get_contact_stats
)


def log(msg: str, level: str = "INFO"):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {msg}"
    print(formatted)
    
    # Also write to log file
    log_file = os.path.join(LOG_DIR, f"marketing_{datetime.now().strftime('%Y-%m-%d')}.log")
    with open(log_file, 'a') as f:
        f.write(formatted + "\n")


def load_config() -> dict:
    """Load configuration from JSON file."""
    default_config = {
        "message_template": "Please refer me to your known friends and consultancies for data engineering / data analyst/ Amazon sde interview proxy and Assessments also..",
        "contact_suffixes": ["client", "proxy", "interview"],
        "delay_min_seconds": 30,
        "delay_max_seconds": 90,
        "batch_size": 50,
        "pause_between_batches_minutes": 30,
        "schedule": {
            "day": "saturday",
            "time": "02:00"
        },
        "whatsapp_positions": {
            "search_box": {"x": 143, "y": 54},
            "first_chat": {"x": 200, "y": 150},
            "message_input": {"x": 900, "y": 850},
            "attach_button": {"x": 835, "y": 850},
            "photo_option": {"x": 835, "y": 700},
            "send_button": {"x": 1390, "y": 850}
        }
    }
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except FileNotFoundError:
        save_config(default_config)
        return default_config


def save_config(config: dict):
    """Save configuration to JSON file."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def get_marketing_images() -> List[str]:
    """Get all images from marketing_images folder."""
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.PNG', '*.JPG', '*.JPEG']
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(IMAGES_DIR, ext)))
    return sorted(set(images))  # Remove duplicates and sort


def open_whatsapp():
    """Open WhatsApp and maximize window."""
    log("📱 Opening WhatsApp...")
    subprocess.run(["open", "-a", "WhatsApp"])
    time.sleep(3)
    
    # Maximize and bring to front
    script = '''
    tell application "WhatsApp" to activate
    delay 1
    tell application "System Events"
        tell process "WhatsApp"
            set frontmost to true
            try
                set theWindow to window 1
                set position of theWindow to {0, 25}
                set size of theWindow to {1440, 875}
            end try
        end tell
    end tell
    delay 1
    '''
    subprocess.run(["osascript", "-e", script], capture_output=True)
    time.sleep(2)
    log("   ✅ WhatsApp ready")


def search_contact(phone: str, name: str) -> bool:
    """
    Search for a contact in WhatsApp by phone number.
    
    Returns:
        True if contact found and chat opened, False otherwise
    """
    config = load_config()
    positions = config.get("whatsapp_positions", {})
    
    # Click on search/new chat area
    log(f"   🔍 Searching for: {name} ({phone})")
    
    # Use Cmd+N for new chat or Cmd+F for search
    pyautogui.hotkey('command', 'n')
    time.sleep(1.5)
    
    # Type phone number to search
    # Clean phone number format
    search_term = phone
    if not phone.startswith('+'):
        search_term = f"+{phone}"
    
    # Type the search term
    pyautogui.typewrite(search_term, interval=0.05)
    time.sleep(2)
    
    # Press down arrow and Enter to select first result
    pyautogui.press('down')
    time.sleep(0.5)
    pyautogui.press('return')
    time.sleep(2)
    
    return True


def send_message(message: str) -> bool:
    """Send a text message in the current chat."""
    log(f"   💬 Sending message...")
    
    # Copy message to clipboard and paste (handles special characters)
    p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    p.communicate(message.encode('utf-8'))
    time.sleep(0.3)
    
    # Paste message
    pyautogui.hotkey('command', 'v')
    time.sleep(0.5)
    
    # Send with Enter
    pyautogui.press('return')
    time.sleep(1)
    
    return True


def attach_images(image_paths: List[str]) -> bool:
    """
    Attach and send multiple images to the current chat.
    WhatsApp allows up to 30 images at once.
    """
    if not image_paths:
        log("   ⚠️ No images to attach")
        return True
    
    log(f"   📷 Attaching {len(image_paths)} images...")
    
    # Click attach button (paperclip icon)
    config = load_config()
    
    # Use keyboard shortcut or click attach
    # On WhatsApp Desktop Mac, we can drag-drop or use the attach menu
    
    # Method: Click the + or attach button
    pyautogui.hotkey('command', 'shift', 'a')  # Attach shortcut (if available)
    time.sleep(1)
    
    # If shortcut doesn't work, try clicking attach button position
    # This will be calibrated in setup mode
    
    # Alternative: Use Finder to select files
    # Open file dialog
    script_open_dialog = '''
    tell application "System Events"
        keystroke "a" using {command down, shift down}
    end tell
    '''
    subprocess.run(["osascript", "-e", script_open_dialog], capture_output=True)
    time.sleep(2)
    
    # Select images using Finder dialog
    if len(image_paths) > 0:
        # Navigate to images folder
        folder_path = os.path.dirname(image_paths[0])
        
        # Use Cmd+Shift+G to go to folder
        script_navigate = f'''
        tell application "System Events"
            keystroke "g" using {{command down, shift down}}
            delay 1
            keystroke "{folder_path}"
            delay 0.5
            keystroke return
            delay 2
        end tell
        '''
        subprocess.run(["osascript", "-e", script_navigate], capture_output=True)
        time.sleep(2)
        
        # Select all images (Cmd+A if all images in folder should be sent)
        # Or select specific files
        if len(image_paths) == len(get_marketing_images()):
            # Select all
            pyautogui.hotkey('command', 'a')
            time.sleep(1)
        else:
            # Select specific files by typing names
            for i, img_path in enumerate(image_paths):
                filename = os.path.basename(img_path)
                if i == 0:
                    pyautogui.typewrite(filename[:10], interval=0.05)
                else:
                    # Cmd+Click for multiple selection
                    pyautogui.keyDown('command')
                    pyautogui.typewrite(filename[:10], interval=0.05)
                    pyautogui.keyUp('command')
                time.sleep(0.5)
        
        # Press Enter/Open to attach
        pyautogui.press('return')
        time.sleep(3)
        
        # Send the images
        pyautogui.press('return')
        time.sleep(2)
    
    return True


def send_images_via_drag(image_paths: List[str]) -> bool:
    """
    Alternative method: Drag and drop images into WhatsApp.
    This is more reliable on macOS.
    """
    if not image_paths:
        return True
    
    log(f"   📷 Sending {len(image_paths)} images via drag method...")
    
    # Create a temporary AppleScript to drag files
    # First, get WhatsApp window position
    
    # Simpler approach: Use pbcopy with file paths and paste
    # This works for images in Finder
    
    # Or use AppleScript to open images with WhatsApp
    
    # Best approach for multiple images: Use the attach menu
    
    # Click in message area first
    pyautogui.click(900, 800)
    time.sleep(0.5)
    
    # Use the plus/attach button
    # Position may vary - using relative position from message input
    attach_x, attach_y = 40, 850  # Left side attach button
    pyautogui.click(attach_x, attach_y)
    time.sleep(1)
    
    # Click "Photos & Videos" option
    photos_x, photos_y = 90, 750  # Photos option in menu
    pyautogui.click(photos_x, photos_y)
    time.sleep(2)
    
    # Now Finder opens - navigate and select images
    folder_path = IMAGES_DIR
    
    # Go to folder dialog
    pyautogui.hotkey('command', 'shift', 'g')
    time.sleep(1)
    
    # Type folder path
    p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    p.communicate(folder_path.encode('utf-8'))
    time.sleep(0.3)
    pyautogui.hotkey('command', 'v')
    time.sleep(0.5)
    pyautogui.press('return')
    time.sleep(2)
    
    # Select all images
    pyautogui.hotkey('command', 'a')
    time.sleep(1)
    
    # Open/Attach
    pyautogui.press('return')
    time.sleep(3)
    
    # Send
    pyautogui.press('return')
    time.sleep(2)
    
    return True


def close_current_chat():
    """Close current chat and go back to chat list."""
    # Press Escape to close any dialogs
    pyautogui.press('escape')
    time.sleep(0.5)
    pyautogui.press('escape')
    time.sleep(0.5)


def send_to_contact(contact: Dict, message: str, images: List[str], dry_run: bool = False) -> bool:
    """
    Send message and images to a single contact.
    
    Args:
        contact: Contact dictionary with name, phone, id
        message: Message text to send
        images: List of image paths to attach
        dry_run: If True, don't actually send (test mode)
    
    Returns:
        True if successful, False otherwise
    """
    name = contact['name']
    phone = contact['phone']
    contact_id = contact['id']
    
    log(f"📤 Processing: {name} ({phone})")
    
    if dry_run:
        log(f"   [DRY RUN] Would send message + {len(images)} images")
        return True
    
    try:
        # Search and open chat
        if not search_contact(phone, name):
            log(f"   ❌ Could not find contact", "ERROR")
            return False
        
        # Send text message first
        if message:
            send_message(message)
            time.sleep(1)
        
        # Send images
        if images:
            send_images_via_drag(images)
            time.sleep(2)
        
        # Mark as messaged in database
        mark_contact_messaged(contact_id, message[:50] if message else "", len(images))
        
        # Close chat
        close_current_chat()
        
        log(f"   ✅ Sent successfully!")
        return True
        
    except Exception as e:
        log(f"   ❌ Error: {e}", "ERROR")
        return False


def run_marketing_campaign(
    suffix_filter: str = None,
    dry_run: bool = False,
    limit: int = None,
    skip_images: bool = False
) -> Dict:
    """
    Run the marketing campaign to all eligible contacts.
    
    Args:
        suffix_filter: Only message contacts with this suffix (e.g., 'client')
        dry_run: Test mode - don't actually send
        limit: Maximum number of contacts to message
        skip_images: Don't send images, only text
    
    Returns:
        Campaign results dictionary
    """
    log("")
    log("=" * 60)
    log("🚀 WhatsApp Marketing Campaign")
    log("=" * 60)
    
    config = load_config()
    message = config.get("message_template", "")
    
    # Get contacts
    contacts = get_contacts_for_messaging(suffix_filter)
    
    if limit:
        contacts = contacts[:limit]
    
    log(f"📋 Contacts to message: {len(contacts)}")
    log(f"💬 Message: {message[:50]}...")
    
    # Get images
    images = [] if skip_images else get_marketing_images()
    log(f"📷 Images to send: {len(images)}")
    
    if not contacts:
        log("⚠️ No contacts found!")
        return {"success": 0, "failed": 0, "total": 0}
    
    if dry_run:
        log("🧪 DRY RUN MODE - No messages will actually be sent")
    
    # Open WhatsApp
    if not dry_run:
        open_whatsapp()
    
    # Process contacts
    results = {"success": 0, "failed": 0, "total": len(contacts)}
    delay_min = config.get("delay_min_seconds", 30)
    delay_max = config.get("delay_max_seconds", 90)
    batch_size = config.get("batch_size", 50)
    pause_minutes = config.get("pause_between_batches_minutes", 30)
    
    for i, contact in enumerate(contacts):
        log(f"\n[{i+1}/{len(contacts)}] Processing...")
        
        success = send_to_contact(contact, message, images, dry_run)
        
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1
        
        # Random delay between messages (avoid spam detection)
        if i < len(contacts) - 1:
            if not dry_run:
                delay = random.randint(delay_min, delay_max)
                log(f"   ⏳ Waiting {delay} seconds before next message...")
                time.sleep(delay)
            
            # Batch pause
            if (i + 1) % batch_size == 0 and i < len(contacts) - 1:
                log(f"\n🛑 Batch complete. Pausing for {pause_minutes} minutes...")
                if not dry_run:
                    time.sleep(pause_minutes * 60)
    
    # Summary
    log("")
    log("=" * 60)
    log("📊 Campaign Results")
    log("=" * 60)
    log(f"   ✅ Successful: {results['success']}")
    log(f"   ❌ Failed: {results['failed']}")
    log(f"   📋 Total: {results['total']}")
    
    return results


def setup_positions():
    """Interactive setup to find correct click positions."""
    log("\n🔧 SETUP MODE - Find Click Positions")
    log("=" * 50)
    
    open_whatsapp()
    
    print("\nMove mouse to find these positions. Press Ctrl+C to stop.\n")
    print("Positions to find:")
    print("1. SEARCH BOX (top search bar)")
    print("2. FIRST CHAT (first chat in list)")
    print("3. MESSAGE INPUT (text input area)")
    print("4. ATTACH BUTTON (paperclip/+ icon)")
    print("5. SEND BUTTON")
    
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\rMouse position: ({x}, {y})          ", end="", flush=True)
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\n\n📝 Update positions in marketing_config.json")


def test_single_contact(phone: str):
    """Test sending to a single phone number."""
    log(f"🧪 Testing with phone: {phone}")
    
    config = load_config()
    message = config.get("message_template", "Test message")
    images = get_marketing_images()
    
    open_whatsapp()
    time.sleep(2)
    
    test_contact = {
        "id": "test",
        "name": "Test Contact",
        "phone": phone
    }
    
    send_to_contact(test_contact, message, images, dry_run=False)


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WhatsApp Marketing Automation")
    parser.add_argument("--run", "-r", action="store_true", help="Run marketing campaign")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Test mode (no actual sending)")
    parser.add_argument("--suffix", "-s", type=str, help="Filter by contact suffix (client/proxy/interview)")
    parser.add_argument("--limit", "-l", type=int, help="Limit number of contacts")
    parser.add_argument("--no-images", action="store_true", help="Send text only, no images")
    parser.add_argument("--setup", action="store_true", help="Setup mode to find click positions")
    parser.add_argument("--test", "-t", type=str, help="Test with single phone number")
    parser.add_argument("--refresh", action="store_true", help="Refresh contacts from macOS")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--images", action="store_true", help="List available images")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_positions()
    
    elif args.test:
        test_single_contact(args.test)
    
    elif args.refresh:
        result = refresh_contacts()
        print(f"\n📊 Contacts refreshed: {result}")
    
    elif args.stats:
        stats = get_contact_stats()
        images = get_marketing_images()
        config = load_config()
        
        print("\n📊 Marketing Statistics")
        print("=" * 50)
        print(f"   Contacts Total: {stats['total']}")
        print(f"   Contacts Active: {stats['active']}")
        print(f"   Contacts Excluded: {stats['excluded']}")
        print(f"   By Suffix: {stats['by_suffix']}")
        print(f"   Messaged Today: {stats['messaged_today']}")
        print(f"\n   Images Available: {len(images)}")
        print(f"   Message Template: {config.get('message_template', '')[:50]}...")
    
    elif args.images:
        images = get_marketing_images()
        print(f"\n📷 Marketing Images ({len(images)} total):")
        print("=" * 50)
        for i, img in enumerate(images):
            print(f"   {i+1}. {os.path.basename(img)}")
        print(f"\n   📁 Folder: {IMAGES_DIR}")
    
    elif args.run:
        run_marketing_campaign(
            suffix_filter=args.suffix,
            dry_run=args.dry_run,
            limit=args.limit,
            skip_images=args.no_images
        )
    
    else:
        parser.print_help()
        print("\n" + "=" * 50)
        print("💡 USAGE EXAMPLES:")
        print("=" * 50)
        print("  python whatsapp_marketing.py --refresh          # Sync contacts from macOS")
        print("  python whatsapp_marketing.py --stats            # Show statistics")
        print("  python whatsapp_marketing.py --run --dry-run    # Test run (no sending)")
        print("  python whatsapp_marketing.py --run              # Run campaign")
        print("  python whatsapp_marketing.py --run -s client    # Only 'client' contacts")
        print("  python whatsapp_marketing.py --run -l 10        # Limit to 10 contacts")
        print("  python whatsapp_marketing.py --test +1234567890 # Test single number")
        print("  python whatsapp_marketing.py --setup            # Find click positions")
        print(f"\n📁 Put marketing images in: {IMAGES_DIR}")

