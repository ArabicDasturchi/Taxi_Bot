import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from app.core.config import API_ID, API_HASH, SESSION_STRING, PHONE
from app.database.db import AsyncSessionLocal
from app.database.crud import CRUD

logger = logging.getLogger(__name__)

# We delay instantiating the userbot until start_userbot is called 
# to prevent asyncio loop errors during import.
userbot = None

TARGET_GROUPS = ["@andijon_toshkent_taksi", "@vodiy_toshkent_taxi_1"] # Example groups

async def start_userbot():
    global userbot
    if not API_ID or not API_HASH:
        logger.warning("Pyrogram Userbot not configured. Missing API_ID/API_HASH.")
        return
        
    userbot = Client(
        "taxi_userbot",
        api_id=int(API_ID),
        api_hash=API_HASH,
        phone_number=PHONE,
        session_string=SESSION_STRING if SESSION_STRING else None
    )
    
    # Message listener for parsing clients needs to be bound here if userbot is local/global
    @userbot.on_message(filters.chat(TARGET_GROUPS) & filters.text)
    async def parse_clients(client: Client, message: Message):
        text = message.text.lower()
        if "odam kerak" in text or "mashina kerak" in text or "toshkentga" in text or "andijonga" in text:
            logger.info(f"Potential client found: {message.text}")
            
            # Find an active driver to recommend (simple matching or random active)
            async with AsyncSessionLocal() as session:
                users = await CRUD.get_all_users(session)
                active_drivers = [u for u in users if u.status == 'active' and u.bot_enabled]
                
            if active_drivers:
                # Pick the first to recommend initially
                driver = active_drivers[0]
                reply_text = (
                    f"👋 Salom! Agar taksi kerak bo'lsa bizning litsenziyaga ega shofyorimiz xizmatga tayyor!\n\n"
                    f"🚗 <b>Mashina</b>: {driver.car_model or 'Zamonaviy avto'}\n"
                    f"📞 <b>Aloqaga chiqing</b>: {driver.contact_number}\n"
                    f"👤 Shofyor: {driver.full_name}"
                )
                try:
                    await message.reply_text(reply_text)
                except Exception as e:
                    logger.error(f"Cannot auto-reply client: {e}")
            
    logger.info("Starting Pyrogram Userbot...")
    await userbot.start()

async def send_ads_to_groups():
    if not userbot: return
    logger.info("Running auto ad scheduler task...")
    
    async with AsyncSessionLocal() as session:
        users = await CRUD.get_all_users(session)
        
        # Get all users with their routes efficiently using eager loading if possible, or just load mapping
        # For simple structure, let's load all active with bot
        for driver in users:
            if driver.status != 'active' or not driver.bot_enabled:
                continue
            
            routes = await CRUD.get_routes_by_driver(session, driver.id)
            if not routes:
                continue
                
            # Formatting multiple destinations if available, else first one
            route_str = f"{routes[-1].from_city} ⇄ {routes[-1].to_city}"
                
            ad_text = (
                f"🚕 <b>TAXI XIZMATI: {route_str.upper()}</b>\n\n"
                f"👤 <b>Haydovchi</b>: {driver.full_name}\n"
                f"🚗 <b>Mashina</b>: {driver.car_model or 'Komfort avto'}\n"
                f"📞 <b>Murojaat uchun</b>: {driver.contact_number}\n\n"
                f"✅ <i>Xavfsiz, qulay va o'z vaqtida manzilingizga yetkazamiz! Shu raqamga aloqaga chiqing!</i>"
            )
            
            for group in TARGET_GROUPS:
                try:
                    await userbot.send_message(group, ad_text)
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Error sending ad to {group}: {e}")
