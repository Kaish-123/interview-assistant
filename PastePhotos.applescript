-- PastePhotos.applescript
-- Quick Photo Paste for WhatsApp/Any Chat App
-- For Stream Deck Integration

-- CONFIGURATION: Set your photos folder path here
set photosFolder to (POSIX path of (path to desktop)) & "photos_to_paste/"

-- Get all image files from folder
set imageExtensions to {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "heic", "JPG", "JPEG", "PNG", "GIF", "WEBP", "BMP", "TIFF", "HEIC"}

try
	-- Get file list using shell command (faster)
	set shellCmd to "ls -1 \"" & photosFolder & "\" 2>/dev/null | grep -iE '\\.(jpg|jpeg|png|gif|webp|bmp|tiff|heic)$'"
	set fileNames to paragraphs of (do shell script shellCmd)
	
	if (count of fileNames) = 0 then
		display notification "No images found in folder" with title "Paste Photos"
		return
	end if
	
	-- Build list of POSIX files
	set fileList to {}
	repeat with fileName in fileNames
		set end of fileList to (POSIX file (photosFolder & fileName))
	end repeat
	
	-- Copy files to clipboard
	set the clipboard to fileList
	
	-- Small delay then paste
	delay 0.1
	
	-- Paste using Cmd+V
	tell application "System Events"
		keystroke "v" using command down
	end tell
	
	display notification "Pasted " & (count of fileNames) & " photos!" with title "Paste Photos"
	
on error errMsg
	display notification errMsg with title "Paste Photos Error"
end try
