"""Profil sahifasi: ism/telefon/manzilni ko'rish-tahrirlash, hamyon balansi
va hisobni to'ldirish so'rovi (admin tasdig'i bilan)."""
from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
from admin_notify import notify_admins
from config import PAYMENT_INFO
from handlers.catalog import format_price
from handlers.states import ProfileEditStates, TopupStates
from keyboards import (
    BTN_PROFILE,
    BTN_CANCEL,
    BTN_SKIP_PROOF,
    main_menu_keyboard,
    cancel_only_keyboard,
    skip_proof_keyboard,
    profile_keyboard,
    topup_admin_keyboard,
)

profile_router = Router()


def _profile_text(profile: dict | None) -> str:
    name = profile["full_name"] if profile and profile["full_name"] else "—"
    phone = profile["phone"] if profile and profile["phone"] else "—"
    address = profile["address"] if profile and profile["address"] else "—"
    balance = profile["balance"] if profile else 0
    return (
        "👤 <b>Profil</b>\n\n"
        f"Ism: {name}\n"
        f"Telefon: {phone}\n"
        f"Manzil: {address}\n\n"
        f"💰 <b>Balans: {format_price(balance)} so'm</b>"
    )


@profile_router.message(F.text == BTN_PROFILE)
async def show_profile(message: Message):
    profile = await db.get_user_profile(message.from_user.id)
    await message.answer(_profile_text(profile), reply_markup=profile_keyboard())


# ---------- Ma'lumotlarni tahrirlash ----------

@profile_router.callback_query(F.data == "edit_profile")
async def start_edit_profile(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditStates.waiting_name)
    await callback.message.answer("Ism-familiyangizni yozing:", reply_markup=cancel_only_keyboard())
    await callback.answer()


@profile_router.message(F.text == BTN_CANCEL, StateFilter(ProfileEditStates))
async def cancel_edit_profile(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_keyboard())


@profile_router.message(ProfileEditStates.waiting_name)
async def edit_profile_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Iltimos, to'liq ismingizni matn ko'rinishida yozing.")
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(ProfileEditStates.waiting_phone)
    await message.answer("Telefon raqamingizni yozing:", reply_markup=cancel_only_keyboard())


@profile_router.message(ProfileEditStates.waiting_phone)
async def edit_profile_phone(message: Message, state: FSMContext):
    phone = (message.contact.phone_number if message.contact else message.text or "").strip()
    if len(phone) < 7:
        await message.answer("Telefon raqam noto'g'ri ko'rinmoqda, qaytadan urinib ko'ring.")
        return
    await state.update_data(phone=phone)
    await state.set_state(ProfileEditStates.waiting_address)
    await message.answer("Manzilingizni yozing:", reply_markup=cancel_only_keyboard())


@profile_router.message(ProfileEditStates.waiting_address)
async def edit_profile_address(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("Iltimos, manzilni matn ko'rinishida yozing.")
        return
    data = await state.get_data()
    await db.upsert_user_profile(
        message.from_user.id,
        full_name=data["full_name"],
        phone=data["phone"],
        address=message.text.strip(),
    )
    await state.clear()
    profile = await db.get_user_profile(message.from_user.id)
    await message.answer("✅ Ma'lumotlaringiz yangilandi!", reply_markup=main_menu_keyboard())
    await message.answer(_profile_text(profile), reply_markup=profile_keyboard())


# ---------- Hisobni to'ldirish ----------

@profile_router.callback_query(F.data == "topup_start")
async def start_topup(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TopupStates.waiting_amount)
    await callback.message.answer(
        "Necha so'mlik hisobingizni to'ldirmoqchisiz? Raqam bilan yozing (masalan: 100000):",
        reply_markup=cancel_only_keyboard(),
    )
    await callback.answer()


@profile_router.message(F.text == BTN_CANCEL, StateFilter(TopupStates))
async def cancel_topup(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_keyboard())


@profile_router.message(TopupStates.waiting_amount)
async def process_topup_amount(message: Message, state: FSMContext):
    text = (message.text or "").replace(" ", "").replace("so'm", "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Iltimos, faqat musbat son kiriting (masalan: 100000).")
        return

    amount = int(text)
    await state.update_data(amount=amount)
    await state.set_state(TopupStates.waiting_proof)
    await message.answer(
        f"💳 <b>To'lov rekvizitlari:</b>\n{PAYMENT_INFO}\n\n"
        f"{format_price(amount)} so'mni shu rekvizitga o'tkazgandan so'ng, "
        "chekning skrinshotini shu yerga yuboring. Agar hozircha skrinshotingiz "
        "bo'lmasa, pastdagi tugmani bosib ham davom etishingiz mumkin — "
        "operator tekshirib, tasdiqlaydi.",
        reply_markup=skip_proof_keyboard(),
    )


async def _submit_topup_request(message: Message, state: FSMContext, bot: Bot, screenshot_file_id: str | None):
    data = await state.get_data()
    amount = data["amount"]
    request_id = await db.create_topup_request(message.from_user.id, amount, screenshot_file_id)
    await state.clear()

    await message.answer(
        f"✅ So'rovingiz (#{request_id}) yuborildi. Operator tasdiqlagach, "
        f"{format_price(amount)} so'm hamyoningizga qo'shiladi.",
        reply_markup=main_menu_keyboard(),
    )

    caption = (
        f"💰 Yangi hisob to'ldirish so'rovi #{request_id}\n\n"
        f"Foydalanuvchi ID: {message.from_user.id}\n"
        f"Summasi: {format_price(amount)} so'm"
    )
    if screenshot_file_id:
        await notify_admins(
            bot, photo=screenshot_file_id, caption=caption,
            reply_markup=topup_admin_keyboard(request_id),
        )
    else:
        await notify_admins(
            bot, text=caption + "\n\n(Skrinshot yuborilmagan)",
            reply_markup=topup_admin_keyboard(request_id),
        )


@profile_router.message(TopupStates.waiting_proof, F.photo)
async def process_topup_proof(message: Message, state: FSMContext, bot: Bot):
    await _submit_topup_request(message, state, bot, message.photo[-1].file_id)


@profile_router.message(TopupStates.waiting_proof, F.text == BTN_SKIP_PROOF)
async def skip_topup_proof(message: Message, state: FSMContext, bot: Bot):
    await _submit_topup_request(message, state, bot, None)


@profile_router.message(TopupStates.waiting_proof)
async def process_topup_proof_invalid(message: Message):
    await message.answer(
        f"Iltimos, chekning skrinshotini (rasm) yuboring, yoki \"{BTN_SKIP_PROOF}\" tugmasini bosing."
    )
