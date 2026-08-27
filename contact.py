"""'Aloqa' bo'limi - hozircha oddiy matn, keyinchalik jonli operator/FAQ qo'shish mumkin."""
from aiogram import Router, F
from aiogram.types import Message

from keyboards import BTN_CONTACT

contact_router = Router()


@contact_router.message(F.text == BTN_CONTACT)
async def show_contact(message: Message):
    await message.answer(
        "☎️ Savol yoki takliflaringiz bo'lsa, shu yerga yozib qoldiring — tez orada javob beramiz.\n\n"
        "Yoki to'g'ridan-to'g'ri: @sizning_username (buni o'zingizning shaxsiy "
        "Telegram foydalanuvchi nomingizga almashtiring, config.py yoki shu faylda)."
    )
