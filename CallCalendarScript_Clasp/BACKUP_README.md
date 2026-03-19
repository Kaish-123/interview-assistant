# Backup your Apps Script project

## One-time setup (if you haven’t already)

1. **Install clasp**  
   `npm install -g @google/clasp`

2. **Log in**  
   From this folder run:  
   `./1_login.sh`  
   Open the URL in your browser and authorize.

3. **Clone your project (if this folder isn’t linked yet)**  
   Put your Script ID in `script_id.txt` or pass it:  
   `./2_clone.sh YOUR_SCRIPT_ID`

## Create a backup

From this folder run:

```bash
./backup_appscript.sh
```

This will:

1. **Pull** the latest script files from your Google Apps Script project (`clasp pull`).
2. **Copy** all `.gs` files and `appsscript.json` into a new folder:  
   `CallCalendarScript_Backup_YYYYMMDD_HHMM`  
   (e.g. `CallCalendarScript_Backup_20260210_1430`).

So you get a timestamped snapshot of your Apps Script project on disk. Run it whenever you want a backup (e.g. before big changes).

## Make the script executable (once)

```bash
chmod +x backup_appscript.sh
```
