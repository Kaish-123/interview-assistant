#!/usr/bin/env python3
"""
Contact Fetcher - Reads contacts from macOS Contacts app
Filters contacts by suffix keywords (client, proxy, interview, etc.)
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

# macOS Contacts Framework via pyobjc
try:
    import Contacts
except ImportError:
    print("⚠️  Contacts framework not available. Install pyobjc-framework-Contacts")
    print("    pip install pyobjc-framework-Contacts")
    Contacts = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "marketing_config.json")
DB_PATH = os.path.join(SCRIPT_DIR, "contacts_cache.db")


def load_config() -> dict:
    """Load configuration from JSON file."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "contact_suffixes": ["client", "proxy", "interview"],
            "excluded_contacts": []
        }


def save_config(config: dict):
    """Save configuration to JSON file."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def init_database():
    """Initialize SQLite database for contact caching and tracking."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Contacts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            suffix_type TEXT,
            is_excluded INTEGER DEFAULT 0,
            last_messaged TEXT,
            message_count INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Message history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            sent_at TEXT,
            message_preview TEXT,
            images_count INTEGER,
            status TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    ''')
    
    conn.commit()
    conn.close()


def request_contacts_access() -> bool:
    """Request access to Contacts on macOS."""
    if Contacts is None:
        return False
    
    store = Contacts.CNContactStore.alloc().init()
    
    # Check current authorization status
    status = Contacts.CNContactStore.authorizationStatusForEntityType_(
        Contacts.CNEntityTypeContacts
    )
    
    if status == Contacts.CNAuthorizationStatusAuthorized:
        return True
    elif status == Contacts.CNAuthorizationStatusNotDetermined:
        # Request access
        granted = [False]
        error = [None]
        
        def completion(success, err):
            granted[0] = success
            error[0] = err
        
        store.requestAccessForEntityType_completionHandler_(
            Contacts.CNEntityTypeContacts,
            completion
        )
        
        # Wait for response (blocking)
        import time
        time.sleep(1)
        
        return granted[0]
    else:
        print("❌ Contacts access denied. Please grant access in System Preferences.")
        print("   → System Preferences → Security & Privacy → Privacy → Contacts")
        return False


def fetch_contacts_from_macos(suffixes: List[str] = None) -> List[Dict]:
    """
    Fetch contacts from macOS Contacts app that match the given suffixes.
    
    Args:
        suffixes: List of keywords to match in contact names (e.g., ['client', 'proxy'])
    
    Returns:
        List of contact dictionaries with name, phone, and suffix_type
    """
    if Contacts is None:
        print("❌ Contacts framework not available")
        return []
    
    config = load_config()
    suffixes = suffixes or config.get("contact_suffixes", ["client", "proxy", "interview"])
    suffixes = [s.lower() for s in suffixes]
    
    store = Contacts.CNContactStore.alloc().init()
    
    # Keys to fetch
    keys_to_fetch = [
        Contacts.CNContactGivenNameKey,
        Contacts.CNContactFamilyNameKey,
        Contacts.CNContactNicknameKey,
        Contacts.CNContactPhoneNumbersKey,
        Contacts.CNContactIdentifierKey,
    ]
    
    # Fetch all contacts
    request = Contacts.CNContactFetchRequest.alloc().initWithKeysToFetch_(keys_to_fetch)
    
    contacts = []
    error = None
    
    def enumerate_contacts(contact, stop):
        # Get full name
        given_name = contact.givenName() or ""
        family_name = contact.familyName() or ""
        nickname = contact.nickname() or ""
        
        full_name = f"{given_name} {family_name}".strip()
        if not full_name:
            full_name = nickname
        
        # Check if name contains any of the suffixes
        name_lower = full_name.lower()
        matched_suffix = None
        
        for suffix in suffixes:
            if suffix in name_lower:
                matched_suffix = suffix
                break
        
        if matched_suffix:
            # Get phone numbers
            phone_numbers = contact.phoneNumbers()
            phone = None
            
            if phone_numbers and len(phone_numbers) > 0:
                # Get the first phone number (preferably mobile)
                for pn in phone_numbers:
                    label = pn.label() or ""
                    if "mobile" in label.lower() or "iphone" in label.lower():
                        phone = pn.value().stringValue()
                        break
                
                # Fallback to first number
                if not phone:
                    phone = phone_numbers[0].value().stringValue()
            
            if phone:
                # Clean phone number (remove spaces, dashes)
                phone = ''.join(c for c in phone if c.isdigit() or c == '+')
                
                contacts.append({
                    "id": contact.identifier(),
                    "name": full_name,
                    "phone": phone,
                    "suffix_type": matched_suffix
                })
    
    try:
        store.enumerateContactsWithFetchRequest_error_usingBlock_(
            request, None, enumerate_contacts
        )
    except Exception as e:
        print(f"❌ Error fetching contacts: {e}")
        return []
    
    return contacts


def sync_contacts_to_database(contacts: List[Dict]) -> int:
    """
    Sync fetched contacts to local SQLite database.
    
    Returns:
        Number of new contacts added
    """
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    new_count = 0
    
    for contact in contacts:
        # Check if contact exists
        cursor.execute("SELECT id, is_excluded FROM contacts WHERE id = ?", (contact['id'],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing contact (preserve exclusion status)
            cursor.execute('''
                UPDATE contacts 
                SET name = ?, phone = ?, suffix_type = ?, updated_at = ?
                WHERE id = ?
            ''', (contact['name'], contact['phone'], contact['suffix_type'], now, contact['id']))
        else:
            # Insert new contact
            cursor.execute('''
                INSERT INTO contacts (id, name, phone, suffix_type, is_excluded, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, ?, ?)
            ''', (contact['id'], contact['name'], contact['phone'], contact['suffix_type'], now, now))
            new_count += 1
    
    conn.commit()
    conn.close()
    
    return new_count


def get_contacts_for_messaging(suffix_filter: str = None) -> List[Dict]:
    """
    Get contacts eligible for messaging (not excluded, from database).
    
    Args:
        suffix_filter: Optional filter by suffix type (e.g., 'client')
    
    Returns:
        List of contact dictionaries
    """
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if suffix_filter:
        cursor.execute('''
            SELECT id, name, phone, suffix_type, last_messaged, message_count
            FROM contacts
            WHERE is_excluded = 0 AND suffix_type = ?
            ORDER BY name
        ''', (suffix_filter.lower(),))
    else:
        cursor.execute('''
            SELECT id, name, phone, suffix_type, last_messaged, message_count
            FROM contacts
            WHERE is_excluded = 0
            ORDER BY name
        ''')
    
    contacts = []
    for row in cursor.fetchall():
        contacts.append({
            "id": row[0],
            "name": row[1],
            "phone": row[2],
            "suffix_type": row[3],
            "last_messaged": row[4],
            "message_count": row[5]
        })
    
    conn.close()
    return contacts


def get_all_contacts_with_status() -> List[Dict]:
    """Get all contacts with their exclusion status for GUI display."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, phone, suffix_type, is_excluded, last_messaged, message_count
        FROM contacts
        ORDER BY suffix_type, name
    ''')
    
    contacts = []
    for row in cursor.fetchall():
        contacts.append({
            "id": row[0],
            "name": row[1],
            "phone": row[2],
            "suffix_type": row[3],
            "is_excluded": bool(row[4]),
            "last_messaged": row[5],
            "message_count": row[6]
        })
    
    conn.close()
    return contacts


def exclude_contact(contact_id: str):
    """Mark a contact as excluded from messaging."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE contacts SET is_excluded = 1, updated_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), contact_id))
    
    conn.commit()
    conn.close()


def include_contact(contact_id: str):
    """Remove exclusion from a contact."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE contacts SET is_excluded = 0, updated_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), contact_id))
    
    conn.commit()
    conn.close()


def mark_contact_messaged(contact_id: str, message_preview: str = "", images_count: int = 0):
    """Record that a message was sent to a contact."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Update contact record
    cursor.execute('''
        UPDATE contacts 
        SET last_messaged = ?, message_count = message_count + 1, updated_at = ?
        WHERE id = ?
    ''', (now, now, contact_id))
    
    # Add to message history
    cursor.execute('''
        INSERT INTO message_history (contact_id, sent_at, message_preview, images_count, status)
        VALUES (?, ?, ?, ?, 'sent')
    ''', (contact_id, now, message_preview[:100], images_count))
    
    conn.commit()
    conn.close()


def get_contact_stats() -> Dict:
    """Get statistics about contacts."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # Total contacts
    cursor.execute("SELECT COUNT(*) FROM contacts")
    stats['total'] = cursor.fetchone()[0]
    
    # By suffix type
    cursor.execute('''
        SELECT suffix_type, COUNT(*) FROM contacts
        GROUP BY suffix_type
    ''')
    stats['by_suffix'] = dict(cursor.fetchall())
    
    # Excluded contacts
    cursor.execute("SELECT COUNT(*) FROM contacts WHERE is_excluded = 1")
    stats['excluded'] = cursor.fetchone()[0]
    
    # Active (not excluded)
    stats['active'] = stats['total'] - stats['excluded']
    
    # Messaged today
    today = datetime.now().date().isoformat()
    cursor.execute('''
        SELECT COUNT(*) FROM message_history
        WHERE sent_at LIKE ?
    ''', (f"{today}%",))
    stats['messaged_today'] = cursor.fetchone()[0]
    
    conn.close()
    return stats


def refresh_contacts() -> Dict:
    """
    Refresh contacts from macOS Contacts app and sync to database.
    
    Returns:
        Statistics about the refresh operation
    """
    print("🔄 Refreshing contacts from macOS Contacts app...")
    
    # Request access if needed
    if not request_contacts_access():
        return {"error": "Contacts access not granted"}
    
    # Fetch contacts
    config = load_config()
    suffixes = config.get("contact_suffixes", ["client", "proxy", "interview"])
    
    contacts = fetch_contacts_from_macos(suffixes)
    print(f"   Found {len(contacts)} contacts matching suffixes: {suffixes}")
    
    # Sync to database
    new_count = sync_contacts_to_database(contacts)
    print(f"   Added {new_count} new contacts to database")
    
    # Get stats
    stats = get_contact_stats()
    
    return {
        "fetched": len(contacts),
        "new": new_count,
        "total": stats['total'],
        "active": stats['active'],
        "excluded": stats['excluded'],
        "by_suffix": stats['by_suffix']
    }


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Contact Fetcher for WhatsApp Marketing")
    parser.add_argument("--refresh", "-r", action="store_true", help="Refresh contacts from macOS")
    parser.add_argument("--list", "-l", action="store_true", help="List all contacts")
    parser.add_argument("--stats", "-s", action="store_true", help="Show contact statistics")
    parser.add_argument("--suffix", type=str, help="Filter by suffix type")
    parser.add_argument("--exclude", type=str, help="Exclude contact by ID")
    parser.add_argument("--include", type=str, help="Include contact by ID")
    
    args = parser.parse_args()
    
    if args.refresh:
        result = refresh_contacts()
        print("\n📊 Refresh Results:")
        print(f"   Fetched: {result.get('fetched', 0)}")
        print(f"   New: {result.get('new', 0)}")
        print(f"   Total: {result.get('total', 0)}")
        print(f"   Active: {result.get('active', 0)}")
        print(f"   Excluded: {result.get('excluded', 0)}")
        print(f"   By Suffix: {result.get('by_suffix', {})}")
    
    elif args.list:
        contacts = get_all_contacts_with_status()
        if args.suffix:
            contacts = [c for c in contacts if c['suffix_type'] == args.suffix.lower()]
        
        print(f"\n📋 Contacts ({len(contacts)} total):\n")
        for c in contacts:
            status = "❌ EXCLUDED" if c['is_excluded'] else "✅"
            last_msg = c['last_messaged'][:10] if c['last_messaged'] else "Never"
            print(f"   {status} [{c['suffix_type']}] {c['name']}")
            print(f"      📱 {c['phone']} | Last: {last_msg} | Count: {c['message_count']}")
    
    elif args.stats:
        stats = get_contact_stats()
        print("\n📊 Contact Statistics:")
        print(f"   Total: {stats['total']}")
        print(f"   Active: {stats['active']}")
        print(f"   Excluded: {stats['excluded']}")
        print(f"   By Suffix: {stats['by_suffix']}")
        print(f"   Messaged Today: {stats['messaged_today']}")
    
    elif args.exclude:
        exclude_contact(args.exclude)
        print(f"✅ Contact {args.exclude} excluded")
    
    elif args.include:
        include_contact(args.include)
        print(f"✅ Contact {args.include} included")
    
    else:
        parser.print_help()
        print("\n💡 Quick Start:")
        print("   python contact_fetcher.py --refresh   # Fetch contacts from macOS")
        print("   python contact_fetcher.py --list      # List all contacts")
        print("   python contact_fetcher.py --stats     # Show statistics")

