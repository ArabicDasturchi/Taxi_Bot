import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from app.core.config import API_ID, API_HASH
from app.database.db import AsyncSessionLocal
from app.database.crud import CRUD

logger = logging.getLogger(__name__)

# Removed TARGET_GROUPS. Bots will now operate in ALL groups the user account is a member of.

class UserbotManager:
    def __init__(self):
        self.clients = {}  # user_id: Client
        
    async def start_all(self):
        if not API_ID or not API_HASH:
            logger.warning("Pyrogram Userbot API keys not configured.")
            return

        async with AsyncSessionLocal() as session:
            users = await CRUD.get_all_users(session)
            for user in users:
                if user.status == 'active' and user.bot_enabled and user.session_string:
                    await self.add_client(user.id, user.session_string)

    async def add_client(self, user_id, session_string):
        if user_id in self.clients:
            return
            
        client = Client(
            f"userbot_{user_id}",
            api_id=int(API_ID),
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True
        )
        
        # Listen to ALL groups the user is a member of
        @client.on_message(filters.group & filters.text)
        async def parse_clients(c: Client, message: Message):
            text = message.text.lower()
            if "taksi kerak" in text or "toshkentga" in text or "vodiyga" in text or "toshkent" in text or "andijonga" in text:
                
                async with AsyncSessionLocal() as session:
                    db_user = await CRUD.get_user_by_id(session, user_id)
                    if not db_user or not db_user.bot_enabled or db_user.available_seats <= 0:
                        return
                        
                    # Filter by route
                    routes = await CRUD.get_routes_by_driver(session, user_id)
                    route_matches = False
                    for r in routes:
                        if r.from_city.lower() in text or r.to_city.lower() in text:
                            route_matches = True
                            
                    if route_matches:
                        reply_text = (
                            f"👋 Salom! Men huddi shu yo'nalishda taksi haydovchisiman, xizmatga tayyorman!\n\n"
                            f"🚗 <b>Mashinam:</b> {db_user.car_model or 'Komfort avto'}\n"
                            f"💺 <b>Bo'sh joylar:</b> {db_user.available_seats} ta\n"
                            f"📞 <b>Menga aloqaga chiqing:</b> {db_user.contact_number}\n\n"
                            f"✅ <i>(Ayni ushbu holatda manzilga tez ketamiz)</i>"
                        )
                        try:
                            await message.reply_text(reply_text)
                            # Optional: Update seats count or just let the driver do it manually
                        except Exception as e:
                            logger.error(f"Cannot auto-reply for {db_user.full_name}: {e}")

        try:
            await client.start()
            self.clients[user_id] = client
            logger.info(f"Started multi-userbot for user_id={user_id}")
                    
        except Exception as e:
            logger.error(f"Failed to start multi-userbot for user_id={user_id}: {e}")

    async def remove_client(self, user_id):
        if user_id in self.clients:
            try:
                await self.clients[user_id].stop()
            except:
                pass
            del self.clients[user_id]
            logger.info(f"Stopped multi-userbot for user_id={user_id}")
            
    async def send_ads(self):
        for user_id, client in list(self.clients.items()):
            try:
                async with AsyncSessionLocal() as session:
                    db_user = await CRUD.get_user_by_id(session, user_id)
                    if not db_user or not db_user.bot_enabled or db_user.available_seats <= 0:
                        continue
                        
                    routes = await CRUD.get_routes_by_driver(session, user_id)
                    if not routes: continue
                    
                    route_str = f"{routes[-1].from_city} ⇄ {routes[-1].to_city}"
                        
                    ad_text = (
                        f"🚕 <b>TAXI: {route_str.upper()}</b>\n\n"
                        f"💺 <b>Bo'sh joylar:</b> {db_user.available_seats} ta mavjud\n"
                        f"🚗 <b>Mashinam:</b> {db_user.car_model or 'Komfort avto'}\n"
                        f"📞 <b>Meni raqamim:</b> {db_user.contact_number}\n\n"
                        f"✅ <i>(Tez va xavfsiz manzilga yetib aytamiz, aloqaga chiqing!)</i>"
                    )
                    
                    # Interate through ALL groups the user is already a member of
                    from pyrogram.enums import ChatType
                    
                    async for dialog in client.get_dialogs():
                        if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                            try:
                                await client.send_message(dialog.chat.id, ad_text)
                                await asyncio.sleep(2)  # delay to prevent spam limits
                            except Exception as e:
                                logger.error(f"Error sending ad for {db_user.full_name} to {dialog.chat.id}: {e}")
                                
            except Exception as e:
                logger.error(f"Error in send_ads for {user_id}: {e}")

# Global instance
manager = UserbotManager()

async def start_userbot():
    await manager.start_all()

async def send_ads_to_groups():
    await manager.send_ads()
