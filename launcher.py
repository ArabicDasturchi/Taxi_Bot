import sys
import logging
import asyncio

# Setup async loop early for Pyrogram on Windows/Python3.10+ before importing it 
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from app.main import start_bots

if __name__ == "__main__":
    try:
        logging.info("Starting launcher...")
        loop.run_until_complete(start_bots())
    except KeyboardInterrupt:
        logging.info("Bot stopped correctly.")
