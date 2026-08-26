"""Buyurtma berish jarayoni:
(saqlangan profil bo'lsa) o'zim uchun / sovg'a -> ism -> telefon -> manzil ->
promo -> tasdiqlash (hamyondan yoki naqd/karta) -> saqlash."""
import json

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
from config import ADMIN_CHAT_ID
from handlers.catalog import format_price
from handlers.states import OrderStates
from keyboards import (
    BTN_CANCEL,
    BTN_SKIP_PROMO,
    main_menu_keyboard,
    contact_request_keyboard,
    cancel_only_keyboard,
    payment_choice_keyboard,
    profile_choice_keyboard,
    admin_order_keyboard,
    skip_promo_keyboard,
)

checkout_router = Router()


def _has_complete_profile(profile: dict | None) -> bool:
    return bool(profile and profile.get("full_name") and profile.get("phone") and profile.get("address"))


@checkout_router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    cart = await db.get_cart(callback.from_user.id)
    if not cart:
        await callback.answer("Savatingiz bo'sh", show_alert=True)
        return

    profile = await db.get_user_profile(callback.from_user.id)
    if _has_complete_profile(profile):
        await callback.message.answer(
            "Saqlangan ma'lumotlaringiz bor:\n\n"
            f"👤 {profile['full_name']}\n"
            f"📱 {profile['phone']}\n"
            f"📍 {profile['address']}\n\n"
            "Shu buyurtma kimga: o'zingizgami yoki sovg'a/boshqa manzilgami?",
            reply_markup=profile_choice_keyboard(),
        )
    else:
        await state.set_state(OrderStates.waiting_name)
        await callback.message.answer(
            "Buyurtmani rasmiylashtirish uchun ism-familiyangizni yozib yuboring:",
            reply_markup=cancel_only_keyboard(),
        )
    await callback.answer()


@checkout_router.callback_query(F.data == "use_saved_profile")
async def use_saved_profile(callback: CallbackQuery, state: FSMContext):
    cart = await db.get_cart(callback.from_user.id)
    if not cart:
        await callback.answer("Savatingiz bo'sh", show_alert=True)
        return
    profile = await db.get_user_profile(callback.from_user.id)
    if not _has_complete_profile(profile):
        await callback.answer()
        await state.set_state(OrderStates.waiting_name)
        await callback.message.answer(
            "Ism-familiyangizni yozing:", reply_markup=cancel_only_keyboard()
        )
        return

    await state.update_data(
        full_name=profile["full_name"], phone=profile["phone"], address=profile["address"]
    )
    await state.set_state(OrderStates.waiting_promo)
    await callback.message.answer(
        "Agar promo-kodingiz bo'lsa, shu yerga yozing. Bo'lmasa pastdagi "
        "tugmani bosib davom eting:",
        reply_markup=skip_promo_keyboard(),
    )
    await callback.answer()


@checkout_router.callback_query(F.data == "new_manual_profile")
async def new_manual_profile(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.waiting_name)
    await callback.message.answer(
        "Qabul qiluvchining ism-familiyasini yozing:",
        reply_markup=cancel_only_keyboard(),
    )
    await callback.answer()


@checkout_router.message(F.text == BTN_CANCEL, StateFilter(OrderStates))
async def cancel_checkout(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Buyurtma berish bekor qilindi.", reply_markup=main_menu_keyboard())


@checkout_router.message(OrderStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Iltimos, to'liq ismingizni matn ko'rinishida yozing.")
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(OrderStates.waiting_phone)
    await message.answer(
        "Endi telefon raqamingizni yuboring — pastdagi tugmani bosing yoki qo'lda yozing:",
        reply_markup=contact_request_keyboard(),
    )


async def _ask_address(message: Message, state: FSMContext):
    await state.set_state(OrderStates.waiting_address)
    await message.answer(
        "Yetkazib berish manzilini (shahar, tuman, mo'ljal) yozing:",
        reply_markup=cancel_only_keyboard(),
    )


@checkout_router.message(OrderStates.waiting_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await _ask_address(message, state)


@checkout_router.message(OrderStates.waiting_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 7:
        await message.answer("Telefon raqam noto'g'ri ko'rinmoqda, qaytadan urinib ko'ring.")
        return
    await state.update_data(phone=phone)
    await _ask_address(message, state)


def _order_summary(data: dict, cart: list, subtotal: int, discount: int, balance: int) -> str:
    lines = ["📋 <b>Buyurtmangizni tekshiring:</b>\n"]
    for item in cart:
        product = item["product"]
        lines.append(f"• {product['name']} x{item['quantity']}")
    lines.append(f"\n💰 Mahsulotlar narxi: {format_price(subtotal)} so'm")
    total = max(subtotal - discount, 0)
    if discount:
        lines.append(f"🏷 Chegirma ({data.get('promo_code')}): -{format_price(discount)} so'm")
        lines.append(f"<b>Jami to'lanadi: {format_price(total)} so'm</b>")
    else:
        lines.append(f"<b>Jami: {format_price(total)} so'm</b>")
    lines.append(f"\n👤 Ism: {data['full_name']}")
    lines.append(f"📱 Telefon: {data['phone']}")
    lines.append(f"📍 Manzil: {data['address']}")
    lines.append(f"\n💳 Hamyon balansingiz: {format_price(balance)} so'm")
    lines.append("\nTo'lov usulini tanlang:")
    return "\n".join(lines)


@checkout_router.message(OrderStates.waiting_address)
async def process_address(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("Iltimos, manzilni matn ko'rinishida yozing.")
        return
    await state.update_data(address=message.text.strip())

    cart = await db.get_cart(message.from_user.id)
    if not cart:
        await state.clear()
        await message.answer("Savatingiz bo'sh qolgan, buyurtma bekor qilindi.", reply_markup=main_menu_keyboard())
        return

    await state.set_state(OrderStates.waiting_promo)
    await message.answer(
        "Agar promo-kodingiz bo'lsa, shu yerga yozing. Bo'lmasa pastdagi "
        "tugmani bosib davom eting:",
        reply_markup=skip_promo_keyboard(),
    )


async def _show_order_summary(message: Message, state: FSMContext, discount: int, promo_code: str | None):
    await state.update_data(discount=discount, promo_code=promo_code)
    data = await state.get_data()
    cart = await db.get_cart(message.from_user.id)
    if not cart:
        await state.clear()
        await message.answer("Savatingiz bo'sh qolgan, buyurtma bekor qilindi.", reply_markup=main_menu_keyboard())
        return

    subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart)
    total = max(subtotal - discount, 0)
    balance = await db.get_balance(message.from_user.id)
    await state.set_state(OrderStates.confirming)
    await message.answer(
        _order_summary(data, cart, subtotal, discount, balance),
        reply_markup=payment_choice_keyboard(balance, total),
    )


@checkout_router.message(OrderStates.waiting_promo, F.text == BTN_SKIP_PROMO)
async def skip_promo(message: Message, state: FSMContext):
    await _show_order_summary(message, state, discount=0, promo_code=None)


@checkout_router.message(OrderStates.waiting_promo, F.text)
async def process_promo(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    promo = await db.get_promo(code)

    if not promo:
        await message.answer(
            "❌ Bunday promo-kod topilmadi. Qaytadan urinib ko'ring yoki "
            f"\"{BTN_SKIP_PROMO}\" tugmasini bosing."
        )
        return
    if promo["max_uses"] is not None and promo["used_count"] >= promo["max_uses"]:
        await message.answer(
            f"❌ \"{code}\" promo-kodining ishlatilish limiti tugagan. "
            f"\"{BTN_SKIP_PROMO}\" tugmasini bosing."
        )
        return

    cart = await db.get_cart(message.from_user.id)
    subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart)
    discount = subtotal * promo["discount_percent"] // 100
    await message.answer(f"✅ Promo-kod qabul qilindi: -{promo['discount_percent']}%")
    await _show_order_summary(message, state, discount=discount, promo_code=code)


async def _finalize_order(callback: CallbackQuery, state: FSMContext, bot: Bot, paid_from_balance: bool):
    data = await state.get_data()
    cart = await db.get_cart(callback.from_user.id)
    if not cart:
        await state.clear()
        await callback.message.edit_text("Savatingiz bo'sh qolgan, buyurtma bekor qilindi.")
        await callback.message.answer("Bosh menyu:", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart)
    discount = data.get("discount", 0)
    total = max(subtotal - discount, 0)

    if paid_from_balance:
        balance = await db.get_balance(callback.from_user.id)
        if balance < total:
            await callback.answer("Hamyoningizda mablag' yetarli emas", show_alert=True)
            return

    order_id = await db.create_order(
        callback.from_user.id,
        data["full_name"],
        data["phone"],
        data["address"],
        promo_code=data.get("promo_code"),
        discount_amount=discount,
    )

    if paid_from_balance:
        await db.adjust_balance(callback.from_user.id, -total)
        await db.update_order_status(order_id, "to'landi (hamyondan)")

    # Keyingi safar qayta kiritmasligi uchun ma'lumotlarni saqlaymiz
    # (bu "o'zim uchun" bo'lmasa ham zarari yo'q - eng oxirgi kiritilgan
    # ma'lumot sifatida saqlanib qoladi, xohlasa Profil bo'limidan tahrirlaydi).
    await db.upsert_user_profile(
        callback.from_user.id,
        full_name=data["full_name"],
        phone=data["phone"],
        address=data["address"],
    )

    await state.clear()

    payment_note = (
        "💰 To'lov hamyoningizdan amalga oshirildi." if paid_from_balance
        else "Tez orada operator to'lov bo'yicha siz bilan bog'lanadi."
    )
    await callback.message.edit_text(
        f"✅ Buyurtmangiz qabul qilindi! Buyurtma raqami: #{order_id}\n\n{payment_note}"
    )
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu_keyboard())

    if ADMIN_CHAT_ID:
        order = await db.get_order(order_id)
        items = json.loads(order["items_json"])
        items_text = "\n".join(f"• {i['name']} x{i['quantity']}" for i in items)
        discount_line = ""
        if order.get("promo_code"):
            discount_line = f"🏷 Promo: {order['promo_code']} (-{format_price(order['discount_amount'])} so'm)\n"
        payment_line = (
            "💰 To'lov: hamyondan (to'langan)\n" if paid_from_balance
            else "💵 To'lov: naqd/karta (operator bilan)\n"
        )
        admin_text = (
            f"🆕 <b>Yangi buyurtma #{order_id}</b>\n\n"
            f"{items_text}\n\n"
            f"{discount_line}"
            f"{payment_line}"
            f"💰 Jami: {format_price(order['total_price'])} so'm\n\n"
            f"👤 {order['full_name']}\n"
            f"📱 {order['phone']}\n"
            f"📍 {order['address']}"
        )
        try:
            await bot.send_message(
                ADMIN_CHAT_ID, admin_text, reply_markup=admin_order_keyboard(order_id)
            )
        except Exception:
            # Admin hali botga /start bosmagan bo'lishi mumkin - bot unga yoza olmaydi.
            pass

    await callback.answer()


@checkout_router.callback_query(F.data == "confirm_balance", OrderStates.confirming)
async def confirm_balance(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await _finalize_order(callback, state, bot, paid_from_balance=True)


@checkout_router.callback_query(F.data == "confirm_cash", OrderStates.confirming)
async def confirm_cash(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await _finalize_order(callback, state, bot, paid_from_balance=False)


@checkout_router.callback_query(F.data == "cancel_order", OrderStates.confirming)
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.")
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu_keyboard())
    await callback.answer()
