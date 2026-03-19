#!/usr/bin/env python3
"""
Sync contacts from macOS Contacts app into contacts.csv.
- Reads every person's name, phone number(s), and Notes
- Uses Notes field as keywords (comma/semicolon separated). Empty notes = match by name only
- One row per phone number (same name and keywords for each)
- Preserves any existing contacts.csv rows that have phone numbers not in Contacts (optional merge)
"""

import csv
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONTACTS_CSV = BASE_DIR / "contacts.csv"
# Tab-separated; notes may contain newlines (we normalize in Python)
APPLESCRIPT = r'''
tell application "Contacts"
    set out to ""
    set personList to every person
    repeat with i from 1 to (count of personList)
        set p to item i of personList
        set theName to (name of p) as text
        if theName is "" then set theName to "Unknown"
        set theNote to ""
        try
            set theNote to (note of p) as text
        end try
        try
            set phoneList to phones of p
            repeat with j from 1 to (count of phoneList)
                set ph to item j of phoneList
                set num to (value of ph) as text
                if num is not "" and (length of num) is greater than or equal to 8 then
                    set out to out & theName & (ASCII character 9) & num & (ASCII character 9) & theNote & (ASCII character 10)
                end if
            end repeat
        end try
    end repeat
    return out
end tell
'''

def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if phone.strip().startswith("+"):
        return "+" + digits
    return digits

def sync_from_mac(merge_with_existing: bool = True) -> int:
    """Sync Contacts app to contacts.csv. Returns number of contacts written."""
    try:
        result = subprocess.run(
            ["osascript", "-e", APPLESCRIPT],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        print("Mac Contacts sync timed out (large contact list or waiting for permission).", file=sys.stderr)
        print("  Use vCard export instead:", file=sys.stderr)
        print("  1. Open Contacts app → File → Export → Export vCard… → save (e.g. to Desktop)", file=sys.stderr)
        print("  2. Run: ./run.sh import-vcard ~/Desktop/contacts.vcf", file=sys.stderr)
        return 0
    if result.returncode != 0:
        print("Mac Contacts sync failed:", result.stderr or result.stdout, file=sys.stderr)
        print("  • Grant access: System Settings → Privacy & Security → Contacts → enable Terminal (or your IDE).", file=sys.stderr)
        print("  • Or export manually: Contacts app → File → Export → Export vCard… then run:", file=sys.stderr)
        print("    ./run.sh import-vcard ~/Desktop/contacts.vcf", file=sys.stderr)
        return 0

    lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    rows = []
    seen_phones = set()
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
        if phone_norm in seen_phones:
            continue
        seen_phones.add(phone_norm)
        # Use notes as keywords (comma/semicolon separated)
        keywords = [k.strip() for k in re.split(r"[,;]", notes) if k.strip()]
        rows.append({"name": name, "phone": phone_norm, "keywords": ",".join(keywords)})

    # If Mac returned no contacts and we're merging, keep existing file (e.g. permission denied)
    if not rows and merge_with_existing and CONTACTS_CSV.exists():
        with open(CONTACTS_CSV, newline="", encoding="utf-8") as f:
            existing_count = len(list(csv.DictReader(f)))
        print("No contacts from Mac (grant Contacts access?). Leaving contacts.csv unchanged.", file=sys.stderr)
        return existing_count

    if merge_with_existing and CONTACTS_CSV.exists():
        existing_phones = {_normalize_phone(r["phone"]) for r in rows}
        with open(CONTACTS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p = _normalize_phone((row.get("phone") or "").strip())
                if p and p not in existing_phones:
                    rows.append({
                        "name": (row.get("name") or "").strip(),
                        "phone": p,
                        "keywords": (row.get("keywords") or "").strip(),
                    })
                    existing_phones.add(p)

    with open(CONTACTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "phone", "keywords"])
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main():
    merge_with_existing = "--replace" not in sys.argv
    count = sync_from_mac(merge_with_existing=merge_with_existing)
    print(f"Synced {count} contacts from Mac Contacts to {CONTACTS_CSV}")
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
