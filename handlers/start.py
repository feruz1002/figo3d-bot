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

    # MUHIM (foydalanuvchi so'rovi bilan qaytarildi): endi pastdagi chat
    # tugmalari HAR DOIM (production'da ham) ko'rsatiladi va BARCHA amal
    # (savat, buyurtma berish, profil, buyurtmalar, shaxsiy buyurtma,
    # aloqa) shular orqali ishlaydi - bu Mini App'ning ba'zan ishonchsiz
    # chiqadigan veb-ko'rinishiga qaraganda barqarorroq. "🛍 Do'kon" Mini
    # App tugmasi ham qoladi (mavjud bo'lsa) - u faqat mahsulotlarni
    # chiroyliroq ko'rish va savatga qo'shish uchun qulay muqobil.
    text = (
        "👋 <b>Assalomu alaykum, Figo3D ga xush kelibsiz!</b>\n\n"
        "Bu yerda siz 3D-print qilingan haykalcha, kalitcha va boshqa "
        "sovg'a buyumlarini tanlab, buyurtma qilishingiz mumkin.\n\n"
        "🗂 <b>Katalog</b> — mahsulotlarni ko'rish\n"
        "🛒 <b>Savat</b> — tanlagan mahsulotlaringiz va buyurtma berish\n"
        "📦 <b>Buyurtmalarim</b> — oldingi buyurtmalar holati\n"
        "👤 <b>Profil</b> — ma'lumotlaringiz va hamyon balansi\n"
        "🎨 <b>Shaxsiy buyurtma</b> — o'z rasmingizdan noyob buyum\n"
        "☎️ <b>Aloqa</b> — savol bo'lsa yozing\n\n"
    )
    if WEBAPP_URL:
        text += (
            "Shuningdek, xabar yozish maydoni yonidagi \"🛍 Do'kon\" tugmasi "
            "orqali mahsulotlarni veb-ko'rinishda ham ko'rishingiz mumkin.\n\n"
        )
    text += "Boshlash uchun pastdagi tugmalardan birini bosing 👇"
    await message.answer(
        text, reply_markup=main_menu_keyboard(is_admin=is_admin(message.from_user.id))
    )
