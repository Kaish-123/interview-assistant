#!/usr/bin/env python3
"""
Fully automated: export Mac Contacts to a file, then load into contacts.csv.
- AppleScript writes directly to a file (no huge stdout), so large contact lists work better.
- Then we read that file and fill contacts.csv, then optionally run build.
One command does everything: ./run.sh load-contacts
"""

import csv
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONTACTS_CSV = BASE_DIR / "contacts.csv"
EXPORT_FILE = BASE_DIR / "exported_contacts.txt"

# AppleScript: receives file path as argv, writes tab-separated lines (name, phone, note) to that file
APPLESCRIPT = r'''
on run argv
    set outPath to item 1 of argv
    set theFile to open for access file (POSIX file outPath) with write permission
    set fileContents to ""
    tell application "Contacts"
        set personList to every person
        repeat with i from 1 to (count of personList)
            set p to item i of personList
            set theName to (name of p) as text
            if theName is "" then set theName to "Unknown"
            set theNote to ""
            try
                set noteVal to note of p
                if noteVal is not missing value then
                    set theNote to noteVal as text
                    set theNote to my replaceText(theNote, (ASCII character 10), " ")
                    set theNote to my replaceText(theNote, (ASCII character 13), " ")
                    set theNote to my replaceText(theNote, (ASCII character 9), " ")
                end if
            end try
            try
                set phoneList to phones of p
                set phoneCount to count of phoneList
                repeat with j from 1 to phoneCount
                    set ph to item j of phoneList
                    set numStr to ""
                    try
                        set numVal to value of ph
                        if numVal is not missing value then set numStr to numVal as text
                    end try
                    if (length of numStr) is greater than or equal to 8 then
                        set fileContents to fileContents & theName & (ASCII character 9) & numStr & (ASCII character 9) & theNote & (ASCII character 10)
                    end if
                end repeat
            end try
        end repeat
    end tell
    write fileContents to theFile
    close access theFile
    return "ok"
end run

on replaceText(txt, find, rep)
    if txt is missing value or txt is "" then return ""
    set AppleScript's text item delimiters to find
    set itemList to text items of txt
    set AppleScript's text item delimiters to rep
    set out to itemList as text
    set AppleScript's text item delimiters to ""
    return out
end replaceText
'''


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if phone.strip().startswith("+"):
        return "+" + digits
    return digits


def export_and_load(build_after: bool = True) -> int:
    """Export Contacts to file, load into contacts.csv. Returns contact count."""
    export_path = EXPORT_FILE.resolve()
    try:
        result = subprocess.run(
            ["osascript", "-e", APPLESCRIPT, str(export_path)],
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        print("Export timed out. Grant Contacts access: System Settings → Privacy & Security → Contacts → enable Terminal.", file=sys.stderr)
        print("Then run again, or use: ./run.sh import-vcard ~/Desktop/contacts.vcf (after manual export).", file=sys.stderr)
        return 0
    if result.returncode != 0:
        print("Export failed:", result.stderr or result.stdout, file=sys.stderr)
        print("Grant Contacts access: System Settings → Privacy & Security → Contacts.", file=sys.stderr)
        return 0

    if not export_path.exists() or export_path.stat().st_size == 0:
        print("No contacts exported (empty file). Check Contacts access.", file=sys.stderr)
        return 0

    # Parse exported file → contacts.csv
    text = export_path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    rows = []
    seen = set()
    for line in lines:
        parts = line.split("\t", 2)
        if len(parts) < 2:
            continue
        name = (parts[0] or "").strip()
        phone = (parts[1] or "").strip()
        notes = (parts[2] if len(parts) > 2 else "").strip()
        notes = re.sub(r"[\r\n\t]+", " ", notes).strip()
        if not phone or len(re.sub(r"\D", "", phone)) < 8:
            continue
        phone_norm = _normalize_phone(phone)
        if phone_norm in seen:
            continue
        seen.add(phone_norm)
        keywords = [k.strip() for k in re.split(r"[,;]", notes) if k.strip()]
        rows.append({"name": name, "phone": phone_norm, "keywords": ",".join(keywords)})

    with open(CONTACTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "phone", "keywords"])
        writer.writeheader()
        writer.writerows(rows)

    # Optionally run build
    if build_after and rows:
        import subprocess as sp
        r = sp.run([sys.executable, str(BASE_DIR / "build_broadcast_lists.py")], cwd=str(BASE_DIR))
        if r.returncode != 0:
            pass  # build prints its own message

    return len(rows)


def main():
    build = "--no-build" not in sys.argv
    count = export_and_load(build_after=build)
    if count > 0:
        print(f"Exported and loaded {count} contacts into contacts.csv.")
        if build:
            print("Broadcast lists rebuilt. Run ./run.sh send-dry-run then ./run.sh send")
    else:
        print("No contacts loaded. See messages above.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
