"""
Bot sozlamalari shu yerdan o'qiladi.
Barcha maxfiy ma'lumotlar (token va h.k.) kod ichida emas, ".env" faylida yoki
Render'ning "Environment" bo'limida saqlanadi - bu xavfsizlik uchun muhim.
"""
import os
from dotenv import load_dotenv

# Mahalliy kompyuterda ishlaganda ".env" faylidagi qiymatlarni o'qiydi.
# Render'da bu fayl bo'lmaydi, lekin muammo emas - Render o'z Environment
# sozlamalaridan to'g'ridan-to'g'ri o'qib beradi.
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi! .env faylini tekshiring "
        "(yoki Render'da Environment Variables bo'limiga qo'shganingizni tekshiring)."
    )

# Buyurtma xabarlari yuboriladigan admin ID (majburiy emas, lekin tavsiya etiladi)
_admin_raw = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_CHAT_ID = int(_admin_raw) if _admin_raw else None

# Render avtomatik beradigan tashqi manzil (masalan: https://figo3d.onrender.com)
# Mahalliy kompyuterda bu bo'sh bo'ladi -> bot polling rejimida ishlaydi.
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip()

# Render har doim shu portni beradi; mahalliy sinovda ishlatilmaydi
PORT = int(os.getenv("PORT", "8080"))

# Ma'lumotlar bazasi fayli (savat va buyurtmalar shu yerda saqlanadi)
DB_PATH = os.getenv("DB_PATH", "figo3d.db")

# Hisobni to'ldirish (hamyon) uchun mijozga ko'rsatiladigan to'lov rekvizitlari
# (masalan karta raqamingiz). Render'ning Environment Variables bo'limida
# PAYMENT_INFO nomi bilan qo'shing - aks holda quyidagi standart matn ko'rsatiladi.
PAYMENT_INFO = os.getenv(
    "PAYMENT_INFO",
    "To'lov rekvizitlari hali sozlanmagan. Admin: buni Render'ning Environment "
    "Variables bo'limida PAYMENT_INFO nomi bilan qo'shing (masalan: "
    "\"Karta: 8600 1234 5678 9012 - F. Familiya\").",
)

# Telegram to'lov tizimi (Click/Payme) uchun "provider token".
# @BotFather -> /mybots -> Figo 3D -> Payments bo'limidan Click (yoki Payme)'ni
# ulaganingizdan so'ng oladigan tokenni shu yerga (Render Environment
# Variables'ga PAYMENT_PROVIDER_TOKEN nomi bilan) qo'yasiz. Token yo'q ekan -
# muammo emas: "Karta orqali to'lash" tugmasi shunchaki ko'rinmaydi, mijozlar
# avvalgidek hamyon yoki naqd/karta (operator bilan) orqali to'laydi.
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "").strip() or None
