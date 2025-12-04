#!/usr/bin/env python3
"""WhatsApp Status Automation - Text & Image Support"""

import subprocess
import time
import sys
import json
import os
import glob

try:
    import pyautogui
except ImportError:
    print("Run: pip install pyautogui")
    sys.exit(1)

pyautogui.FAILSAFE = True
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
IMAGES_DIR = os.path.join(SCRIPT_DIR, "status_images")

# Ensure images directory exists
os.makedirs(IMAGES_DIR, exist_ok=True)

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except:
        return {"status_captions": ["Weekend vibes ✨"], "current_caption_index": 0, "current_image_index": 0}

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def get_caption(config):
    captions = config.get("status_captions", [])
    if not captions:
        return "Weekend vibes ✨"
    idx = config.get("current_caption_index", 0) % len(captions)
    return captions[idx]

def get_images():
    """Get all images from status_images folder."""
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(IMAGES_DIR, ext)))
        images.extend(glob.glob(os.path.join(IMAGES_DIR, ext.upper())))
    return sorted(images)

def get_next_image(config):
    """Get next image to upload with its caption."""
    images = get_images()
    if not images:
        return None, None
    
    idx = config.get("current_image_index", 0) % len(images)
    image_path = images[idx]
    
    # Caption can be: 
    # 1. From image_captions in config (matched by filename)
    # 2. From filename (without extension)
    # 3. Default caption
    filename = os.path.basename(image_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    image_captions = config.get("image_captions", {})
    caption = image_captions.get(filename, name_without_ext.replace("_", " ").replace("-", " "))
    
    return image_path, caption

def open_whatsapp():
    """Open WhatsApp, bring to front, and MAXIMIZE to full screen."""
    print("📱 Opening WhatsApp...")
    subprocess.run(["open", "-a", "WhatsApp"])
    time.sleep(3)
    
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
    time.sleep(1)
    print("   ✅ WhatsApp maximized and ready")

def set_text_status(caption=None):
    """Set text-only WhatsApp status."""
    config = load_config()
    caption = caption or get_caption(config)
    
    print("\n" + "="*50)
    print("🚀 WhatsApp TEXT Status")
    print(f"   Caption: {caption}")
    print("="*50 + "\n")
    
    open_whatsapp()
    
    # Click Status icon
    print("📍 Clicking Status icon...")
    status_x, status_y = 33, 198
    pyautogui.click(status_x, status_y)
    time.sleep(2)
    
    # Click pencil icon for text status
    print("✏️ Clicking text status button...")
    pencil_x, pencil_y = 1364, 133
    pyautogui.click(pencil_x, pencil_y)
    time.sleep(2)
    
    # Type caption
    print(f"💬 Typing: {caption}")
    p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    p.communicate(caption.encode('utf-8'))
    time.sleep(0.5)
    pyautogui.hotkey('command', 'v')
    time.sleep(1)
    
    # Click Send
    print("   Clicking Send button...")
    send_x, send_y = 1402, 874
    pyautogui.click(send_x, send_y)
    time.sleep(1)
    
    # Update caption index
    config["current_caption_index"] = config.get("current_caption_index", 0) + 1
    save_config(config)
    
    print("\n✅ Text status posted!")

def set_image_status(image_path=None, caption=None):
    """Set image WhatsApp status with caption."""
    config = load_config()
    
    # Get image and caption
    if not image_path:
        image_path, auto_caption = get_next_image(config)
        if not image_path:
            print("❌ No images found in status_images/ folder!")
            print(f"   Add images to: {IMAGES_DIR}")
            return
        caption = caption or auto_caption
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print("\n" + "="*50)
    print("🖼️ WhatsApp IMAGE Status")
    print(f"   Image: {os.path.basename(image_path)}")
    print(f"   Caption: {caption}")
    print("="*50 + "\n")
    
    open_whatsapp()
    
    # Click Status icon
    print("📍 Clicking Status icon...")
    status_x, status_y = 33, 198
    pyautogui.click(status_x, status_y)
    time.sleep(2)
    
    # Click camera icon (opens camera view)
    print("📷 Clicking camera button...")
    camera_x, camera_y = 1312, 131
    pyautogui.click(camera_x, camera_y)
    time.sleep(2)
    
    # Click gallery/photo selection icon to open Finder (NOT the camera shutter)
    print("🖼️ Clicking gallery button to select photo...")
    gallery_x, gallery_y = 41, 836  # Calibrated position
    pyautogui.click(gallery_x, gallery_y)
    time.sleep(2)
    
    # Finder opens - navigate to image using Cmd+Shift+G
    print(f"📂 Selecting image: {os.path.basename(image_path)}")
    time.sleep(1)
    
    # Use Cmd+Shift+G to go to folder path
    select_file_script = f'''
    tell application "System Events"
        keystroke "g" using {{command down, shift down}}
        delay 1
        keystroke "{image_path}"
        delay 0.5
        keystroke return
        delay 1
        keystroke return
    end tell
    '''
    subprocess.run(["osascript", "-e", select_file_script], capture_output=True)
    time.sleep(3)
    
    # Add caption if the caption field is available
    if caption:
        print(f"💬 Adding caption: {caption}")
        # Caption field is usually at the bottom of the image preview
        # Click on caption area first
        caption_x, caption_y = 720, 800  # Adjust if needed - center bottom
        pyautogui.click(caption_x, caption_y)
        time.sleep(0.5)
        
        # Type caption
        p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        p.communicate(caption.encode('utf-8'))
        time.sleep(0.3)
        pyautogui.hotkey('command', 'v')
        time.sleep(1)
    
    # Click Send button
    print("   Clicking Send button...")
    send_x, send_y = 1402, 874
    pyautogui.click(send_x, send_y)
    time.sleep(1)
    
    # Update image index
    config["current_image_index"] = config.get("current_image_index", 0) + 1
    save_config(config)
    
    print("\n✅ Image status posted!")

def set_status(caption=None, with_image=False):
    """Set WhatsApp status (text or image)."""
    if with_image:
        set_image_status(caption=caption)
    else:
        set_text_status(caption=caption)

def list_images():
    """List all images available for status."""
    images = get_images()
    print("\n📷 Available Images in status_images/")
    print("="*50)
    if not images:
        print("   No images found!")
        print(f"   Add images to: {IMAGES_DIR}")
    else:
        for i, img in enumerate(images):
            filename = os.path.basename(img)
            print(f"   {i+1}. {filename}")
    print()

def setup():
    """Find correct click positions."""
    print("\n🔧 SETUP MODE - Find Click Positions")
    print("="*50)
    
    open_whatsapp()
    
    print("\nMove mouse to see coordinates. Press Ctrl+C to stop.\n")
    print("Positions to find:")
    print("1. STATUS icon (circle in left sidebar)")
    print("2. PENCIL icon (text status)")
    print("3. CAMERA icon (image status)")
    print("4. SEND button")
    print("5. CAPTION field (bottom of image preview)\n")
    
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\rMouse position: ({x}, {y})          ", end="", flush=True)
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\n\n📝 Update positions in the code if needed.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="WhatsApp Status Automation")
    parser.add_argument("--run", "-r", action="store_true", help="Post text status")
    parser.add_argument("--image", "-i", action="store_true", help="Post image status")
    parser.add_argument("--caption", "-c", type=str, help="Custom caption")
    parser.add_argument("--setup", action="store_true", help="Setup mode")
    parser.add_argument("--list", "-l", action="store_true", help="List available images")
    
    args = parser.parse_args()
    
    if args.setup:
        setup()
    elif args.list:
        list_images()
    elif args.image:
        set_image_status(caption=args.caption)
    elif args.run or args.caption:
        set_text_status(caption=args.caption)
    else:
        parser.print_help()
        print("\n" + "="*50)
        print("💡 USAGE:")
        print("="*50)
        print("  ./run.sh --run              # Post text status")
        print("  ./run.sh --image            # Post image status")
        print("  ./run.sh --image -c 'Hi!'   # Image with custom caption")
        print("  ./run.sh --list             # List available images")
        print("  ./run.sh --setup            # Find click positions")
        print(f"\n📁 Put images in: {IMAGES_DIR}")

if __name__ == "__main__":
    main()
