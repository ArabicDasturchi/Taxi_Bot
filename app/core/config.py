import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API (Userbot)
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
PHONE = os.environ.get("PHONE")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Bot Tokens
ADMIN_BOT_TOKEN = os.environ.get("ADMIN_BOT_TOKEN")
USER_BOT_TOKEN = os.environ.get("USER_BOT_TOKEN")

if not ADMIN_BOT_TOKEN or not USER_BOT_TOKEN:
    print("\n" + "="*50)
    print("XATO: Variables larni To'g'ri joylashtirmagansiz!!!")
    print("Siz hozir bu kalitlarni boshqa (Service idishni tashqarisida) joyga yozgansiz.")
    print("Yoki ularni nomida bo'sh joy qop ketgan!")
    print(f"Server ichida topilgan kalitlar qatori: {list(os.environ.keys())}")
    print("="*50 + "\n")

# Admin Settings
ADMIN_TELEGRAM_ID = int(os.environ.get("ADMIN_TELEGRAM_ID", 0))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "YourAdminUsername").replace("@", "")

# Payment Settings
MY_CARD = os.environ.get("MY_CARD", "9860 0825 3462 9983")
MY_CARD_EXPIRY = os.environ.get("MY_CARD_EXPIRY", "04/30")
SUBSCRIPTION_PRICE = 300000  # 300,000 so'm
