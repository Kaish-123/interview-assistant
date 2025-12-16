#!/usr/bin/env python3
"""
Telegram Group Finder - Find relevant groups for marketing
Searches for public groups/channels related to your niche
"""

import asyncio
import json
from pathlib import Path
from telethon import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel, Chat
from colorama import init, Fore, Style

init()

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"

# Keywords to search for proxy interview / job support groups
SEARCH_KEYWORDS = [
    "proxy interview",
    "interview proxy",
    "job support",
    "interview support",
    "data engineer job",
    "data analyst job",
    "full stack developer",
    "devops job support",
    "java developer job",
    "python developer job",
    "IT job support",
    "USA IT jobs",
    "remote interview",
    "tech interview",
    "coding interview",
    "software engineer job",
    "developer jobs USA",
    "IT consultancy",
    "job placement",
    "resume help IT",
    "mock interview",
    "interview preparation",
    "fresher IT jobs",
    "experienced IT jobs",
    "proxy support",
    "assessment support",
    "technical interview",
    "job referral",
    "IT training",
    "career support"
]


async def search_groups():
    """Search for relevant groups on Telegram."""
    
    # Load config
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    client = TelegramClient(
        str(SCRIPT_DIR / "finder_session"),
        config['api_id'],
        config['api_hash']
    )
    
    await client.start()
    print(f"{Fore.GREEN}✓ Connected to Telegram{Style.RESET_ALL}\n")
    
    all_results = {}
    
    print(f"{Fore.CYAN}🔍 Searching for relevant groups...{Style.RESET_ALL}")
    print("=" * 60)
    
    for keyword in SEARCH_KEYWORDS:
        try:
            print(f"{Fore.YELLOW}Searching: '{keyword}'...{Style.RESET_ALL}", end=" ")
            
            result = await client(SearchRequest(
                q=keyword,
                limit=50
            ))
            
            found = 0
            for chat in result.chats:
                if isinstance(chat, Channel):
                    username = f"@{chat.username}" if chat.username else f"ID:{chat.id}"
                    
                    # Skip if already found
                    if username in all_results:
                        continue
                    
                    # Determine type
                    chat_type = "Group" if chat.megagroup else "Channel"
                    members = chat.participants_count if hasattr(chat, 'participants_count') and chat.participants_count else "?"
                    
                    all_results[username] = {
                        'title': chat.title,
                        'username': username,
                        'type': chat_type,
                        'members': members,
                        'id': chat.id
                    }
                    found += 1
            
            print(f"{Fore.GREEN}Found {found} new{Style.RESET_ALL}")
            await asyncio.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            await asyncio.sleep(2)
    
    await client.disconnect()
    
    # Sort by type and display
    groups = [r for r in all_results.values() if r['type'] == 'Group']
    channels = [r for r in all_results.values() if r['type'] == 'Channel']
    
    print("\n" + "=" * 60)
    print(f"\n{Fore.GREEN}📊 SEARCH RESULTS{Style.RESET_ALL}")
    print(f"Total found: {len(all_results)} ({len(groups)} groups, {len(channels)} channels)\n")
    
    # Display groups first (more valuable for marketing)
    print(f"{Fore.CYAN}👥 GROUPS (you can likely post here):{Style.RESET_ALL}")
    print("-" * 60)
    for i, g in enumerate(groups[:50], 1):
        members_str = f"({g['members']} members)" if g['members'] != "?" else ""
        print(f"{i:2}. {g['title'][:40]:<40} {g['username']:<25} {members_str}")
    
    print(f"\n{Fore.YELLOW}📢 CHANNELS (need admin access to post):{Style.RESET_ALL}")
    print("-" * 60)
    for i, c in enumerate(channels[:30], 1):
        members_str = f"({c['members']} members)" if c['members'] != "?" else ""
        print(f"{i:2}. {c['title'][:40]:<40} {c['username']:<25} {members_str}")
    
    # Save results to file
    results_file = SCRIPT_DIR / "found_groups.json"
    with open(results_file, 'w') as f:
        json.dump({
            'groups': groups,
            'channels': channels,
            'total': len(all_results)
        }, f, indent=2)
    
    print(f"\n{Fore.GREEN}✓ Results saved to: {results_file}{Style.RESET_ALL}")
    
    # Provide join instructions
    print(f"\n{Fore.CYAN}📝 NEXT STEPS:{Style.RESET_ALL}")
    print("1. Open Telegram and search for these group usernames")
    print("2. Join the relevant groups")
    print("3. Run: python add_new_groups.py (to add joined groups to your config)")
    print("4. Your marketing bot will automatically include new groups!")
    
    return all_results


async def join_groups(usernames: list):
    """Join multiple groups at once."""
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    client = TelegramClient(
        str(SCRIPT_DIR / "finder_session"),
        config['api_id'],
        config['api_hash']
    )
    
    await client.start()
    print(f"{Fore.GREEN}✓ Connected{Style.RESET_ALL}\n")
    
    joined = 0
    for username in usernames:
        try:
            # Normalize username
            if not username.startswith('@'):
                username = '@' + username
            
            print(f"Joining {username}...", end=" ")
            entity = await client.get_entity(username)
            await client(JoinChannelRequest(entity))
            print(f"{Fore.GREEN}✓ Joined!{Style.RESET_ALL}")
            joined += 1
            await asyncio.sleep(3)  # Rate limiting
        except Exception as e:
            print(f"{Fore.RED}✗ Failed: {e}{Style.RESET_ALL}")
    
    await client.disconnect()
    print(f"\n{Fore.GREEN}Joined {joined}/{len(usernames)} groups{Style.RESET_ALL}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--join":
        # Join mode: python group_finder.py --join @group1 @group2
        groups_to_join = sys.argv[2:]
        if groups_to_join:
            from telethon.tl.functions.channels import JoinChannelRequest
            asyncio.run(join_groups(groups_to_join))
        else:
            print("Usage: python group_finder.py --join @group1 @group2 ...")
    else:
        # Search mode
        asyncio.run(search_groups())

