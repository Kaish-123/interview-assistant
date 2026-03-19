#!/usr/bin/env python3
"""
Quick Photo Paste for WhatsApp (Stream Deck)
Attaches all photos from a folder to WhatsApp instantly
"""

import os
import subprocess
import time
from pathlib import Path

# ===========================================
# CONFIGURATION - Change this to your photos folder
# ===========================================
PHOTOS_FOLDER = os.path.expanduser("~/Desktop/photos_to_paste")

# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.heic'}

# ===========================================

def notify(title, message):
    """Show macOS notification"""
    subprocess.run([
        'osascript', '-e',
        f'display notification "{message}" with title "{title}"'
    ], capture_output=True)

def copy_files_to_clipboard(file_paths):
    """Copy multiple files to clipboard using AppleScript"""
    if not file_paths:
        return False
    
    # Build the file list for AppleScript
    file_list = ', '.join([f'POSIX file "{p}"' for p in file_paths])
    
    script = f'''
    set theFiles to {{{file_list}}}
    set the clipboard to theFiles
    '''
    
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.returncode == 0

def paste():
    """Press Cmd+V to paste"""
    subprocess.run([
        'osascript', '-e',
        'tell application "System Events" to keystroke "v" using command down'
    ], capture_output=True)

def main():
    # Check if folder exists
    if not os.path.isdir(PHOTOS_FOLDER):
        notify("Error", f"Folder not found: {PHOTOS_FOLDER}")
        print(f"Error: Folder not found: {PHOTOS_FOLDER}")
        return
    
    # Get all image files
    folder = Path(PHOTOS_FOLDER)
    image_files = sorted([
        str(f) for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ])
    
    if not image_files:
        notify("Paste Photos", "No images found in folder")
        print("No images found")
        return
    
    print(f"Found {len(image_files)} photos")
    notify("Paste Photos", f"Pasting {len(image_files)} photos...")
    
    # Copy all files to clipboard at once
    if copy_files_to_clipboard(image_files):
        print("Files copied to clipboard")
        # Paste immediately
        paste()
        print("Paste command sent!")
        notify("Done", f"Pasted {len(image_files)} photos!")
    else:
        notify("Error", "Failed to copy files")
        print("Failed to copy files to clipboard")

if __name__ == "__main__":
    main()
