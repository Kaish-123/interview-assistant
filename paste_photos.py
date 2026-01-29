#!/usr/bin/env python3
"""
Paste Photos Script
Reads photos from Desktop folder and pastes them using automation
"""

import os
import glob
import time
import subprocess
from pathlib import Path
from typing import List

try:
    import pyautogui
except ImportError:
    # Try to find and use venv if available
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_path = os.path.join(script_dir, "venv")
    
    if os.path.exists(venv_path):
        print("⚠️  pyautogui not found in current environment.")
        print(f"💡 Try running with venv: source {venv_path}/bin/activate && python3 {__file__}")
    else:
        print("❌ pyautogui not installed. Run: pip install pyautogui")
    exit(1)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05  # Reduced from 0.5 to 0.05 for faster execution

# Default folder - can be Desktop or photos_to_paste subfolder
DESKTOP_PATH = os.path.expanduser("~/Desktop")
PHOTOS_FOLDER = os.path.join(DESKTOP_PATH, "photos_to_paste")


def get_photos_from_folder(folder_path: str = None) -> List[str]:
    """
    Get all image files from specified folder.
    If folder_path is None, checks both photos_to_paste and Desktop.
    """
    if folder_path is None:
        # Try photos_to_paste first, then Desktop
        if os.path.exists(PHOTOS_FOLDER):
            folder_path = PHOTOS_FOLDER
        else:
            folder_path = DESKTOP_PATH
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return []
    
    # Supported image extensions
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', 
                  '*.JPG', '*.JPEG', '*.PNG', '*.GIF', '*.WEBP']
    
    photos = []
    for ext in extensions:
        photos.extend(glob.glob(os.path.join(folder_path, ext)))
    
    # Sort by filename
    photos = sorted(set(photos))
    print(f"📷 Found {len(photos)} photos in {folder_path}")
    return photos


def paste_photos_via_clipboard(photo_paths: List[str], delay: float = 0.05):
    """
    Paste photos by copying each to clipboard and pasting.
    This method works well for applications that accept clipboard images.
    Optimized for speed - minimal delays. Ultra-fast mode.
    """
    if not photo_paths:
        print("❌ No photos to paste")
        return
    
    print(f"📋 Pasting {len(photo_paths)} photos via clipboard (ULTRA-FAST MODE)...")
    if delay <= 0.05:
        print("⚡ ULTRA-FAST: Starting immediately - make sure target app is focused!")
        time.sleep(0.2)  # Minimal wait for user to focus
    else:
        print("⏳ Waiting 0.5 seconds - please focus on the target application NOW...")
        time.sleep(0.5)
    
    # Pre-build all AppleScript commands for faster execution
    scripts = []
    for photo_path in photo_paths:
        script = f'''
        set imageFile to POSIX file "{photo_path}"
        try
            set the clipboard to (read file imageFile as «class PNGf»)
        on error
            try
                set the clipboard to (read file imageFile as «class JPEG»)
            on error
                set the clipboard to (read file imageFile)
            end try
        end try
        '''
        scripts.append(script)
    
    print(f"🚀 Starting rapid paste of {len(photo_paths)} photos...")
    start_time = time.time()
    
    for i, (photo_path, script) in enumerate(zip(photo_paths, scripts), 1):
        # Copy file to clipboard using AppleScript
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode != 0:
            if i <= 5 or i % 20 == 0:  # Only print errors for first 5 or every 20th
                print(f"   ⚠️  Warning: Could not copy {os.path.basename(photo_path)}")
            continue
        
        # Minimal delay - just enough for clipboard to update
        # No delay needed if ultra-fast mode
        if delay > 0.02:
            time.sleep(0.01)  # Very minimal delay only if not ultra-fast
        
        # Paste using Cmd+V
        pyautogui.hotkey('command', 'v')
        time.sleep(delay)  # Ultra-fast: 0.02-0.05 seconds
    
    elapsed = time.time() - start_time
    print(f"✅ Completed! Pasted {len(photo_paths)} photos in {elapsed:.2f} seconds ({len(photo_paths)/elapsed:.1f} photos/sec)")


def paste_photos_via_finder(photo_paths: List[str], delay: float = 0.1):
    """
    Paste photos by opening Finder, selecting files, and copying them.
    Then pastes in the active application.
    Optimized for speed.
    """
    if not photo_paths:
        print("❌ No photos to paste")
        return
    
    print(f"📁 Pasting {len(photo_paths)} photos via Finder (FAST MODE)...")
    print("⏳ Waiting 1 second - please focus on the target application...")
    time.sleep(1)  # Reduced from 3 to 1 second
    
    folder_path = os.path.dirname(photo_paths[0])
    
    # Open Finder to the folder
    script_open = f'''
    tell application "Finder"
        activate
        open folder POSIX file "{folder_path}"
        delay 1
    end tell
    '''
    subprocess.run(["osascript", "-e", script_open], capture_output=True)
    time.sleep(0.5)  # Reduced from 2 to 0.5 seconds
    
    # Select all photos (if all photos should be selected)
    # Or select specific files
    if len(photo_paths) == len(get_photos_from_folder(folder_path)):
        # Select all
        pyautogui.hotkey('command', 'a')
        time.sleep(0.2)  # Reduced from 1 to 0.2 seconds
    else:
        # Select specific files
        for photo_path in photo_paths:
            filename = os.path.basename(photo_path)
            pyautogui.hotkey('command', 'f')  # Find
            time.sleep(0.1)  # Reduced from 0.5 to 0.1
            pyautogui.typewrite(filename, interval=0.01)  # Faster typing
            time.sleep(0.1)  # Reduced from 0.5 to 0.1
            pyautogui.press('return')
            time.sleep(0.1)  # Reduced from 0.5 to 0.1
            pyautogui.hotkey('command', 'a')  # Select found file
            time.sleep(0.1)  # Reduced from 0.5 to 0.1
    
    # Copy selected files
    pyautogui.hotkey('command', 'c')
    time.sleep(0.2)  # Reduced from 1 to 0.2 seconds
    
    # Switch back to previous application (assuming it's the target)
    pyautogui.hotkey('command', 'tab')
    time.sleep(0.2)  # Reduced from 1 to 0.2 seconds
    
    # Paste
    pyautogui.hotkey('command', 'v')
    time.sleep(delay)


def paste_photos_via_drag_drop(photo_paths: List[str], delay: float = 0.1):
    """
    Alternative method using drag and drop simulation.
    Note: This is more complex and may require window positioning.
    Optimized for speed.
    """
    if not photo_paths:
        print("❌ No photos to paste")
        return
    
    print(f"🖱️  Pasting {len(photo_paths)} photos via drag & drop (FAST MODE)...")
    print("⚠️  This method requires manual positioning")
    print("⏳ Waiting 1 second - please focus on the target application...")
    time.sleep(1)  # Reduced from 3 to 1 second
    
    # This would require more complex automation
    # For now, use clipboard method as fallback
    paste_photos_via_clipboard(photo_paths, delay)


def main():
    """Main function to paste photos."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Paste photos from Desktop folder")
    parser.add_argument(
        "--folder",
        type=str,
        default=None,
        help="Path to folder containing photos (default: ~/Desktop/photos_to_paste or ~/Desktop)"
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["clipboard", "finder", "drag"],
        default="clipboard",
        help="Method to use for pasting (default: clipboard)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.03,
        help="Delay between pasting each photo in seconds (default: 0.03 for maximum speed)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of photos to paste (default: all)"
    )
    parser.add_argument(
        "--ultra-fast",
        action="store_true",
        help="Ultra-fast mode: minimal delays (0.02s between photos)"
    )
    
    args = parser.parse_args()
    
    # Get photos
    photos = get_photos_from_folder(args.folder)
    
    if not photos:
        print("❌ No photos found!")
        return
    
    # Limit if specified and valid
    if args.limit is not None:
        if args.limit <= 0:
            print("❌ Limit must be a positive number!")
            return
        if args.limit > len(photos):
            print(f"⚠️  Limit ({args.limit}) is greater than available photos ({len(photos)}). Using all photos.")
        else:
            photos = photos[:args.limit]
            print(f"📊 Limiting to first {args.limit} photos")
    
    # Apply ultra-fast mode if requested
    if args.ultra_fast:
        args.delay = 0.02
        print("⚡ ULTRA-FAST MODE enabled (0.02s delay)")
    
    # Paste using selected method
    if args.method == "clipboard":
        paste_photos_via_clipboard(photos, args.delay)
    elif args.method == "finder":
        paste_photos_via_finder(photos, args.delay)
    elif args.method == "drag":
        paste_photos_via_drag_drop(photos, args.delay)
    
    print("✅ Done!")


if __name__ == "__main__":
    main()
