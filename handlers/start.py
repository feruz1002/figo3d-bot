"""/start buyrug'i va botning birinchi salomlashuvi."""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import main_menu_keyboard

start_router = Router()


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "👋 <b>Assalomu alaykum, Figo3D ga xush kelibsiz!</b>\n\n"
        "Bu yerda siz 3D-print qilingan haykalcha, kalitcha va boshqa "
        "sovg'a buyumlarini tanlab, buyurtma qilishingiz mumkin.\n\n"
        "🗂 <b>Katalog</b> — mahsulotlarni ko'rish\n"
        "🛒 <b>Savat</b> — tanlagan mahsulotlaringiz\n"
        "📦 <b>Buyurtmalarim</b> — oldingi buyurtmalar holati\n"
        "☎️ <b>Aloqa</b> — savol bo'lsa yozing\n\n"
        "Boshlash uchun pastdagi tugmalardan birini bosing 👇"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())
