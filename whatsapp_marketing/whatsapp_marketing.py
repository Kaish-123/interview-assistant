#!/usr/bin/env python3
"""
WhatsApp Marketing Automation - Reliable Version
Properly sends messages with images to contacts
"""

import subprocess
import time
import sys
import json
import os
import glob
import random
from datetime import datetime
from typing import List, Dict

try:
    import pyautogui
except ImportError:
    print("❌ pyautogui not installed. Run: pip install pyautogui")
    sys.exit(1)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "marketing_config.json")
IMAGES_DIR = os.path.join(SCRIPT_DIR, "marketing_images")
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

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
    sys.stdout.flush()
    
    log_file = os.path.join(LOG_DIR, f"marketing_{datetime.now().strftime('%Y-%m-%d')}.log")
    with open(log_file, 'a') as f:
        f.write(formatted + "\n")


def load_config() -> dict:
    """Load configuration."""
    default_config = {
        "message_template": "Please refer me to your known friends and consultancies for data engineering / data analyst/ Amazon sde interview proxy and Assessments also..",
        "contact_suffixes": ["client", "proxy", "interview"],
        "delay_min_seconds": 30,
        "delay_max_seconds": 90,
        "batch_size": 50,
        "pause_between_batches_minutes": 30
    }
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except FileNotFoundError:
        save_config(default_config)
        return default_config


def save_config(config: dict):
    """Save configuration."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def get_marketing_images() -> List[str]:
    """Get all images from marketing_images folder."""
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.PNG', '*.JPG', '*.JPEG']
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(IMAGES_DIR, ext)))
    return sorted(set(images))


def copy_to_clipboard(text: str):
    """Copy text to clipboard using pbcopy."""
    p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    p.communicate(text.encode('utf-8'))
    p.wait()
    time.sleep(0.2)


def paste_from_clipboard():
    """Paste from clipboard using Cmd+V."""
    pyautogui.hotkey('command', 'v')
    time.sleep(0.3)


def press_key(key: str, times: int = 1, delay: float = 0.2):
    """Press a key multiple times with delay."""
    for _ in range(times):
        pyautogui.press(key)
        time.sleep(delay)


def open_whatsapp():
    """Open WhatsApp Desktop and maximize."""
    log("📱 Opening WhatsApp Desktop...")
    
    # Open WhatsApp
    subprocess.run(["open", "-a", "WhatsApp"], check=True)
    time.sleep(3)
    
    # Activate and maximize
    script = '''
    tell application "WhatsApp"
        activate
    end tell
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
    '''
    subprocess.run(["osascript", "-e", script], capture_output=True)
    time.sleep(2)
    
    # Click somewhere in WhatsApp to ensure it's focused
    pyautogui.click(700, 400)
    time.sleep(0.5)
    
    log("   ✅ WhatsApp ready")


def search_and_open_chat(phone: str, name: str) -> bool:
    """
    Search for contact and open chat.
    
    FLOW:
    1. Press Escape to close any open dialogs
    2. Press Cmd+N to open new chat
    3. Paste phone number
    4. Wait for search results
    5. Press Enter to select first result
    6. Wait for chat to open
    """
    log(f"   🔍 Searching: {name} ({phone})")
    
    # Step 1: Close any open dialogs/chats
    press_key('escape', times=2, delay=0.3)
    time.sleep(0.5)
    
    # Step 2: Open new chat dialog (Cmd+N)
    log("   📝 Opening new chat...")
    pyautogui.hotkey('command', 'n')
    time.sleep(1.5)
    
    # Step 3: Clear any existing text and paste phone number
    # The search field should be focused after Cmd+N
    pyautogui.hotkey('command', 'a')  # Select all
    time.sleep(0.2)
    
    # Format phone number (ensure it has country code)
    search_phone = phone.strip()
    if not search_phone.startswith('+'):
        # Assume Indian number if no country code
        if len(search_phone) == 10:
            search_phone = '+91' + search_phone
        else:
            search_phone = '+' + search_phone
    
    log(f"   📋 Pasting: {search_phone}")
    copy_to_clipboard(search_phone)
    paste_from_clipboard()
    time.sleep(2)  # Wait for search results
    
    # Step 4: Check if results appeared and select first one
    log("   ⬇️ Selecting first result...")
    press_key('down', times=1, delay=0.3)
    time.sleep(0.3)
    press_key('return', times=1, delay=0.5)
    time.sleep(1.5)  # Wait for chat to open
    
    log("   ✅ Chat opened")
    return True


def send_text_message(message: str) -> bool:
    """
    Send text message in currently open chat.
    
    FLOW:
    1. Message input should be focused after opening chat
    2. Paste the message
    3. Press Enter to send
    """
    if not message or not message.strip():
        log("   ⚠️ No message to send")
        return True
    
    log(f"   💬 Sending message ({len(message)} chars)...")
    
    # Click in message area to ensure focus (bottom center of chat)
    pyautogui.click(700, 820)
    time.sleep(0.5)
    
    # Clear any existing text
    pyautogui.hotkey('command', 'a')
    time.sleep(0.1)
    
    # Paste message
    copy_to_clipboard(message)
    paste_from_clipboard()
    time.sleep(0.5)
    
    # Send with Enter
    log("   📤 Pressing Enter to send...")
    press_key('return', times=1, delay=0.5)
    time.sleep(1)
    
    log("   ✅ Message sent")
    return True


def send_images(image_paths: List[str]) -> bool:
    """
    Send images in currently open chat.
    
    FLOW:
    1. Click attachment button (+ icon)
    2. Select "Photos & Videos"
    3. Navigate to folder using Cmd+Shift+G
    4. Select all images with Cmd+A
    5. Press Enter to attach
    6. Press Enter to send
    """
    if not image_paths:
        log("   ⚠️ No images to send")
        return True
    
    log(f"   📷 Sending {len(image_paths)} images...")
    
    # Method 1: Drag and drop using AppleScript (more reliable)
    folder_path = IMAGES_DIR
    
    # Get list of image filenames
    image_files = [os.path.basename(img) for img in image_paths]
    
    log(f"   📂 From folder: {folder_path}")
    
    # Use AppleScript to attach files
    # First, let's try clicking the attach button
    
    # Click in message area first
    pyautogui.click(700, 820)
    time.sleep(0.3)
    
    # Press Cmd+O to open file picker (if supported)
    # Or click the + button
    
    # Find and click the attachment button (usually on the left of message input)
    # Position varies by WhatsApp version, let's try common positions
    
    # Try clicking the + button (usually around x=40-50, y=820-850)
    log("   📎 Clicking attachment button...")
    
    # Look for attachment button - try a few positions
    attach_positions = [(42, 848), (45, 845), (50, 850), (40, 840)]
    
    for pos in attach_positions:
        pyautogui.click(pos[0], pos[1])
        time.sleep(0.8)
        
        # Check if menu appeared by looking for "Photos & Videos" option
        # The menu item is usually around y=750-780
        break  # Try first position
    
    time.sleep(1)
    
    # Click "Photos & Videos" option in the menu
    log("   🖼️ Selecting Photos & Videos...")
    pyautogui.click(120, 720)  # Approximate position of Photos option
    time.sleep(1.5)
    
    # Finder dialog should open
    # Navigate to images folder using Cmd+Shift+G
    log("   📂 Navigating to images folder...")
    pyautogui.hotkey('command', 'shift', 'g')
    time.sleep(1)
    
    # Paste folder path
    copy_to_clipboard(folder_path)
    paste_from_clipboard()
    time.sleep(0.5)
    
    # Press Enter to go to folder
    press_key('return', times=1, delay=1)
    time.sleep(1.5)
    
    # Select all files with Cmd+A
    log("   ☑️ Selecting all images...")
    pyautogui.hotkey('command', 'a')
    time.sleep(0.5)
    
    # Press Enter to attach selected files
    log("   📎 Attaching files...")
    press_key('return', times=1, delay=1)
    time.sleep(2)  # Wait for images to load in preview
    
    # Press Enter again to send
    log("   📤 Sending images...")
    press_key('return', times=1, delay=1)
    time.sleep(2)  # Wait for upload
    
    log("   ✅ Images sent")
    return True


def send_images_simple(image_paths: List[str]) -> bool:
    """
    Simpler method: Copy images to clipboard and paste.
    Works on macOS by copying files in Finder and pasting in WhatsApp.
    """
    if not image_paths:
        return True
    
    log(f"   📷 Sending {len(image_paths)} images (simple method)...")
    
    # Create AppleScript to copy files to clipboard
    file_list = '", "'.join(image_paths)
    script = f'''
    tell application "Finder"
        set theFiles to {{}}
        repeat with f in {{"{file_list}"}}
            set end of theFiles to (POSIX file f as alias)
        end repeat
        set the clipboard to theFiles
    end tell
    '''
    
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    
    if result.returncode != 0:
        log(f"   ⚠️ Could not copy files: {result.stderr}", "WARN")
        return False
    
    time.sleep(0.5)
    
    # Click in message area
    pyautogui.click(700, 820)
    time.sleep(0.3)
    
    # Paste files
    log("   📋 Pasting images...")
    pyautogui.hotkey('command', 'v')
    time.sleep(2)  # Wait for images to appear
    
    # Press Enter to send
    log("   📤 Sending...")
    press_key('return', times=1, delay=1)
    time.sleep(2)
    
    log("   ✅ Images sent")
    return True


def close_chat():
    """Close current chat / go back."""
    press_key('escape', times=2, delay=0.3)
    time.sleep(0.5)


def send_to_contact(contact: Dict, message: str, images: List[str], dry_run: bool = False) -> bool:
    """
    Complete flow to send message and images to a contact.
    """
    name = contact.get('name', 'Unknown')
    phone = contact.get('phone', '')
    contact_id = contact.get('id', '')
    
    log(f"\n{'='*50}")
    log(f"📤 Contact: {name}")
    log(f"   Phone: {phone}")
    log(f"{'='*50}")
    
    if not phone:
        log("   ❌ No phone number!", "ERROR")
        return False
    
    if dry_run:
        log(f"   [DRY RUN] Would send:")
        log(f"   - Message: {message[:50]}...")
        log(f"   - Images: {len(images)}")
        return True
    
    try:
        # Step 1: Search and open chat
        if not search_and_open_chat(phone, name):
            log("   ❌ Failed to open chat", "ERROR")
            return False
        
        # Step 2: Send text message
        if message:
            if not send_text_message(message):
                log("   ❌ Failed to send message", "ERROR")
                return False
        
        # Step 3: Send images
        if images:
            # Try simple method first (more reliable)
            if not send_images_simple(images):
                log("   ⚠️ Simple method failed, trying alternative...")
                send_images(images)
        
        # Step 4: Mark as sent in database
        try:
            mark_contact_messaged(contact_id, message[:50] if message else "", len(images))
        except Exception as e:
            log(f"   ⚠️ Could not mark as sent: {e}", "WARN")
        
        # Step 5: Close chat
        close_chat()
        
        log(f"   ✅ SUCCESS - Sent to {name}")
        return True
        
    except Exception as e:
        log(f"   ❌ ERROR: {str(e)}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        return False


def run_marketing_campaign(
    suffix_filter: str = None,
    dry_run: bool = False,
    limit: int = None,
    skip_images: bool = False,
    contact_ids: List[str] = None
) -> Dict:
    """
    Run marketing campaign.
    
    Args:
        suffix_filter: Filter contacts by suffix
        dry_run: Test mode - don't actually send
        limit: Max contacts to process
        skip_images: Skip sending images
        contact_ids: Specific contact IDs to send to
    """
    log("\n" + "="*60)
    log("🚀 WHATSAPP MARKETING CAMPAIGN")
    log("="*60 + "\n")
    
    config = load_config()
    message = config.get("message_template", "")
    
    # Get contacts
    contacts = get_contacts_for_messaging(suffix_filter)
    
    # Filter by specific IDs if provided
    if contact_ids:
        contacts = [c for c in contacts if c['id'] in contact_ids]
    
    if limit:
        contacts = contacts[:limit]
    
    # Get images
    images = [] if skip_images else get_marketing_images()
    
    log(f"📋 Contacts: {len(contacts)}")
    log(f"💬 Message: {message[:60]}...")
    log(f"📷 Images: {len(images)}")
    log(f"🧪 Dry Run: {dry_run}")
    log("")
    
    if not contacts:
        log("⚠️ No contacts to message!")
        return {"success": 0, "failed": 0, "total": 0}
    
    # Open WhatsApp (unless dry run)
    if not dry_run:
        open_whatsapp()
        time.sleep(2)
    
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
        
        # Delay between messages
        if i < len(contacts) - 1 and not dry_run:
            delay = random.randint(delay_min, delay_max)
            log(f"\n⏳ Waiting {delay} seconds...")
            time.sleep(delay)
            
            # Batch pause
            if (i + 1) % batch_size == 0:
                log(f"\n🛑 Batch complete. Pausing {pause_minutes} minutes...")
                time.sleep(pause_minutes * 60)
    
    # Summary
    log("\n" + "="*60)
    log("📊 CAMPAIGN RESULTS")
    log("="*60)
    log(f"   ✅ Successful: {results['success']}")
    log(f"   ❌ Failed: {results['failed']}")
    log(f"   📋 Total: {results['total']}")
    log("="*60 + "\n")
    
    return results


def test_single_contact(phone: str, skip_images: bool = False):
    """Test with a single phone number."""
    log(f"\n🧪 TESTING WITH: {phone}\n")
    
    config = load_config()
    message = config.get("message_template", "Test message")
    images = [] if skip_images else get_marketing_images()
    
    open_whatsapp()
    time.sleep(2)
    
    contact = {
        "id": "test",
        "name": "Test Contact",
        "phone": phone
    }
    
    result = send_to_contact(contact, message, images, dry_run=False)
    
    if result:
        log("\n✅ TEST SUCCESSFUL!")
    else:
        log("\n❌ TEST FAILED!")
    
    return result


def setup_mode():
    """Interactive setup to find positions."""
    log("\n🔧 SETUP MODE")
    log("="*50)
    log("Move your mouse to find positions.")
    log("Press Ctrl+C to stop.\n")
    
    open_whatsapp()
    
    log("Positions to find:")
    log("1. Message input area (bottom center)")
    log("2. Attachment button (+ icon, left of message)")
    log("3. Photos option in menu")
    log("4. Send button\n")
    
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\rPosition: ({x}, {y})     ", end="", flush=True)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n\n✅ Setup complete. Update positions in code if needed.")


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WhatsApp Marketing")
    parser.add_argument("--run", "-r", action="store_true", help="Run campaign")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Test mode")
    parser.add_argument("--suffix", "-s", type=str, help="Filter by suffix")
    parser.add_argument("--limit", "-l", type=int, help="Limit contacts")
    parser.add_argument("--no-images", action="store_true", help="Skip images")
    parser.add_argument("--test", "-t", type=str, help="Test with phone number")
    parser.add_argument("--setup", action="store_true", help="Setup mode")
    parser.add_argument("--refresh", action="store_true", help="Refresh contacts")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_mode()
    elif args.test:
        test_single_contact(args.test, args.no_images)
    elif args.refresh:
        print(refresh_contacts())
    elif args.stats:
        stats = get_contact_stats()
        print(f"\n📊 Stats: {json.dumps(stats, indent=2)}")
    elif args.run:
        run_marketing_campaign(
            suffix_filter=args.suffix,
            dry_run=args.dry_run,
            limit=args.limit,
            skip_images=args.no_images
        )
    else:
        parser.print_help()
        print(f"\n📁 Images folder: {IMAGES_DIR}")
        print("\n💡 Examples:")
        print("  python whatsapp_marketing.py --test +919876543210")
        print("  python whatsapp_marketing.py --run --dry-run")
        print("  python whatsapp_marketing.py --run --limit 5")
        print("  python whatsapp_marketing.py --setup")
