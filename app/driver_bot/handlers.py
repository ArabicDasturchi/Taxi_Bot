from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from app.core.config import ADMIN_TELEGRAM_ID, SUBSCRIPTION_PRICE, MY_CARD, MY_CARD_EXPIRY, ADMIN_USERNAME
from app.driver_bot.states import DriverRegistration, PyrogramAuth, SettingUpdate
from app.driver_bot.keyboards import phone_request_keyboard, driver_main_menu, select_direction_keyboard, regions_keyboard
from app.database.db import AsyncSessionLocal
from app.database.crud import CRUD
from app.admin_bot.keyboards import user_approve_keyboard
from app.worker.scraper import manager
from pyrogram import Client

clients_auth = {}

driver_router = Router()

@driver_router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user = await CRUD.get_user(session, telegram_id)
        
        if user:
            # Force Admin to be active always
            if telegram_id == ADMIN_TELEGRAM_ID and user.status != "active":
                await CRUD.update_user_status(session, user.id, "active")
                user.status = "active"

            if user.status == "active":
                await message.answer(
                    "🚕 <b>Taxi Express Driver Paneliga Xush Kelibsiz!</b>\n\nQuyidagi xizmatlardan birini tanlang:",
                    reply_markup=driver_main_menu(user.bot_enabled)
                )
            elif user.status == "pending":
                await message.answer(
                     f"⚠️ <b>To'lov tasdiqlanmagan.</b> Kuting yoki Adminga {SUBSCRIPTION_PRICE} so'm to'lov qilinganligini tasdiqlash uchun botga to'lov skrinshotini (cheki) yuboring."
                )
            else:
                await message.answer("Siz bloklangansiz.")
            return

    await message.answer(
        "🚕 <b>Taxi Express Bot</b> tizimiga xush kelibsiz!\n\nIltimos, ism va familiyangizni kiriting:"
    )
    await state.set_state(DriverRegistration.waiting_for_name)

@driver_router.message(DriverRegistration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer(
        f"Rahmat, {message.text}! Endi telefon raqamingizni pastdagi tugma orqali yuboring:",
        reply_markup=phone_request_keyboard()
    )
    await state.set_state(DriverRegistration.waiting_for_phone)

@driver_router.message(DriverRegistration.waiting_for_phone, F.contact)
@driver_router.message(DriverRegistration.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext, bot: Bot):
    phone_number = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone_number=phone_number)
    
    await message.answer(
        "📞 <b>Zo'r! Endi mijozlar sizga aloqaga chiqishi uchun asosiy telefon raqamingizni kiriting:</b>\n"
        "(Telegram raqamingiz bilan bir xil bo'lishi ham mumkin)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(DriverRegistration.waiting_for_contact_number)

@driver_router.message(DriverRegistration.waiting_for_contact_number)
async def process_contact_number(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(contact_number=message.text)
    
    await message.answer(
        "🚗 <b>Ajoyib! Endi mashinangiz rusumini va rangini kiriting:</b>\n\nMisol uchun: <i>Oq Chevrolet Cobalt</i> yoki <i>Qora Gentra</i>"
    )
    await state.set_state(DriverRegistration.waiting_for_car_model)

@driver_router.message(DriverRegistration.waiting_for_car_model)
async def process_car_model(message: Message, state: FSMContext, bot: Bot):
    car_model = message.text
    user_data = await state.get_data()
    full_name = user_data.get("full_name")
    phone_number = user_data.get("phone_number")
    contact_number = user_data.get("contact_number")
    telegram_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        user = await CRUD.create_user(session, telegram_id, full_name, phone_number, contact_number, car_model)
        
        # Check Admin or 1st free user Bypass
        all_users = await CRUD.get_all_users(session)
        non_admin_users = [u for u in all_users if u.telegram_id != ADMIN_TELEGRAM_ID]
        
        is_free_or_admin = telegram_id == ADMIN_TELEGRAM_ID or len(non_admin_users) <= 1
        
        if is_free_or_admin:
            await CRUD.update_user_status(session, user.id, "active")
            user.status = "active"
            
    if is_free_or_admin:
        await message.answer(
            "👨‍💻 <b>To'lov avtomatik tarzda by-pass qilindi. (Admin/Free Access)</b>\n\nMarhamat xizmatlardan birini tanlang va botni tekshiring:",
            reply_markup=driver_main_menu(bot_enabled=False)
        )
        await state.clear()
        return

    await message.answer(
        f"✅ <b>Tabriklaymiz, ro'yxatdan o'tdingiz!</b>\n\n"
        f"Endi botdan to'liq va professional tarzda foydalanish uchun <b>{SUBSCRIPTION_PRICE} so'm</b> to'lov qiling.\n\n"
        f"Karta raqam: <b><code>{MY_CARD}</code></b>\n"
        f"Muddati: <b>{MY_CARD_EXPIRY}</b>\n\n"
        f"💳 <i>To'lov qilganingizni tasdiqlovchi rasmni (chekni) shu yerga tashlang!</i>"
    )
    await state.clear()
    
    # Notify Admin about new user registration
    await bot.send_message(
        ADMIN_TELEGRAM_ID,
        f"👤 <b>Yangi Foydalanuvchi!</b>\n\n"
        f"Ism: {full_name}\n"
        f"Tel: {phone_number}\n"
        f"Aloqa: {contact_number}\n"
        f"Mashina: {car_model}\n\n"
        f"<i>To'lov skrinshoti kutilyapti...</i>"
    )

@driver_router.message(F.photo)
async def handle_payment_receipt(message: Message, bot: Bot):
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user = await CRUD.get_user(session, telegram_id)
        if not user or user.status == "active":
            return # Ignore if active or not user
            
        if user.status == "pending":
            await message.send_copy(
                ADMIN_TELEGRAM_ID, 
                reply_markup=user_approve_keyboard(user.id)
            )
            await bot.send_message(ADMIN_TELEGRAM_ID, f"💰 <b>Foydalanuvchi to'lov chekini yubordi.</b>\nFoydalanuvchi ID: {user.id}\nIsmi: {user.full_name}\nTasdiqlaysizmi?")
            await message.answer("⏳ <b>To'lovingiz adminga yuborildi.</b>\n\nTasdiqlanishini kuting. Tasdiqlangach sizga xabar yuboriladi.")

@driver_router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    if callback.from_user.id != ADMIN_TELEGRAM_ID:
        return
        
    user_id = int(callback.data.split("_")[1])
    async with AsyncSessionLocal() as session:
        await CRUD.update_user_status(session, user_id, "active")
        user = await CRUD.get_user_by_id(session, user_id)
        
    if user:
        await bot.send_message(user.telegram_id, "✅ <b>Sizning to'lovingiz tasdiqlandi!</b>\n\nSiz endi tizimdan to'liq foydalanishingiz mumkin.")
    await callback.message.edit_text("✅ To'lov tasdiqlandi va haydovchi 'active' holatiga o'tkazildi.")

@driver_router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    if callback.from_user.id != ADMIN_TELEGRAM_ID:
        return
        
    user_id = int(callback.data.split("_")[1])
    async with AsyncSessionLocal() as session:
        await CRUD.update_user_status(session, user_id, "rejected")
        user = await CRUD.get_user_by_id(session, user_id)
        
    if user:
        await bot.send_message(user.telegram_id, "❌ <b>To'lovingiz rad etildi!</b>\n\nIltimos to'lov chekini qaytadan yuboring yoki adminga murojaat qiling.")
    await callback.message.edit_text("❌ To'lov rad etildi va haydovchiga xabar yuborildi.")

@driver_router.message(F.text == "🚖 Yo'nalishni O'zgartirish")
async def choose_route(message: Message):
    async with AsyncSessionLocal() as session:
        user = await CRUD.get_user(session, message.from_user.id)
        if not user or user.status != "active":
            return
            
    await message.answer(
        "📍 <b>Siz qaysi yo'nalishda faoliyat olib borasiz?</b>\n\nIltimos, avval yo'nalishni tanlang:", 
        reply_markup=select_direction_keyboard()
    )

@driver_router.callback_query(F.data.in_(["dir_to_tashkent", "dir_from_tashkent"]))
async def direction_selected(callback: CallbackQuery):
    direction = callback.data.replace("dir_", "")
    text = "📍 <b>Qaysi tumandan Toshkentga ketmoqchisiz?</b>" if direction == "to_tashkent" else "📍 <b>Toshkentdan qaysi tumanga ketmoqchisiz?</b>"
    await callback.message.edit_text(text, reply_markup=regions_keyboard(direction))

@driver_router.callback_query(F.data == "back_to_directions")
async def back_to_directions(callback: CallbackQuery):
    await callback.message.edit_text(
        "📍 <b>Siz qaysi yo'nalishda faoliyat olib borasiz?</b>\n\nIltimos, avval yo'nalishni tanlang:", 
        reply_markup=select_direction_keyboard()
    )

@driver_router.callback_query(F.data.startswith("route_"))
async def route_selected(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await CRUD.get_user(session, callback.from_user.id)
        if not user or user.status != "active": return
            
        # Example data: route_to_tashkent_Andijon or route_from_tashkent_Paxtaobod
        data = callback.data.split("_")
        direction = data[1] + "_" + data[2] # to_tashkent
        region = data[3]
        
        if direction == "to_tashkent":
            from_city = region
            to_city = "Toshkent"
            text_result = f"{region} ⇄ Toshkent"
        else:
            from_city = "Toshkent"
            to_city = region
            text_result = f"Toshkent ⇄ {region}"
        
        await CRUD.add_passenger_route(session, user.id, from_city, to_city) 
        
    await callback.message.edit_text(
        f"✅ Siz <b>{text_result}</b> yo'nalishini tanladingiz.\n\n"
        f"Endi bot avtomatik ushbu yo'nalish bo'yicha mijoz qidiradi. (Boshqa yo'nalish ham qo'shishingiz mumkin)\n\n"
        f"Avto qidiruv ishlashi uchun, pastdagi <b>🟢 Avto-qidiruvni Yoqish</b> tugmasini bossangiz bas."
    )

@driver_router.message(F.text == "🟢 Avto-qidiruvni Yoqish")
async def start_auth(message: Message, state: FSMContext):
    async with AsyncSessionLocal() as session:
        user = await CRUD.get_user(session, message.from_user.id)
        if not user or user.status != "active": return
        if user.session_string:
            await CRUD.update_bot_toggle(session, user.id, True)
            await manager.add_client(user.id, user.session_string)
            await message.answer("✅ Avto-qidiruv va avto-habar yoqildi! Endi bot guruhlarda sizning nomingizdan ishlaydi.", reply_markup=driver_main_menu(True))
            return
            
    await message.answer("<b>Sizning telegramingiz nomidan guruhlarga avtomatik e'lon tashlash uchun Telegram ga biriktirishimiz kerak!</b>\n\nIltimos, telegram raqamingizni yuboring (Masalan: +998901234567):", reply_markup=phone_request_keyboard())
    await state.set_state(PyrogramAuth.waiting_for_phone)

@driver_router.message(PyrogramAuth.waiting_for_phone)
async def auth_phone(message: Message, state: FSMContext, bot: Bot):
    phone = message.contact.phone_number if message.contact else message.text
    
    # Check if user clicked a menu button instead of entering a phone number
    if phone in ["🚖 Yo'nalishni O'zgartirish", "💳 To'lov va Ta'riflar", "📊 Mening Statistikam", "⚙️ Mening Ma'lumotlarim", "👨‍💻 Adminga Murojaat", "💺 Bo'sh Joylar Soni", "🔴 Avto-qidiruvni O'chirish"]:
        await state.clear()
        async with AsyncSessionLocal() as session:
            user = await CRUD.get_user(session, message.from_user.id)
            await message.answer("🔄 Avto-qidiruvga ulanish bekor qilindi.", reply_markup=driver_main_menu(user.bot_enabled))
        return

    phone = str(phone).replace("+", "").replace(" ", "").strip()
    
    if not phone.isdigit():
        return await message.answer("❗️ <b>Noto'g'ri format!</b> Raqam faqat sonlardan iborat bo'lishi kerak (misol: +998901234567). Iltimos, qaytadan kiriting:")
        
    from app.core.config import API_ID, API_HASH
    try:
        client = Client(f"temp_auth_{message.from_user.id}", api_id=int(API_ID), api_hash=API_HASH, in_memory=True)
        await client.connect()
        sent_code = await client.send_code(phone)
        clients_auth[message.from_user.id] = {"client": client, "phone": phone, "phone_code_hash": sent_code.phone_code_hash}
        await message.answer(
            "📲 <b>Telegram rasmiy tasdiqlash kodini yubordi!</b>\n\n"
            "⚠️ <b>DIQQAT:</b> Xavfsizlik sababli kodni yozishda RAQAMLAR ORASINI OCHIB yozing! "
            "Aks holda o'z hisobingizdan vaqtincha bloklanasiz!\n\n"
            "✅ <b>To'g'ri yozish:</b> <code>1 2 3 4 5</code>\n"
            "❌ <b>Noto'g'ri yozish:</b> <code>12345</code>\n\n"
            "Iltimos, kodingizni oralariga probel tashlab yuboring:", 
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(PyrogramAuth.waiting_for_code)
    except Exception as e:
        await message.answer(f"Xato yuz berdi: {e}. Qaytadan /start bosing.")
        await state.clear()

@driver_router.message(PyrogramAuth.waiting_for_code)
async def auth_code(message: Message, state: FSMContext):
    code = message.text.replace(" ", "").replace("-", "").strip()
    auth_data = clients_auth.get(message.from_user.id)
    if not auth_data:
        return await message.answer("Seans eskirgan. Qaytadan urinib ko'ring.")
        
    client = auth_data["client"]
    try:
        await client.sign_in(auth_data["phone"], auth_data["phone_code_hash"], code)
        session_string = await client.export_session_string()
        await client.disconnect()
        del clients_auth[message.from_user.id]
        
        async with AsyncSessionLocal() as session:
            db_user = await CRUD.get_user(session, message.from_user.id)
            await CRUD.update_session_string(session, db_user.id, session_string)
            await CRUD.update_bot_toggle(session, db_user.id, True)
            await manager.add_client(db_user.id, session_string)
            
        await message.answer("🎉 <b>Ajoyib! Telegram hisobingiz muvaffaqiyatli ulandi!</b> Avto-qidiruv va mijozlarga javob qaytarish yoqildi!", reply_markup=driver_main_menu(True))
        await state.clear()
        
    except Exception as e:
        if "SessionPasswordNeeded" in str(type(e)):
            await message.answer("Sizda Ikki qadamli tekshiruv (2FA Parol) yoqilgan ekan. Iltimos, Telegram parolingizni kiriting:")
            await state.set_state(PyrogramAuth.waiting_for_password)
        else:
            await message.answer(f"Kodni kiritishda xatolik: Noto'g'ri kod. Yana muallif kodni yozing:")

@driver_router.message(PyrogramAuth.waiting_for_password)
async def auth_password(message: Message, state: FSMContext):
    password = message.text
    auth_data = clients_auth.get(message.from_user.id)
    client = auth_data["client"]
    try:
        await client.check_password(password)
        session_string = await client.export_session_string()
        await client.disconnect()
        del clients_auth[message.from_user.id]
        
        async with AsyncSessionLocal() as session:
            db_user = await CRUD.get_user(session, message.from_user.id)
            await CRUD.update_session_string(session, db_user.id, session_string)
            await CRUD.update_bot_toggle(session, db_user.id, True)
            await manager.add_client(db_user.id, session_string)
            
        await message.answer("🎉 Ajoyib! Telegram hisobingiz ulandi! Avto-qidiruv yoqildi.", reply_markup=driver_main_menu(True))
        await state.clear()
    except Exception as e:
        await message.answer(f"Parolda xatolik: noto'g'ri parol kiritdingiz. Yana urining:")

@driver_router.message(F.text == "🔴 Avto-qidiruvni O'chirish")
async def toggle_off(message: Message):
    async with AsyncSessionLocal() as session:
        user = await CRUD.get_user(session, message.from_user.id)
        if user.status != "active": return
        await CRUD.update_bot_toggle(session, user.id, False)
        await manager.remove_client(user.id)
        
    await message.answer("❌ Avto-qidiruv to'xtatildi.", reply_markup=driver_main_menu(False))

@driver_router.message(F.text == "💺 Bo'sh Joylar Soni")
async def ask_for_seats(message: Message, state: FSMContext):
    await message.answer("Hozirda mashinangizda nechta bo'sh joy bor? (Faqat raqam kiriting, masalan: 3):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SettingUpdate.waiting_for_seats)

@driver_router.message(SettingUpdate.waiting_for_seats)
async def update_seats(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 0 or int(message.text) > 4:
        return await message.answer("Iltimos faqat raqam kiriting (0-4):")
    
    seats = int(message.text)
    async with AsyncSessionLocal() as session:
        user = await CRUD.get_user(session, message.from_user.id)
        await CRUD.update_available_seats(session, user.id, seats)
    
    await message.answer(f"✅ Bo'sh joylar soni: <b>{seats} ta</b> deb belgilandi!\nEndi mijozlarga shunday yetkaziladi.", reply_markup=driver_main_menu(user.bot_enabled))
    await state.clear()

@driver_router.message(F.text == "📊 Mening Statistikam")
async def driver_stats(message: Message):
    async with AsyncSessionLocal() as session:
        user = await CRUD.get_user(session, message.from_user.id)
        if not user: return
        
        stat_text = (
            f"📊 <b>Sizning Statistikangiz:</b>\n\n"
            f"✅ <b>Topilgan mijozlar:</b> {user.clients_found} ta\n"
            f"📤 <b>Yuborilgan e'lonlar:</b> {user.ads_sent} marta\n"
            f"⏳ Hisobingiz faol."
        )
        await message.answer(stat_text)

@driver_router.message(F.text == "⚙️ Mening Ma'lumotlarim")
async def my_data_info(message: Message):
    async with AsyncSessionLocal() as session:
        user = await CRUD.get_user(session, message.from_user.id)
        if not user: return
        
        info_text = (
            f"⚙️ <b>Sizning profilingiz ma'lumotlari:</b>\n\n"
            f"👤 <b>Ism:</b> {user.full_name}\n"
            f"📞 <b>Telegram Raqam:</b> {user.phone_number}\n"
            f"☎️ <b>Aloqa Raqam:</b> {user.contact_number}\n"
            f"🚗 <b>Avtomobil:</b> {user.car_model}\n\n"
            f"<i>Ma'lumotlarni o'zgartirish uchun adminga murojaat qiling.</i>"
        )
        await message.answer(info_text)

@driver_router.message(F.text == "💳 To'lov va Ta'riflar")
async def payment_info(message: Message):
    async with AsyncSessionLocal() as session:
        user = await CRUD.get_user(session, message.from_user.id)
        if not user: return
        
        status_text = "🟢 Faol" if user.status == "active" else ("🔴 Bloklangan / Kutilmoqda" if user.status != "pending" else "⏳ Tasdiqlanmoqda")
        non_admin_users = [u for u in (await CRUD.get_all_users(session)) if u.telegram_id != ADMIN_TELEGRAM_ID]
        is_free_or_admin = message.from_user.id == ADMIN_TELEGRAM_ID or (user.telegram_id != ADMIN_TELEGRAM_ID and user in non_admin_users[:1])
        
        tarif = "Cheksiz (Admin/Premium)" if is_free_or_admin else "Oylik obuna bo'yicha"
        
        pay_text = (
            f"💳 <b>To'lov ma'lumotlaringiz:</b>\n\n"
            f"🔹 <b>Joriy Status:</b> {status_text}\n"
            f"🔹 <b>Ta'rif:</b> {tarif}\n\n"
            f"💰 <b>Obuna narxi:</b> {SUBSCRIPTION_PRICE} so'm\n"
            f"Karta raqam: <b><code>{MY_CARD}</code></b>\n"
            f"Muddati: <b>{MY_CARD_EXPIRY}</b>\n\n"
            f"<i>To'lov muddati tugaganda yana shu raqamga to'lov qilib chekni yuborasiz!</i>"
        )
        await message.answer(pay_text)

@driver_router.message(F.text == "👨‍💻 Adminga Murojaat")
async def talk_to_admin(message: Message):
    await message.answer(f"👨‍💻 <b>Admin bilan bog'lanish:</b>\n\nSavol va takliflaringiz bo'lsa adminga yozishingiz mumkin:\n👉 <a href='https://t.me/{ADMIN_USERNAME}'>Adminga Yozish</a>")
