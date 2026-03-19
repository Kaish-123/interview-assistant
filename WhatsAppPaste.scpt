-- WhatsApp Photo Paste Script
-- Copies each image as IMAGE DATA and pastes to WhatsApp
-- For Stream Deck

use framework "Foundation"
use framework "AppKit"
use scripting additions

-- Configuration
set photosFolder to (POSIX path of (path to desktop)) & "photos_to_paste/"
set imageExtensions to {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "heic"}

-- Get image files
set imageFiles to {}
try
	tell application "System Events"
		set allFiles to name of every file of folder photosFolder
		repeat with fileName in allFiles
			set theExt to text ((offset of "." in fileName) + 1) thru -1 of fileName
			if imageExtensions contains theExt then
				set end of imageFiles to fileName as text
			end if
		end repeat
	end tell
on error errMsg
	display notification errMsg with title "Error"
	return
end try

if (count of imageFiles) = 0 then
	display notification "No images found in folder" with title "Paste Photos"
	return
end if

display notification "Pasting " & (count of imageFiles) & " photos..." with title "WhatsApp Paste"

-- Small delay to focus
delay 0.3

-- Paste each image
repeat with fileName in imageFiles
	set imagePath to photosFolder & fileName
	
	-- Copy image DATA to clipboard using Cocoa
	set imageURL to current application's NSURL's fileURLWithPath:imagePath
	set theImage to current application's NSImage's alloc()'s initWithContentsOfURL:imageURL
	
	if theImage is not missing value then
		set pb to current application's NSPasteboard's generalPasteboard()
		pb's clearContents()
		pb's writeObjects:{theImage}
		
		-- Paste
		tell application "System Events"
			keystroke "v" using command down
		end tell
		
		delay 0.2
		
		-- Press Enter to send
		tell application "System Events"
			keystroke return
		end tell
		
		delay 0.4
	end if
end repeat

display notification "Pasted " & (count of imageFiles) & " photos!" with title "Done!"
