#!/usr/bin/env python3
"""
WhatsApp API Marketing - Cron Job Script
=========================================
Designed to be run by cron/launchd on a schedule.
Sends messages once and exits.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add script directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from whatsapp_api_marketer import WhatsAppAPIMarketer

# Set up logging for cron
LOG_FILE = SCRIPT_DIR / "logs" / "cron_messages.log"
LOG_FILE.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def run_cron_job():
    """Run a single message sending cycle."""
    logger.info("=" * 60)
    logger.info("WHATSAPP API CRON JOB STARTED")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Initialize marketer
        config_path = SCRIPT_DIR / "config.json"
        marketer = WhatsAppAPIMarketer(str(config_path))
        
        # Verify credentials
        if not await marketer.verify_credentials():
            logger.error("API credentials verification failed!")
            return False
        
        # Send to all targets
        await marketer.send_to_all()
        
        # Cleanup
        await marketer._close_session()
        
        logger.info("CRON JOB COMPLETED SUCCESSFULLY")
        return True
        
    except Exception as e:
        logger.error(f"CRON JOB FAILED: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main entry point."""
    success = asyncio.run(run_cron_job())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
