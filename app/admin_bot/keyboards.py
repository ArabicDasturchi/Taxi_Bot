from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def admin_main_menu():
    keyboard = [
        [KeyboardButton(text="👥 Haydovchilar Ro'yxati")],
        [KeyboardButton(text="➕ Yangi Shofir Qo'shish"), KeyboardButton(text="💰 To'lovni Tasdiqlash")],
        [KeyboardButton(text="📈 Umumiy Statistika"), KeyboardButton(text="🔄 Botlarni Yoqish")],
        [KeyboardButton(text="👨💻 Admin Support")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def user_approve_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ To'lovni Tasdiqlash", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton(text="❌ Bekor Qilish", callback_data=f"reject_{user_id}")]
    ])
