"""
Muhim himoya: agar foydalanuvchi biror jarayon o'rtasida (masalan, buyurtma
uchun manzil yozayotganda) pastdagi asosiy menyu tugmalaridan birini bossa,
bu matn xato ravishda o'sha jarayonning ma'lumoti sifatida saqlanib qolmasligi
kerak (masalan "🗂 Katalog" degan so'z manzil sifatida saqlanib qolishi mumkin edi).

Bu router ENG BIRINCHI bo'lib ro'yxatdan o'tkaziladi (handlers/__init__.py'da):
u har doim menyu tugmasi bosilganda avval joriy holatni (agar bo'lsa) tozalaydi,
so'ngra SkipHandler orqali ishni haqiqiy menyu funksiyasiga (masalan katalogni
ko'rsatish) o'tkazib beradi.
"""
from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards import (
    BTN_ADMIN,
    BTN_CATALOG,
    BTN_CART,
    BTN_ORDERS,
    BTN_PROFILE,
    BTN_CONTACT,
    BTN_CUSTOM,
)

menu_guard_router = Router()

_MENU_BUTTON_TEXTS = {
    BTN_CATALOG, BTN_CART, BTN_ORDERS, BTN_PROFILE, BTN_CONTACT, BTN_CUSTOM, BTN_ADMIN,
}


@menu_guard_router.message(F.text.in_(_MENU_BUTTON_TEXTS))
async def clear_state_before_menu_action(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    # Xabarni "ishlatilgan" deb hisoblamaymiz - keyingi mos router
    # (masalan catalog_router) shu matnni o'zi qayta ko'rib, kerakli menyuni ochsin.
    raise SkipHandler()
