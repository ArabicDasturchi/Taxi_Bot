# Taxi Express Pro Bot 🚕

Professional, to'liq avtomatlashgan Taksi tizimi.

## Qanday Ishlatiladi?

1. `.env` faylini ochib, o'z ma'lumotlaringizni kiriting (`BOT_TOKEN` va qolganlar).
2. Tizim uchun kutubxonalarni o'rnating: `pip install -r requirements.txt`
3. Botni ishga tushiring: `python launcher.py`

## Xususiyatlar:
- **Admin Panel (`/admin`)**: Shofyorlarni boshqarish, to'lov tasdiqlash, va statistikani kuzatish. To'lov tasdiqlangandan so'ng u shofyorga "Avto Qidiruv" xizmatini yoqadi!
- **Haydovchi Bot**: Shofyor ro'yxatdan o'tadi, telefon raqamini tasdiqlaydi. 200 ming so'm to'lovni qiladi.
- **Background Worker**: Pyrogram va APScheduler yordamida har 5 daqiqada guruhlarga reklama tashlash hamda mijozlarni qidirib shofyorga yo'naltirish.
