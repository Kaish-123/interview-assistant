-- WhatsApp Paste ALL Photos at Once
-- Copies ALL images to clipboard and pastes in ONE go

use framework "Foundation"
use framework "AppKit"
use scripting additions

set photosFolder to (POSIX path of (path to desktop)) & "photos_to_paste/"

-- Get all image files
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
	display notification "No images found" with title "Paste Photos"
	return
end if

display notification "Loading " & (count of imageFiles) & " photos..." with title "WhatsApp Paste"

-- Load ALL images into an array
set imageArray to current application's NSMutableArray's new()

repeat with fileName in imageFiles
	set imagePath to photosFolder & fileName
	set imageURL to current application's NSURL's fileURLWithPath:imagePath
	set theImage to current application's NSImage's alloc()'s initWithContentsOfURL:imageURL
	if theImage is not missing value then
		imageArray's addObject:theImage
	end if
end repeat

-- Copy ALL images to clipboard at once
set pb to current application's NSPasteboard's generalPasteboard()
pb's clearContents()
pb's writeObjects:imageArray

-- Paste all at once
tell application "System Events"
	keystroke "v" using command down
end tell

delay 0.5

-- Press Enter to send
tell application "System Events"
	keystroke return
end tell

display notification "Pasted " & (count of imageFiles) & " photos!" with title "Done!"
