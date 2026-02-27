import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Fix for Pyrogram initialization
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
from pyrogram import Client
async def main():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    if not api_id or not api_hash:
        print("API_ID yoki API_HASH topilmadi!")
        return

    # Load the session file
    app = Client("taxi_userbot", api_id=api_id, api_hash=api_hash)
    await app.start()
    session_string = await app.export_session_string()
    print("\n" + "="*50)
    print("MANA SIZNING SESSION_STRING KODINGIZ:")
    print(session_string)
    print("="*50 + "\n")
    print("Shu kodni nusxalab, .env faylidagi SESSION_STRING=  ketiga qo'shing.")
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
