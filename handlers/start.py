"""/start buyrug'i va botning birinchi salomlashuvi."""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import db
from config import WEBAPP_URL, is_admin
from keyboards import main_menu_keyboard

start_router = Router()


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    # Statistika uchun ("📊 Statistika" bo'limidagi "botni ko'rgan odamlar
    # soni") - hali birorta buyurtma bermagan bo'lsa ham, shu yerda "ko'rildi"
    # deb belgilanadi. Profil ma'lumotlariga (ism/telefon/manzil) tegmaydi.
    await db.touch_user_seen(message.from_user.id)
    # 28-avgust: admin panelidagi "Mijoz bilan bog'lanish" havolasi uchun
    # (tg://user?id=... Mini App ichida bloklangani aniqlandi - db.py'dagi
    # remember_username izohiga qarang).
    await db.remember_username(message.from_user.id, message.from_user.username)

    # MUHIM (29-avgust, foydalanuvchi so'rovi bilan YANA O'ZGARDI): endi
    # oddiy mijozlarga pastdagi chat tugmalari UMUMAN ko'rsatilmaydi
    # (keyboards.py'dagi main_menu_keyboard izohiga qarang) - katalog,
    # savat, buyurtma berish, profil, buyurtmalarim, shaxsiy buyurtma va
    # aloqa endi FAQAT "🛍 Do'kon" Mini App ichida ishlaydi. Shuning uchun
    # salomlashuv matni ham shu Mini App tugmasiga yo'naltiradi.
    admin_user = is_admin(message.from_user.id)
    text = (
        "👋 <b>Assalomu alaykum, Figo3D ga xush kelibsiz!</b>\n\n"
        "Bu yerda siz 3D-print qilingan haykalcha, kalitcha va boshqa "
        "sovg'a buyumlarini tanlab, buyurtma qilishingiz mumkin.\n\n"
    )
    if WEBAPP_URL:
        text += (
            "Boshlash uchun xabar yozish maydoni yonidagi \"🛍 Do'kon\" "
            "tugmasini bosing 👇\n\n"
            "U yerda: mahsulotlar katalogi, savat, buyurtma berish va "
            "to'lov, profil va hamyon, buyurtmalaringiz holati, shaxsiy "
            "buyurtma va yangiliklar — barchasi bitta joyda."
        )
    else:
        # Xavfsizlik uchun zaxira matn (WEBAPP_URL sozlanmagan holatlarda,
        # masalan lokal test muhitida) - production'da (Render'da) bu
        # doim sozlangan bo'ladi, shuning uchun bu shoxobcha amalda
        # ko'rinmasligi kerak.
        text += (
            "⚠️ Hozircha veb-do'kon vaqtincha ishlamayapti. Iltimos, "
            "birozdan so'ng qaytadan urinib ko'ring yoki operatorga yozing."
        )
    if admin_user:
        text += "\n\n🛠 Admin sifatida pastdagi \"Admin panel\" tugmasidan foydalanishingiz mumkin."
    await message.answer(
        text, reply_markup=main_menu_keyboard(is_admin=admin_user)
    )
