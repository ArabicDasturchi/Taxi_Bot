from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def phone_request_keyboard():
    keyboard = [[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

def driver_main_menu(bot_enabled: bool = False):
    status_text = "🟢 Avto-qidiruvni Yoqish" if not bot_enabled else "🔴 Avto-qidiruvni O'chirish"
    
    keyboard = [
        [KeyboardButton(text="🚖 Yo'nalishni O'zgartirish"), KeyboardButton(text=status_text)],
        [KeyboardButton(text="📊 Mening Statistikam"), KeyboardButton(text="⚙️ Mening Ma'lumotlarim")],
        [KeyboardButton(text="💳 To'lov va Ta'riflar"), KeyboardButton(text="👨‍💻 Adminga Murojaat")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def select_direction_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Tumanlardan -> Toshkentga", callback_data="dir_to_tashkent")],
        [InlineKeyboardButton(text="⬅️ Toshkentdan -> Tumanlarga", callback_data="dir_from_tashkent")]
    ])

def regions_keyboard(direction: str):
    # direction is either 'to_tashkent' or 'from_tashkent'
    regions = [
        "Andijon", "Paxtaobod", "Izboskan", "Asaka", "Marhamat", 
        "Buloqboshi", "Xo'jaobod", "Baliqchi", "Oltinko'l", 
        "Shahrixon", "Bo'z", "Qo'rg'ontepa", "Qorasuv", 
        "Jalaquduq", "Xonobod", "Ulug'nor"
    ]
    
    keyboard = []
    # 2 buttons per row
    row = []
    for r in regions:
        # e.g route_to_tashkent_Andijon
        cb_data = f"route_{direction}_{r}"
        
        # Format text
        if direction == "to_tashkent":
            text = f"{r} ⇄ Toshkent"
        else:
            text = f"Toshkent ⇄ {r}"
            
        row.append(InlineKeyboardButton(text=text, callback_data=cb_data))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_directions")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
