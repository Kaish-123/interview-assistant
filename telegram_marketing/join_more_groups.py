#!/usr/bin/env python3
"""
Join More Groups - Run this script later to join remaining groups
Telegram has rate limits, so we join groups slowly over time.
"""

import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import FloodWaitError, UserAlreadyParticipantError
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# Groups to join (remaining from our search)
GROUPS_TO_JOIN = [
    '@reactjs2020',
    '@itjobsusa',
    '@devopssupportazureaws',
    '@onlypythondevelopers',
    '@proxyandsupport',
    '@USA_Top_IT_Trainings_Placements',
    '@fullstackdeveloperjob',
    '@aws_cloud_professional',
    '@java_jobs_inteview_support_proxy',
    '@gcpjobs',
    '@pythonproexpert',
    '@IT_Fresher_Jobs',
    '@developer_jobs',
    '@usa_it_jobs',
    '@awssaac03practiceandjobs',
    '@azuredevopsjobs',
    '@tech_job_support',
    '@awsdevopsgroup',
    '@techjobs2024',
    '@FullStackDevsGroup',
    '@fullstackdevlopermari',
    '@ITJobsIndiaUSA',
    '@devops_it_jobs',
    '@JOBIT_Recruitment_Indonesia',
    '@na3ml_jobs',
    '@ds_de_jobs',
    '@azuretra',
    '@AI_ML_Jobs',
    '@devops_jobs_ru',
    '@it_world_jobs'
]

async def join_groups_slowly():
    """Join groups with proper delays to avoid rate limits."""
    
    config = json.load(open(SCRIPT_DIR / 'config.json'))
    client = TelegramClient(
        str(SCRIPT_DIR / 'finder_session'),
        config['api_id'],
        config['api_hash']
    )
    
    await client.start()
    print("✓ Connected to Telegram")
    print()
    print("🚀 Joining groups (with delays to avoid rate limits)...")
    print("=" * 60)
    
    joined = []
    
    for i, username in enumerate(GROUPS_TO_JOIN, 1):
        try:
            print(f"[{i}/{len(GROUPS_TO_JOIN)}] Joining {username}...", end=" ")
            entity = await client.get_entity(username)
            await client(JoinChannelRequest(entity))
            print(f"✅ Joined: {entity.title}")
            joined.append({
                'name': entity.title,
                'username': username
            })
            
            # Long delay between joins to avoid rate limits
            print(f"    ⏳ Waiting 30 seconds before next join...")
            await asyncio.sleep(30)
            
        except UserAlreadyParticipantError:
            print("⚡ Already a member")
        except FloodWaitError as e:
            print(f"⏰ Rate limited for {e.seconds}s")
            if e.seconds < 300:  # If less than 5 minutes, wait
                print(f"    Waiting {e.seconds} seconds...")
                await asyncio.sleep(e.seconds + 5)
                # Retry
                try:
                    entity = await client.get_entity(username)
                    await client(JoinChannelRequest(entity))
                    print(f"    ✅ Joined on retry!")
                    joined.append({'name': entity.title, 'username': username})
                except:
                    pass
            else:
                print("    Too long wait, skipping remaining groups")
                break
        except Exception as e:
            print(f"❌ Failed: {str(e)[:50]}")
        
        await asyncio.sleep(5)
    
    await client.disconnect()
    
    print()
    print("=" * 60)
    print(f"✅ Successfully joined {len(joined)} new groups!")
    
    if joined:
        print()
        print("📝 Add these to your config.json targets:")
        print("-" * 60)
        for g in joined:
            print(f'  {{"name": "{g["name"][:30]}", "username": "{g["username"]}", "enabled": true}},')
    
    return joined


if __name__ == "__main__":
    print("=" * 60)
    print("  TELEGRAM GROUP JOINER")
    print("  Run this to join more groups for marketing")
    print("=" * 60)
    print()
    asyncio.run(join_groups_slowly())
