#!/usr/bin/env python3
"""
Build broadcast lists from contacts using keywords.
- Reads contacts from contacts.csv (name, phone, keywords)
- For each broadcast list definition in config.json, selects contacts that match ANY keyword
- Splits into multiple lists when contacts exceed max_contacts_per_list (e.g. 256 for WhatsApp)
- Writes built lists to broadcast_lists/ as JSON for sending
"""

import csv
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONTACTS_CSV = BASE_DIR / "contacts.csv"
CONFIG_FILE = BASE_DIR / "config.json"
OUTPUT_DIR = BASE_DIR / "broadcast_lists"


def load_contacts(csv_path: Path) -> list[dict]:
    """Load contacts from CSV. Columns: name, phone, keywords (comma-separated)."""
    contacts = []
    if not csv_path.exists():
        return contacts
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            phone = (row.get("phone") or "").strip()
            keywords_raw = (row.get("keywords") or "").strip()
            keywords = [k.strip().lower() for k in re.split(r"[,;]", keywords_raw) if k.strip()]
            if phone:
                contacts.append({
                    "name": name,
                    "phone": _normalize_phone(phone),
                    "keywords": keywords,
                })
    return contacts


def _normalize_phone(phone: str) -> str:
    """Keep digits and leading + for international format."""
    digits = re.sub(r"\D", "", phone)
    if phone.strip().startswith("+"):
        return "+" + digits
    return digits


def contact_matches_keywords(contact: dict, keywords: list[str]) -> bool:
    """True if contact's name or keywords contain any of the given keywords (case-insensitive)."""
    search_in = " ".join([contact.get("name", "").lower()] + contact.get("keywords", []))
    kw_lower = [k.strip().lower() for k in keywords if k.strip()]
    for k in kw_lower:
        if k in search_in:
            return True
    return False


def build_lists_for_definition(
    contacts: list[dict],
    definition: dict,
    max_per_list: int,
) -> list[dict]:
    """
    For one broadcast list definition (name + keywords), filter contacts and chunk into
    multiple lists if needed. Returns list of { "name": "ListName_1", "contacts": [...] }.
    """
    list_name = definition.get("name", "Unnamed")
    keywords = definition.get("keywords", [])
    if not keywords:
        return []

    matching = [c for c in contacts if contact_matches_keywords(c, keywords)]
    # Deduplicate by phone
    seen = set()
    unique = []
    for c in matching:
        p = c.get("phone", "")
        if p and p not in seen:
            seen.add(p)
            unique.append(c)

    result = []
    for i in range(0, len(unique), max_per_list):
        chunk = unique[i : i + max_per_list]
        suffix = f"_{len(result) + 1}" if len(unique) > max_per_list and result else ""
        result.append({
            "name": f"{list_name}{suffix}",
            "keywords": keywords,
            "contacts": chunk,
            "total_contacts": len(chunk),
        })
    return result


def main():
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    contacts = load_contacts(CONTACTS_CSV)
    if not contacts:
        # Remove old lists so we don't send to stale/sample data
        if OUTPUT_DIR.exists():
            for f in OUTPUT_DIR.iterdir():
                if f.suffix == ".json":
                    f.unlink(missing_ok=True)
        print("No contacts in contacts.csv.")
        print("  • Run ./run.sh sync  to load from Mac Contacts app")
        print("  • Or run ./run.sh import-vcard path/to/contacts.vcf  after exporting from Contacts (File → Export → vCard)")
        return 1
    max_per_list = config.get("max_contacts_per_list", 256)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_built = []
    for definition in config.get("broadcast_lists", []):
        lists = build_lists_for_definition(contacts, definition, max_per_list)
        for lst in lists:
            out_name = lst["name"].replace(" ", "_") + ".json"
            out_path = OUTPUT_DIR / out_name
            out_path.write_text(json.dumps(lst, indent=2, ensure_ascii=False), encoding="utf-8")
            all_built.append({"name": lst["name"], "path": str(out_path), "count": lst["total_contacts"]})

    # Write index of all built lists (for sender)
    index_path = OUTPUT_DIR / "_index.json"
    index = {
        "default_message_file": config.get("default_message_file", "message.txt"),
        "lists": all_built,
    }
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    print(f"Built {len(all_built)} broadcast list(s) from {len(contacts)} contacts.")
    for item in all_built:
        print(f"  - {item['name']}: {item['count']} contacts -> {item['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
