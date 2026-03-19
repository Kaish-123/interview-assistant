#!/bin/bash
# Opens Finder with photos selected - ready to drag to WhatsApp
# This is the MOST RELIABLE method for WhatsApp

PHOTOS_FOLDER="$HOME/Desktop/photos_to_paste"

# Check folder exists
if [ ! -d "$PHOTOS_FOLDER" ]; then
    osascript -e 'display notification "Folder not found!" with title "Error"'
    exit 1
fi

# Count photos
COUNT=$(ls -1 "$PHOTOS_FOLDER"/*.{jpg,jpeg,png,gif,JPG,JPEG,PNG,GIF} 2>/dev/null | wc -l | tr -d ' ')

if [ "$COUNT" -eq 0 ]; then
    osascript -e 'display notification "No photos found" with title "Error"'
    exit 1
fi

# Open Finder and select all photos
osascript <<'EOF'
tell application "Finder"
    activate
    set theFolder to POSIX file "/Users/mohammadkaishmanihar/Desktop/photos_to_paste" as alias
    open theFolder
    delay 0.5
end tell

tell application "System Events"
    keystroke "a" using command down
end tell

display notification "Photos selected! Now drag to WhatsApp" with title "Ready"
EOF

echo "Finder opened with $COUNT photos selected. Drag them to WhatsApp!"
