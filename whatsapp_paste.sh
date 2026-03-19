#!/bin/bash
# WhatsApp Photo Paste - Stream Deck Script
# Pastes all photos from folder to WhatsApp as IMAGE DATA

PHOTOS_FOLDER="$HOME/Desktop/photos_to_paste"

# Check folder
if [ ! -d "$PHOTOS_FOLDER" ]; then
    osascript -e 'display notification "Folder not found!" with title "Error"'
    exit 1
fi

# Get image count
COUNT=$(ls -1 "$PHOTOS_FOLDER"/*.{jpg,jpeg,png,gif,JPG,JPEG,PNG,GIF} 2>/dev/null | wc -l | tr -d ' ')

if [ "$COUNT" -eq 0 ]; then
    osascript -e 'display notification "No images found" with title "Paste Photos"'
    exit 0
fi

osascript -e "display notification \"Pasting $COUNT photos...\" with title \"WhatsApp Paste\""

# Run the AppleScript that does the actual work
osascript <<'APPLESCRIPT'
use framework "Foundation"
use framework "AppKit"
use scripting additions

set photosFolder to (POSIX path of (path to desktop)) & "photos_to_paste/"

-- Get files
set imageFiles to {}
tell application "System Events"
    set allFiles to name of every file of folder photosFolder
    repeat with fileName in allFiles
        set lowerName to do shell script "echo " & quoted form of (fileName as text) & " | tr '[:upper:]' '[:lower:]'"
        if lowerName ends with ".jpg" or lowerName ends with ".jpeg" or lowerName ends with ".png" or lowerName ends with ".gif" or lowerName ends with ".heic" then
            set end of imageFiles to fileName as text
        end if
    end repeat
end tell

if (count of imageFiles) = 0 then
    return
end if

delay 0.3

repeat with fileName in imageFiles
    set imagePath to photosFolder & fileName
    
    -- Copy as image DATA
    set imageURL to current application's NSURL's fileURLWithPath:imagePath
    set theImage to current application's NSImage's alloc()'s initWithContentsOfURL:imageURL
    
    if theImage is not missing value then
        set pb to current application's NSPasteboard's generalPasteboard()
        pb's clearContents()
        pb's writeObjects:{theImage}
        
        tell application "System Events"
            keystroke "v" using command down
        end tell
        
        delay 0.2
        
        tell application "System Events"
            keystroke return
        end tell
        
        delay 0.4
    end if
end repeat

display notification "Done!" with title "WhatsApp Paste"
APPLESCRIPT

echo "Done!"
