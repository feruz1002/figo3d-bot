"""'Aloqa' bo'limi.

MUHIM: matn kodda QOTIB QOLMAGAN - Render'ning Environment Variables
bo'limidagi `CONTACT_INFO` o'zgaruvchisidan o'qiladi (xuddi avval Mini
App'ning "Aloqa" bo'limida ishlatilgani kabi) - shu bilan foydalanuvchi
buni o'zgartirish uchun kodga tegishi shart emas, faqat Render'da shu
o'zgaruvchini yangilab, qayta deploy qilsa kifoya."""
from aiogram import Router, F
from aiogram.types import Message

from config import CONTACT_INFO
from keyboards import BTN_CONTACT

contact_router = Router()


@contact_router.message(F.text == BTN_CONTACT)
async def show_contact(message: Message):
    await message.answer(f"☎️ <b>Aloqa</b>\n\n{CONTACT_INFO}")
