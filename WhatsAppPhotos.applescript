-- WhatsApp Photo Paste Script
-- Opens Finder with photos selected, ready to drag to WhatsApp

set photosFolder to (POSIX path of (path to desktop)) & "photos_to_paste"

-- Open Finder and select all photos
tell application "Finder"
    activate
    
    try
        set theFolder to POSIX file photosFolder as alias
        open theFolder
        
        -- Wait for window to open
        delay 0.3
        
        -- Select all files
        tell application "System Events"
            keystroke "a" using command down
        end tell
        
        display notification "Photos selected! Drag them to WhatsApp" with title "Ready to Drag"
        
    on error errMsg
        display notification errMsg with title "Error"
    end try
end tell
