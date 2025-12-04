#!/usr/bin/env python3
"""WhatsApp Status Automation - Simple & Direct"""

import subprocess
import time
import sys
import json
import os

try:
    import pyautogui
except ImportError:
    print("Run: pip install pyautogui")
    sys.exit(1)

pyautogui.FAILSAFE = True
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except:
        return {"status_captions": ["Weekend vibes ✨"], "current_caption_index": 0}

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def get_caption(config):
    captions = config.get("status_captions", ["Status"])
    idx = config.get("current_caption_index", 0) % len(captions)
    return captions[idx]

def open_whatsapp():
    """Open WhatsApp, bring to front, and MAXIMIZE to full screen."""
    print("📱 Opening WhatsApp...")
    subprocess.run(["open", "-a", "WhatsApp"])
    time.sleep(3)
    
    # Activate WhatsApp and MAXIMIZE window
    script = '''
    tell application "WhatsApp" to activate
    delay 1
    tell application "System Events"
        tell process "WhatsApp"
            set frontmost to true
            -- Maximize the window to full screen size
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
    time.sleep(1)
    print("   ✅ WhatsApp maximized and ready")

def set_status(caption=None):
    """Set WhatsApp status using simple clicks."""
    config = load_config()
    caption = caption or get_caption(config)
    
    print("\n" + "="*50)
    print("🚀 WhatsApp Status Automation")
    print(f"   Caption: {caption}")
    print("="*50 + "\n")
    
    # Step 1: Open WhatsApp
    open_whatsapp()
    
    # Step 2: Click Status icon
    # Use screen coordinates - Status is usually 2nd icon in left sidebar
    print("📍 Clicking Status icon...")
    
    # Get current mouse position to understand screen
    screen_w, screen_h = pyautogui.size()
    print(f"   Screen size: {screen_w}x{screen_h}")
    
    # WhatsApp window is typically positioned at left side
    # Status icon is in the left sidebar, 2nd from top
    # Typical position: around x=125, y=160 for standard WhatsApp window
    
    # Click Status tab - YOUR CALIBRATED POSITION
    status_x = 33
    status_y = 198
    print(f"   Clicking Status at ({status_x}, {status_y})")
    pyautogui.click(status_x, status_y)
    time.sleep(2)
    
    # Step 3: Click the pencil/text icon to add text status
    print("✏️ Clicking text status button...")
    # Pencil icon - YOUR CALIBRATED POSITION
    pencil_x = 1364
    pencil_y = 133
    print(f"   Clicking pencil at ({pencil_x}, {pencil_y})")
    pyautogui.click(pencil_x, pencil_y)
    time.sleep(2)
    
    # Step 4: Type and send
    print(f"💬 Typing: {caption}")
    
    # Type using clipboard (supports emojis)
    p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    p.communicate(caption.encode('utf-8'))
    time.sleep(0.5)
    pyautogui.hotkey('command', 'v')
    time.sleep(1)
    
    # Send - Click the send button at YOUR CALIBRATED POSITION
    print("   Clicking Send button...")
    send_x = 1402
    send_y = 874
    print(f"   Clicking Send at ({send_x}, {send_y})")
    pyautogui.click(send_x, send_y)
    time.sleep(1)
    
    # Update caption index
    config["current_caption_index"] = config.get("current_caption_index", 0) + 1
    save_config(config)
    
    print("\n✅ Done! Check WhatsApp to verify.")

def setup():
    """Find correct click positions."""
    print("\n🔧 SETUP MODE - Find Click Positions")
    print("="*50)
    
    open_whatsapp()
    
    print("\nMove mouse to see coordinates. Press Ctrl+C to stop.\n")
    print("1. Move to STATUS icon (circle in left sidebar)")
    print("2. Move to PENCIL icon (to create text status)")
    print("3. Note both positions!\n")
    
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\rMouse position: ({x}, {y})          ", end="", flush=True)
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\n\n📝 Update the coordinates in set_status() function:")
        print("   status_x, status_y = YOUR_STATUS_POSITION")
        print("   pencil_x, pencil_y = YOUR_PENCIL_POSITION")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", "-r", action="store_true")
    parser.add_argument("--caption", "-c", type=str)
    parser.add_argument("--setup", action="store_true")
    
    args = parser.parse_args()
    
    if args.setup:
        setup()
    elif args.run or args.caption:
        set_status(args.caption)
    else:
        parser.print_help()
        print("\n./run.sh --setup  # Find positions first")
        print("./run.sh --run    # Run automation")

if __name__ == "__main__":
    main()
