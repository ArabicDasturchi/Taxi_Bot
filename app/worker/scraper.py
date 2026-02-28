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
        if "taksi kerak" in text or "toshkentga" in text or "vodiyga" in text or "andijonga" in text or "farg'onaga" in text or "namanganga" in text:
            logger.info(f"Potential client found: {message.text}")
            
            async with AsyncSessionLocal() as session:
                users = await CRUD.get_all_users(session)
                active_drivers = [u for u in users if u.status == 'active' and u.bot_enabled]
                
                # Check if we have any matching routes
                matching_driver = None
                for driver in active_drivers:
                    routes = await CRUD.get_routes_by_driver(session, driver.id)
                    for r in routes:
                        from_c = r.from_city.lower()
                        to_c = r.to_city.lower()
                        # Very simple match logic: if message mentions the destination or origin
                        if from_c in text or to_c in text or "toshkent" in text or "vodiy" in text:
                            matching_driver = driver
                            break
                    if matching_driver:
                        break
                
                # If no specific route matched, pick any active bot driver
                if not matching_driver and active_drivers:
                    matching_driver = active_drivers[0]
                    
            if matching_driver:
                reply_text = (
                    f"👋 Salom! Sizga taksi kerakmi? Bizning ishonchli haydovchimiz xizmatga tayyor!\n\n"
                    f"👤 <b>Shofyor:</b> {matching_driver.full_name}\n"
                    f"🚗 <b>Mashina:</b> {matching_driver.car_model or 'Komfort avto'}\n"
                    f"📞 <b>Aloqaga chiqing:</b> {matching_driver.contact_number}\n\n"
                    f"✅ <i>(Tez va xavfsiz manzilga yetib oling!)</i>"
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
