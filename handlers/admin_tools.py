"""Admin uchun kichik yordamchi vosita: mahsulotga rasm qo'shish uchun kerak
bo'ladigan "file_id"ni topib berish. Boshqa hech qanday tashqi botga hojat
qolmaydi - shu bot o'ziga yuborilgan rasmning file_id'sini qaytarib beradi.

Bu FAQAT admin (ADMIN_CHAT_ID) uchun ishlaydi va FAQAT hech qanday jarayon
(masalan checkout yoki shaxsiy buyurtma) davom etmayotgan bo'lsa ishga tushadi -
shu sababli oddiy mijozlarga yoki boshqa jarayonlarga xalaqit bermaydi."""
from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_CHAT_ID

admin_tools_router = Router()


@admin_tools_router.message(F.photo)
async def send_file_id(message: Message, state: FSMContext):
    if ADMIN_CHAT_ID is None or message.from_user.id != ADMIN_CHAT_ID:
        # Admin bo'lmasa - boshqa routerlar (masalan shaxsiy buyurtma oqimi) shu
        # rasmni o'zi ko'rib chiqsin, biz aralashmaymiz.
        raise SkipHandler()

    current_state = await state.get_state()
    if current_state is not None:
        # Admin biror jarayon (masalan o'zi shaxsiy buyurtma sinab ko'rayotgan)
        # ichida bo'lsa, o'sha jarayon o'z ishini davom ettirsin.
        raise SkipHandler()

    file_id = message.photo[-1].file_id
    await message.answer(
        "📎 Ushbu rasmning file_id'si:\n\n"
        f"<code>{file_id}</code>\n\n"
        "Ustiga bosib nusxalang (copy), so'ng <code>products.py</code> faylida "
        "kerakli mahsulotning <code>\"photos\"</code> ro'yxatiga shu qatorni "
        "qo'shing (tirnoqlar bilan)."
    )
