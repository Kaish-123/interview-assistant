#!/usr/bin/env python3
"""
Paste Photos to WhatsApp - Works by pasting image DATA (not files)
WhatsApp accepts image data paste, not file paste
"""

import os
import subprocess
import time
from pathlib import Path

# ===========================================
# CONFIGURATION
# ===========================================
PHOTOS_FOLDER = os.path.expanduser("~/Desktop/photos_to_paste")
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.heic'}

def notify(title, message):
    subprocess.run([
        'osascript', '-e',
        f'display notification "{message}" with title "{title}"'
    ], capture_output=True)

def copy_image_data_to_clipboard(image_path):
    """Copy image as PNG data to clipboard (WhatsApp accepts this)"""
    script = f'''
    use framework "Foundation"
    use framework "AppKit"
    
    set imagePath to "{image_path}"
    set imageURL to current application's NSURL's fileURLWithPath:imagePath
    set theImage to current application's NSImage's alloc()'s initWithContentsOfURL:imageURL
    
    if theImage is not missing value then
        set pb to current application's NSPasteboard's generalPasteboard()
        pb's clearContents()
        pb's writeObjects:{{theImage}}
        return "success"
    else
        return "failed"
    end if
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return "success" in result.stdout

def paste():
    """Press Cmd+V"""
    subprocess.run([
        'osascript', '-e',
        'tell application "System Events" to keystroke "v" using command down'
    ], capture_output=True)

def press_enter():
    """Press Enter to send"""
    subprocess.run([
        'osascript', '-e',
        'tell application "System Events" to keystroke return'
    ], capture_output=True)

def main():
    if not os.path.isdir(PHOTOS_FOLDER):
        notify("Error", f"Folder not found: {PHOTOS_FOLDER}")
        return
    
    folder = Path(PHOTOS_FOLDER)
    image_files = sorted([
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ])
    
    if not image_files:
        notify("Paste Photos", "No images found")
        return
    
    notify("Paste Photos", f"Pasting {len(image_files)} photos to WhatsApp...")
    
    # Give user 2 seconds to focus WhatsApp
    time.sleep(2)
    
    for i, img in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] Pasting: {img.name}")
        
        if copy_image_data_to_clipboard(str(img)):
            paste()
            time.sleep(0.5)  # Wait for paste
            press_enter()     # Send the image
            time.sleep(1)     # Wait before next
        else:
            print(f"  Failed to copy: {img.name}")
    
    notify("Done!", f"Pasted {len(image_files)} photos!")

if __name__ == "__main__":
    main()
