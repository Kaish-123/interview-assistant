#!/usr/bin/env python3
"""
AUTO GROWTH ENGINE - Fully Automated Telegram Marketing
=========================================================
This script automatically:
1. Finds new relevant groups
2. Joins them (respecting rate limits)
3. Adds them to your marketing config
4. Your message bot will automatically send to new groups

Run this daily or set up as cron job for fully automated growth!
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from telethon import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel
from telethon.errors import FloodWaitError, UserAlreadyParticipantError, ChannelPrivateError

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
GROWTH_LOG = SCRIPT_DIR / "growth_log.json"

# Keywords to search for - focused on your niche
SEARCH_KEYWORDS = [
    "proxy interview",
    "interview proxy",
    "job support",
    "interview support",
    "data engineer",
    "data analyst",
    "full stack developer",
    "python developer",
    "java developer",
    "devops jobs",
    "IT jobs USA",
    "IT jobs India",
    "software developer",
    "tech jobs",
    "remote developer",
    "fresher IT jobs",
    "IT placement",
    "IT training",
    "coding jobs",
    "developer jobs",
    "cloud jobs",
    "aws jobs",
    "azure jobs",
    "backend developer",
    "frontend developer",
    "web developer jobs",
    "IT recruitment",
    "tech recruitment",
    "mock interview",
    "interview preparation"
]


def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


def load_growth_log():
    if GROWTH_LOG.exists():
        with open(GROWTH_LOG, 'r') as f:
            return json.load(f)
    return {
        "last_search": None,
        "last_join": None,
        "searched_keywords": [],
        "joined_groups": [],
        "failed_groups": [],
        "total_joined": 0
    }


def save_growth_log(log):
    with open(GROWTH_LOG, 'w') as f:
        json.dump(log, f, indent=2, default=str)


def get_existing_targets(config):
    """Get set of existing target usernames."""
    existing = set()
    for t in config.get('targets', []):
        username = t.get('username', '')
        if username.startswith('@'):
            existing.add(username.lower())
        elif username.startswith('ID:'):
            existing.add(username)
    return existing


async def find_new_groups(client, existing_targets, max_groups=50):
    """Search for new groups not already in config."""
    
    print("\n🔍 SEARCHING FOR NEW GROUPS...")
    print("=" * 60)
    
    found_groups = []
    searched = 0
    
    # Shuffle keywords for variety
    keywords = SEARCH_KEYWORDS.copy()
    random.shuffle(keywords)
    
    for keyword in keywords:
        if len(found_groups) >= max_groups:
            break
            
        try:
            print(f"  Searching: '{keyword}'...", end=" ")
            result = await client(SearchRequest(q=keyword, limit=30))
            
            new_count = 0
            for chat in result.chats:
                if isinstance(chat, Channel) and chat.megagroup:  # Only groups
                    username = f"@{chat.username}" if chat.username else None
                    
                    if username and username.lower() not in existing_targets:
                        if username.lower() not in [g['username'].lower() for g in found_groups]:
                            members = getattr(chat, 'participants_count', 0) or 0
                            found_groups.append({
                                'title': chat.title,
                                'username': username,
                                'members': members,
                                'id': chat.id
                            })
                            new_count += 1
            
            print(f"Found {new_count} new")
            searched += 1
            await asyncio.sleep(1.5)  # Rate limiting
            
        except Exception as e:
            print(f"Error: {str(e)[:30]}")
            await asyncio.sleep(2)
    
    # Sort by member count (bigger groups first)
    found_groups.sort(key=lambda x: x.get('members', 0), reverse=True)
    
    print(f"\n✅ Found {len(found_groups)} new groups!")
    return found_groups


async def join_new_groups(client, groups, max_joins=5):
    """Join new groups with rate limit handling."""
    
    print("\n🚀 JOINING NEW GROUPS...")
    print("=" * 60)
    
    joined = []
    failed = []
    
    for i, group in enumerate(groups[:max_joins], 1):
        try:
            print(f"  [{i}/{min(len(groups), max_joins)}] Joining {group['username']}...", end=" ")
            
            entity = await client.get_entity(group['username'])
            await client(JoinChannelRequest(entity))
            
            print(f"✅ Joined! ({group.get('members', '?')} members)")
            joined.append({
                'name': entity.title,
                'username': group['username'],
                'members': group.get('members', 0),
                'joined_at': datetime.now().isoformat()
            })
            
            # Wait between joins to avoid rate limits
            wait_time = random.randint(25, 40)
            print(f"      ⏳ Waiting {wait_time}s before next join...")
            await asyncio.sleep(wait_time)
            
        except UserAlreadyParticipantError:
            print("⚡ Already member")
            joined.append({
                'name': group.get('title', group['username']),
                'username': group['username'],
                'members': group.get('members', 0),
                'joined_at': 'already_member'
            })
            
        except FloodWaitError as e:
            print(f"⏰ Rate limited ({e.seconds}s)")
            if e.seconds < 120:  # Wait if less than 2 minutes
                await asyncio.sleep(e.seconds + 5)
            else:
                print("      Rate limit too long, stopping joins for now")
                failed.extend([g['username'] for g in groups[i:max_joins]])
                break
                
        except ChannelPrivateError:
            print("🔒 Private group, skipping")
            failed.append(group['username'])
            
        except Exception as e:
            print(f"❌ Failed: {str(e)[:40]}")
            failed.append(group['username'])
            await asyncio.sleep(3)
    
    print(f"\n✅ Joined {len(joined)} groups, {len(failed)} failed")
    return joined, failed


def add_groups_to_config(config, new_groups):
    """Add newly joined groups to config."""
    
    existing = get_existing_targets(config)
    added = 0
    
    for group in new_groups:
        username = group['username']
        if username.lower() not in existing:
            members_str = f" ({group.get('members', '?')})" if group.get('members') else ""
            config['targets'].append({
                'name': f"{group['name'][:35]}{members_str}",
                'username': username,
                'enabled': True
            })
            existing.add(username.lower())
            added += 1
    
    return added


async def run_auto_growth(max_search=30, max_join=5):
    """Main auto-growth function."""
    
    print("\n" + "=" * 60)
    print("  🌱 TECHYERA AUTO GROWTH ENGINE")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # Load config and log
    config = load_config()
    growth_log = load_growth_log()
    
    # Check if we should run (rate limit protection)
    last_join = growth_log.get('last_join')
    if last_join:
        last_join_time = datetime.fromisoformat(last_join)
        hours_since = (datetime.now() - last_join_time).total_seconds() / 3600
        if hours_since < 4:
            print(f"\n⏳ Only {hours_since:.1f} hours since last join.")
            print(f"   Wait {4 - hours_since:.1f} more hours to avoid rate limits.")
            print("   Searching only (no joins)...")
            max_join = 0
    
    # Connect to Telegram
    client = TelegramClient(
        str(SCRIPT_DIR / "growth_session"),
        config['api_id'],
        config['api_hash']
    )
    
    try:
        await client.start(phone=config['phone_number'])
        me = await client.get_me()
        print(f"\n✓ Connected as: {me.first_name}")
        
        # Get existing targets
        existing = get_existing_targets(config)
        print(f"📊 Current targets: {len(existing)}")
        
        # Find new groups
        new_groups = await find_new_groups(client, existing, max_groups=max_search)
        
        if new_groups and max_join > 0:
            # Join groups
            joined, failed = await join_new_groups(client, new_groups, max_joins=max_join)
            
            if joined:
                # Add to config
                added = add_groups_to_config(config, joined)
                save_config(config)
                print(f"\n✅ Added {added} new groups to config!")
                
                # Update growth log
                growth_log['last_join'] = datetime.now().isoformat()
                growth_log['joined_groups'].extend([g['username'] for g in joined])
                growth_log['total_joined'] += len(joined)
            
            growth_log['failed_groups'].extend(failed)
        
        # Update log
        growth_log['last_search'] = datetime.now().isoformat()
        save_growth_log(growth_log)
        
        # Summary
        print("\n" + "=" * 60)
        print("  📊 GROWTH SUMMARY")
        print("=" * 60)
        print(f"  Groups found: {len(new_groups)}")
        print(f"  Groups joined: {len(joined) if max_join > 0 and new_groups else 0}")
        print(f"  Total targets now: {len(config['targets'])}")
        print(f"  Total joined ever: {growth_log['total_joined']}")
        print("=" * 60)
        
    finally:
        await client.disconnect()
    
    return config


async def test_can_post(client, config):
    """Test which groups we can actually post to."""
    
    print("\n🧪 TESTING POST PERMISSIONS...")
    print("=" * 60)
    
    can_post = []
    cannot_post = []
    
    for target in config['targets']:
        try:
            entity = await client.get_entity(target['username'])
            # Try to get permissions
            if hasattr(entity, 'default_banned_rights'):
                if entity.default_banned_rights and entity.default_banned_rights.send_messages:
                    cannot_post.append(target['username'])
                else:
                    can_post.append(target['username'])
            else:
                can_post.append(target['username'])
        except:
            cannot_post.append(target['username'])
    
    print(f"  ✅ Can post: {len(can_post)}")
    print(f"  ❌ Cannot post: {len(cannot_post)}")
    
    return can_post, cannot_post


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--search-only":
            print("Search only mode (no joining)")
            asyncio.run(run_auto_growth(max_search=50, max_join=0))
        elif sys.argv[1] == "--aggressive":
            print("Aggressive mode (more joins)")
            asyncio.run(run_auto_growth(max_search=50, max_join=10))
        else:
            print("Usage: python auto_growth.py [--search-only|--aggressive]")
    else:
        # Normal mode
        asyncio.run(run_auto_growth(max_search=30, max_join=5))
