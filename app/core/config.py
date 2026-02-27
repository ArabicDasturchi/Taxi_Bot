import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API (Userbot)
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
SESSION_STRING = os.getenv("SESSION_STRING")

# Bot Tokens
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN")

# Admin Settings
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", 0))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "YourAdminUsername").replace("@", "")

# Payment Settings
MY_CARD = os.getenv("MY_CARD", "9860 0825 3462 9983")
MY_CARD_EXPIRY = os.getenv("MY_CARD_EXPIRY", "04/30")
SUBSCRIPTION_PRICE = 200000  # 200,000 so'm
