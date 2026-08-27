"""Shaxsiy buyurtma: mijoz o'z rasmini yuboradi, undan noyob haykalcha/buyum
tayyorlashni so'raydi. Narx oldindan belgilanmagani uchun bu savat/checkout
oqimidan alohida - to'g'ridan-to'g'ri adminga (operatorga) forward qilinadi,
narx operator bilan kelishib olinadi."""
from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
from admin_notify import notify_admins
from handlers.states import CustomOrderStates
from keyboards import (
    BTN_CUSTOM,
    BTN_CANCEL,
    main_menu_keyboard,
    cancel_only_keyboard,
    contact_request_keyboard,
    custom_admin_keyboard,
)

custom_router = Router()


@custom_router.message(F.text == BTN_CUSTOM)
async def start_custom_order(message: Message, state: FSMContext):
    await state.set_state(CustomOrderStates.waiting_photo)
    await message.answer(
        "🎨 <b>Shaxsiy buyurtma</b>\n\n"
        "O'zingiz xohlagan rasmni yuboring (odam, uy hayvoni, logotip va h.k.) — "
        "hamkorlarimiz shu asosida noyob haykalcha yoki buyum tayyorlab berishadi.\n\n"
        "Rasmni shu yerga yuboring 👇",
        reply_markup=cancel_only_keyboard(),
    )


@custom_router.message(F.text == BTN_CANCEL, StateFilter(CustomOrderStates))
async def cancel_custom_order(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Shaxsiy buyurtma bekor qilindi.", reply_markup=main_menu_keyboard())


@custom_router.message(CustomOrderStates.waiting_photo, F.photo)
async def process_custom_photo(message: Message, state: FSMContext):
    # Eng katta o'lchamdagi versiyasini olamiz (ro'yxatning oxirgisi)
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    await state.set_state(CustomOrderStates.waiting_description)
    await message.answer(
        "Qanday ko'rinishda tayyorlashni xohlaysiz? (taxminiy o'lcham, rang, "
        "uslub va boshqa istaklaringizni yozing)",
        reply_markup=cancel_only_keyboard(),
    )


@custom_router.message(CustomOrderStates.waiting_photo)
async def process_custom_photo_invalid(message: Message):
    await message.answer("Iltimos, rasm (fotosurat) yuboring — fayl yoki hujjat emas.")


@custom_router.message(CustomOrderStates.waiting_description)
async def process_custom_description(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, matn ko'rinishida yozing.")
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(CustomOrderStates.waiting_name)
    await message.answer("Ism-familiyangizni yozing:", reply_markup=cancel_only_keyboard())


@custom_router.message(CustomOrderStates.waiting_name)
async def process_custom_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Iltimos, to'liq ismingizni matn ko'rinishida yozing.")
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(CustomOrderStates.waiting_phone)
    await message.answer(
        "Telefon raqamingizni yuboring — pastdagi tugmani bosing yoki qo'lda yozing:",
        reply_markup=contact_request_keyboard(),
    )


async def _ask_custom_address(message: Message, state: FSMContext):
    await state.set_state(CustomOrderStates.waiting_address)
    await message.answer(
        "Yetkazib berish manzilingizni yozing:", reply_markup=cancel_only_keyboard()
    )


@custom_router.message(CustomOrderStates.waiting_phone, F.contact)
async def process_custom_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await _ask_custom_address(message, state)


@custom_router.message(CustomOrderStates.waiting_phone, F.text)
async def process_custom_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 7:
        await message.answer("Telefon raqam noto'g'ri ko'rinmoqda, qaytadan urinib ko'ring.")
        return
    await state.update_data(phone=phone)
    await _ask_custom_address(message, state)


@custom_router.message(CustomOrderStates.waiting_address)
async def process_custom_address(message: Message, state: FSMContext, bot: Bot):
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("Iltimos, manzilni matn ko'rinishida yozing.")
        return

    data = await state.get_data()
    address = message.text.strip()

    custom_order_id = await db.create_custom_order(
        user_id=message.from_user.id,
        photo_file_id=data["photo_file_id"],
        description=data["description"],
        full_name=data["full_name"],
        phone=data["phone"],
        address=address,
    )
    await state.clear()

    await message.answer(
        f"✅ So'rovingiz qabul qilindi! Raqami: #{custom_order_id}\n\n"
        "Operatorimiz rasmingizni ko'rib chiqib, narxni kelishish uchun tez orada "
        "siz bilan bog'lanadi.",
        reply_markup=main_menu_keyboard(),
    )

    caption = (
        f"🎨 Yangi SHAXSIY buyurtma so'rovi #{custom_order_id}\n\n"
        f"Tavsif: {data['description']}\n\n"
        f"Ism: {data['full_name']}\n"
        f"Tel: {data['phone']}\n"
        f"Manzil: {address}\n\n"
        "Rasmni ko'rib, narxni kelishib, mijoz bilan bog'laning."
    )
    await notify_admins(
        bot,
        photo=data["photo_file_id"],
        caption=caption,
        reply_markup=custom_admin_keyboard(custom_order_id),
    )
