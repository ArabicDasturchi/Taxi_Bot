import asyncio
from pyrogram import Client
from dotenv import load_dotenv
import os

load_dotenv()

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")

async def main():
    print("Userbot Sessiyasini yaratamiz...")
    if not API_ID or not API_HASH:
        print("XATO: .env faylda API_ID va API_HASH yo'q!")
        return
        
    async with Client("my_account", api_id=int(API_ID), api_hash=API_HASH, in_memory=True) as app:
        session_string = await app.export_session_string()
        print("\n" + "="*50)
        print("Sizning SESSION_STRING kalitingiz (buni nusxalab oling):")
        print("\n" + session_string + "\n")
        print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
