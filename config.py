"""
Bot sozlamalari shu yerdan o'qiladi.
Barcha maxfiy ma'lumotlar (token va h.k.) kod ichida emas, ".env" faylida yoki
Render'ning "Environment" bo'limida saqlanadi - bu xavfsizlik uchun muhim.
"""
import hashlib
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

# Buyurtma xabarlari yuboriladigan va /admin buyrug'i hamda admin veb-paneliga
# kira oladigan odam(lar). Endi BIR NECHTA odamga ruxsat berish mumkin
# (masalan siz + 3D-print hamkoringiz) - Render'ning Environment Variables
# bo'limida ADMIN_IDS nomi bilan vergul orqali ajratilgan ID'lar ro'yxatini
# qo'shing (masalan: "123456789,987654321"). Eski ADMIN_CHAT_ID (bitta ID)
# hamon ishlayveradi - ikkalasi ham qo'shilib, umumiy ro'yxat hosil bo'ladi,
# shuning uchun avvalgi sozlamangizni o'zgartirish shart emas.
_admin_raw = os.getenv("ADMIN_CHAT_ID", "").strip()
_admin_ids_raw = os.getenv("ADMIN_IDS", "").strip()
_admin_ids_set = set()
if _admin_raw:
    _admin_ids_set.add(int(_admin_raw))
for _part in _admin_ids_raw.split(","):
    _part = _part.strip()
    if _part:
        _admin_ids_set.add(int(_part))
ADMIN_IDS = sorted(_admin_ids_set)

# Orqaga moslik uchun: ba'zi eski kod qismlari yagona "birinchi admin" ID
# raqamini kutadi (masalan buyurtma tasdiqlash xabari ostidagi tugma h.k.).
ADMIN_CHAT_ID = ADMIN_IDS[0] if ADMIN_IDS else None


def is_admin(user_id: int) -> bool:
    """Shu Telegram ID admin (yoki ruxsat etilgan hamkor) ro'yxatidami?"""
    return user_id in ADMIN_IDS

# Render avtomatik beradigan tashqi manzil (masalan: https://figo3d.onrender.com)
# Mahalliy kompyuterda bu bo'sh bo'ladi -> bot polling rejimida ishlaydi.
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip()

# MUHIM (29-avgust, "eski mahsulotlar ko'rinmayapti" muammosiga javoban):
# Telegram (ayniqsa Desktop, Windows'da) Mini App sahifasini juda "yopishqoq"
# keshlaydi - hatto webapp_api.py'dagi "no-cache" sarlavhalari bo'lsada,
# ba'zan eski (deploy qilinganidan OLDINGI) HTML/JS nusxasini ko'rsatishda
# davom etadi, chunki WebView sahifani manzil (URL) bo'yicha keshlaydi. Buni
# oldini olish uchun manzilga fayl mazmuniga qarab hisoblangan "?v=..."
# parametrini qo'shamiz - fayl har o'zgarganda (har yangi deploy'da) manzil
# ham o'zgaradi, shuning uchun Telegram uni "yangi sahifa" deb hisoblab,
# eski keshdan emas, serverdan qayta yuklaydi. (Server tomonda "/webapp" va
# "/admin-panel" yo'llari so'rov parametriga qaramaydi - shuning uchun bu
# xavfsiz, aiohttp uni e'tiborsiz qoldiradi.)
def _asset_version(*relative_parts: str) -> str:
    _path = os.path.join(os.path.dirname(os.path.abspath(__file__)), *relative_parts)
    try:
        with open(_path, "rb") as _f:
            return hashlib.sha256(_f.read()).hexdigest()[:10]
    except OSError:
        return "0"


# Veb-do'kon (Telegram Mini App) manzili. Faqat Render'da (webhook rejimida,
# ya'ni haqiqiy https manzil mavjud bo'lganda) ishlaydi - Telegram Mini App
# tugmasi https talab qiladi. Mahalliy sinovda bu None bo'ladi va bot
# avvalgi (tugmali) katalog ko'rinishiga tushadi.
WEBAPP_URL = (
    RENDER_EXTERNAL_URL.rstrip("/") + "/webapp?v=" + _asset_version("webapp", "index.html")
) if RENDER_EXTERNAL_URL else None

# Admin boshqaruv paneli (Mini App) manzili - xuddi WEBAPP_URL kabi, faqat
# Render'da (https bilan) ishlaydi. Kirish config.ADMIN_IDS ro'yxati orqali
# cheklanadi (webapp_auth.py + admin_webapp_api.py'ga qarang).
ADMIN_PANEL_URL = (
    RENDER_EXTERNAL_URL.rstrip("/") + "/admin-panel?v=" + _asset_version("webapp", "admin.html")
) if RENDER_EXTERNAL_URL else None

# Render har doim shu portni beradi; mahalliy sinovda ishlatilmaydi
PORT = int(os.getenv("PORT", "8080"))

# Ma'lumotlar bazasi fayli - bu doim mahalliy nusxa (tezkor o'qish/yozish
# uchun), pastdagi Turso sozlansa esa har yozuvdan keyin avtomatik ravishda
# doimiy (Render diskiga bog'liq bo'lmagan) bulutga ham nusxalanadi.
DB_PATH = os.getenv("DB_PATH", "figo3d.db")

# Turso (bepul, doimiy SQLite-mos bulut baza) - Render'ning bepul diski
# vaqti-vaqti bilan tozalanib turishi mumkinligi uchun (masalan uzoq vaqt
# ishlatilmay qolgach), buyurtmalar/hamyon/mahsulotlar YO'QOLIB QOLMASLIGI
# uchun qo'shildi. Sozlash: turso.tech saytida bepul akkaunt oching, yangi
# baza yarating, undan "Database URL" va "Auth Token" oling, Render'ning
# Environment Variables bo'limiga TURSO_DATABASE_URL va TURSO_AUTH_TOKEN
# nomlari bilan qo'shing. Ikkalasi ham bo'sh bo'lsa - muammo emas, bot
# avvalgidek faqat mahalliy fayl bilan ishlayveradi (lekin Render diski
# tozalansa, ma'lumot yo'qolish xavfi qoladi).
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "").strip() or None
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip() or None

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

# "🎯 Vazifalar" bo'limida yuborilgan skrinshotlarni SUN'IY INTELLEKT
# (Claude) yordamida oldindan baholash uchun (29-avgust) - MAJBURIY EMAS:
# bo'sh qoldirilsa, hamma vazifa skrinshoti avvalgidek FAQAT admin
# tomonidan qo'lda tekshiriladi. Kalitni console.anthropic.com'da bepul
# ro'yxatdan o'tib, "Get API keys" bo'limidan olasiz (sk-ant-... bilan
# boshlanadi), Render'ning Environment Variables bo'limiga
# ANTHROPIC_API_KEY nomi bilan qo'shing. Bundan tashqari admin panelning
# "🎯 Vazifalar" bo'limidagi "🤖 AI tekshiruvi" tugmasi orqali istalgan
# vaqt YOQIB/O'CHIRIB turish mumkin (kalit bo'lsa ham) - shu bilan siz
# nazoratni to'liq qo'lda saqlaysiz.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip() or None
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001").strip()

# Click.uz orqali hamyonni AVTOMATIK to'ldirish (4-sentabr) - mijoz
# to'lagach, balans operator kutmasdan darhol qo'shiladi. Click bilan
# shartnoma tuzganingizdan so'ng beriladigan 4 ta qiymatni Render'ning
# Environment Variables bo'limiga QUYIDAGI NOMLAR bilan qo'shing (hech
# qachon bu qiymatlarni chatda yoki kodda YOZMANG - faqat Render sozlamalarida):
#   CLICK_SERVICE_ID       - Click bergan "Service ID"
#   CLICK_MERCHANT_ID      - Click bergan "Merchant ID"
#   CLICK_SECRET_KEY       - Click bergan maxfiy kalit ("Secret Key")
#   CLICK_MERCHANT_USER_ID - Click bergan "Merchant user ID"
# To'rttasi ham to'ldirilmaguncha bu funksiya O'CHIQ turadi - mijozlarga
# "Click orqali" tugmasi ko'rinmaydi, hamyonni faqat bank kartasi
# usulida (skrinshot yuborib) to'ldirish imkoniyati qoladi (avvalgidek).
CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "").strip() or None
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "").strip() or None
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "").strip() or None
CLICK_MERCHANT_USER_ID = os.getenv("CLICK_MERCHANT_USER_ID", "").strip() or None

# "☎️ Aloqa" tugmasida mijozlarga ko'rsatiladigan matn (chatda).
# Render'ning Environment Variables bo'limida CONTACT_INFO nomi bilan
# qo'shing - masalan: "@figo3d_support yoki +998 90 123 45 67".
CONTACT_INFO = os.getenv(
    "CONTACT_INFO",
    "Savol yoki takliflaringiz bo'lsa yozing: @sizning_username\n\n"
    "(Admin: buni Render'ning Environment Variables bo'limida CONTACT_INFO "
    "nomi bilan o'zingizning haqiqiy aloqa ma'lumotingizga almashtiring.)",
)
