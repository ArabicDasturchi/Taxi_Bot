from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from app.core.config import ADMIN_TELEGRAM_ID, ADMIN_USERNAME
from app.admin_bot.keyboards import admin_main_menu
from app.database.db import AsyncSessionLocal
from app.database.crud import CRUD

admin_router = Router()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_TELEGRAM_ID

@admin_router.message(CommandStart())
@admin_router.message(Command("admin"))
async def admin_start(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("Siz admin emassiz!")
        
    await message.answer(
        "🚕 <b>Taxi Admin Professional Panel</b>\n\nXizmatlardan birini tanlang:",
        reply_markup=admin_main_menu()
    )

@admin_router.message(F.text == "👥 Haydovchilar Ro'yxati")
async def show_drivers(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        users = await CRUD.get_all_users(session)
        
    text = "👥 <b>Hozirgi Haydovchilar:</b>\n\n"
    if not users:
        text += "Hali haydovchilar yo'q."
    for u in users:
        text += f"👤 <b>{u.full_name}</b> | Tel: {u.phone_number} | Status: {u.status}\n"
        
    await message.answer(text)

@admin_router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
        
    user_id = int(callback.data.split("_")[1])
    async with AsyncSessionLocal() as session:
        await CRUD.update_user_status(session, user_id, "active")
        user = await CRUD.get_user(session, user_id)
        
    await bot.send_message(user_id, "✅ <b>Sizning to'lovingiz tasdiqlandi!</b>\n\nSiz endi tizimdan to'liq foydalanishingiz mumkin.")
    await callback.message.edit_text("✅ To'lov tasdiqlandi va haydovchi 'active' holatiga o'tkazildi.")

@admin_router.message(F.text == "📈 Umumiy Statistika")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    async with AsyncSessionLocal() as session:
        users = await CRUD.get_all_users(session)
        active = sum(1 for u in users if u.status == "active")
        pending = sum(1 for u in users if u.status == "pending")
        
    text = f"📈 <b>Umumiy Statistika:</b>\n\n"
    text += f"👥 Jami haydovchilar: {len(users)}\n"
    text += f"✅ Faol: {active}\n"
    text += f"⏳ Kutmoqda: {pending}\n"
    await message.answer(text)

@admin_router.message(F.text == "➕ Yangi Shofir Qo'shish")
async def add_driver_info(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("ℹ️ <b>Ma'lumot:</b>\n\nYangi haydovchilar to'g'ridan-to'g'ri <i>Foydalanuvchi Boti</i> orqali ro'yxatdan o'tishlari kerak. Bu ma'lumotlar bazasi xavfsizligi va to'g'ri ishlashi uchun muhim.")

@admin_router.message(F.text == "💰 To'lovni Tasdiqlash")
async def pending_payments(message: Message):
    if not is_admin(message.from_user.id): return
    async with AsyncSessionLocal() as session:
        users = await CRUD.get_all_users(session)
        pending_users = [u for u in users if u.status == "pending"]
    
    if not pending_users:
        return await message.answer("✅ Hozircha tasdiqlanmagan to'lovlar mavjud emas.")
        
    await message.answer(f"⏳ <b>Kutilayotgan to'lovlar ({len(pending_users)} ta):</b>\n\nIltimos, har bir foydalanuvchining to'lov chekini tekshirib tasdiqlang. Cheklar tushgan xabarlardan tasdiqlashingiz mumkin.")

@admin_router.message(F.text == "🔄 Botlarni Yoqish")
async def toggle_system(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("⚙️ <b>Tizim Holati:</b>\n\nBarcha botlar va Userbot parser xizmati faol holatda ishlab turibdi. Tizimni o'chirish uchun serverdan (yoki terminaldan) to'xtatish kerak.")

@admin_router.message(F.text == "👨💻 Admin Support")
async def admin_support(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer(f"👨‍💻 <b>Dasturiy ta'minot (Support):</b>\n\nAgar botda biror muammo chiqsa yoki qo'shimcha funksiya kerak bo'lsa darhol murojat qiling:\n👉 <a href='https://t.me/{ADMIN_USERNAME}'>Adminga Yozish</a>")
