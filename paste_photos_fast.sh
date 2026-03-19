#!/bin/bash
# Quick Photo Paste - Works with WhatsApp, ChatGPT, any chat app
# For Stream Deck

PHOTOS_FOLDER="$HOME/Desktop/photos_to_paste"

# Check folder exists
if [ ! -d "$PHOTOS_FOLDER" ]; then
    osascript -e 'display notification "Folder not found!" with title "Paste Photos"'
    exit 1
fi

# Get all image files
cd "$PHOTOS_FOLDER"
FILES=$(ls -1 *.{jpg,jpeg,png,gif,webp,bmp,tiff,heic,JPG,JPEG,PNG,GIF,WEBP,BMP,TIFF,HEIC} 2>/dev/null)

if [ -z "$FILES" ]; then
    osascript -e 'display notification "No images found" with title "Paste Photos"'
    exit 0
fi

COUNT=$(echo "$FILES" | wc -l | tr -d ' ')

# Build AppleScript to copy files
SCRIPT="set fileList to {"
FIRST=true
while IFS= read -r file; do
    if [ -n "$file" ]; then
        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            SCRIPT+=", "
        fi
        SCRIPT+="POSIX file \"$PHOTOS_FOLDER/$file\""
    fi
done <<< "$FILES"
SCRIPT+="}"
SCRIPT+="
set the clipboard to fileList"

# Copy to clipboard
osascript -e "$SCRIPT"

# Paste immediately
osascript -e 'tell application "System Events" to keystroke "v" using command down'

# Notify
osascript -e "display notification \"Pasted $COUNT photos!\" with title \"Done\""
