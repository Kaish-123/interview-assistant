#!/usr/bin/env python3
"""
Import contacts from a vCard (.vcf) file into contacts.csv.
Use this if Mac Contacts sync doesn't work.

Export from Mac: Open Contacts app → File → Export → Export vCard…
Then run: python3 import_vcard.py ~/Desktop/contacts.vcf
"""

import csv
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONTACTS_CSV = BASE_DIR / "contacts.csv"


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if phone.strip().startswith("+"):
        return "+" + digits
    return digits


def _parse_vcard_block(block: str) -> list[dict]:
    """Parse one VCARD block; return list of {name, phone, keywords} (one per TEL)."""
    lines = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith(" ") and lines:
            lines[-1] = lines[-1] + line.strip()
        elif line:
            lines.append(line)

    name = ""
    phones = []
    note = ""

    for line in lines:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.split(";")[0].strip().upper()
        value = value.strip()
        if key == "FN":
            name = value
        elif key == "TEL":
            value = re.sub(r"\s+", "", value)
            if len(re.sub(r"\D", "", value)) >= 8:
                phones.append(value)
        elif key == "NOTE":
            note = value.replace("\n", " ").strip()

    if not name:
        name = "Unknown"
    keywords = [k.strip() for k in re.split(r"[,;]", note) if k.strip()]
    result = []
    seen = set()
    for ph in phones:
        norm = _normalize_phone(ph)
        if norm in seen:
            continue
        seen.add(norm)
        result.append({"name": name, "phone": norm, "keywords": ",".join(keywords)})
    return result


def import_vcard(vcf_path: Path) -> int:
    """Read .vcf file and write contacts.csv. Returns number of contacts."""
    text = vcf_path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\bBEGIN:VCARD\b", text, flags=re.IGNORECASE)
    all_rows = []
    seen_phones = set()
    for block in blocks:
        if "END:VCARD" not in block.upper():
            continue
        for row in _parse_vcard_block(block):
            if row["phone"] in seen_phones:
                continue
            seen_phones.add(row["phone"])
            all_rows.append(row)

    with open(CONTACTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "phone", "keywords"])
        writer.writeheader()
        writer.writerows(all_rows)
    return len(all_rows)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 import_vcard.py <path-to-contacts.vcf>", file=sys.stderr)
        print("Export from Mac Contacts: File → Export → Export vCard…", file=sys.stderr)
        return 1
    vcf_path = Path(sys.argv[1]).expanduser().resolve()
    if not vcf_path.exists():
        print(f"File not found: {vcf_path}", file=sys.stderr)
        print("Use the path to your real .vcf file. Example: ./run.sh import-vcard ~/Desktop/contacts.vcf", file=sys.stderr)
        print("Export from Contacts: File → Export → Export vCard… then use that file path.", file=sys.stderr)
        return 1
    count = import_vcard(vcf_path)
    print(f"Imported {count} contacts to {CONTACTS_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
