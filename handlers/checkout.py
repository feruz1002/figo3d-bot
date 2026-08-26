"""Buyurtma berish jarayoni: ism -> telefon -> manzil -> tasdiqlash -> saqlash."""
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
    main_menu_keyboard,
    contact_request_keyboard,
    cancel_only_keyboard,
    confirm_order_keyboard,
    admin_order_keyboard,
    skip_promo_keyboard,
    BTN_SKIP_PROMO,
)

checkout_router = Router()


@checkout_router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    cart = await db.get_cart(callback.from_user.id)
    if not cart:
        await callback.answer("Savatingiz bo'sh", show_alert=True)
        return
    await state.set_state(OrderStates.waiting_name)
    await callback.message.answer(
        "Buyurtmani rasmiylashtirish uchun ism-familiyangizni yozib yuboring:",
        reply_markup=cancel_only_keyboard(),
    )
    await callback.answer()


@checkout_router.message(F.text == "❌ Bekor qilish", StateFilter(OrderStates))
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
        "Yetkazib berish manzilingizni (shahar, tuman, mo'ljal) yozing:",
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


def _order_summary(data: dict, cart: list, subtotal: int, discount: int) -> str:
    lines = ["📋 <b>Buyurtmangizni tekshiring:</b>\n"]
    for item in cart:
        product = item["product"]
        lines.append(f"• {product['name']} x{item['quantity']}")
    lines.append(f"\n💰 Mahsulotlar narxi: {format_price(subtotal)} so'm")
    if discount:
        lines.append(f"🏷 Chegirma ({data.get('promo_code')}): -{format_price(discount)} so'm")
        lines.append(f"<b>Jami to'lanadi: {format_price(subtotal - discount)} so'm</b>")
    else:
        lines.append(f"<b>Jami: {format_price(subtotal)} so'm</b>")
    lines.append(f"\n👤 Ism: {data['full_name']}")
    lines.append(f"📱 Telefon: {data['phone']}")
    lines.append(f"📍 Manzil: {data['address']}")
    lines.append(
        "\nTasdiqlasangiz, buyurtmangiz qabul qilinadi va operator to'lov "
        "bo'yicha tez orada siz bilan bog'lanadi."
    )
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
    await state.set_state(OrderStates.confirming)
    await message.answer(
        _order_summary(data, cart, subtotal, discount),
        reply_markup=confirm_order_keyboard(),
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


@checkout_router.callback_query(F.data == "confirm_order", OrderStates.confirming)
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = await db.create_order(
        callback.from_user.id,
        data["full_name"],
        data["phone"],
        data["address"],
        promo_code=data.get("promo_code"),
        discount_amount=data.get("discount", 0),
    )
    await state.clear()

    await callback.message.edit_text(
        f"✅ Buyurtmangiz qabul qilindi! Buyurtma raqami: #{order_id}\n\n"
        "Tez orada operator siz bilan bog'lanadi."
    )
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu_keyboard())

    if ADMIN_CHAT_ID:
        order = await db.get_order(order_id)
        items = json.loads(order["items_json"])
        items_text = "\n".join(f"• {i['name']} x{i['quantity']}" for i in items)
        discount_line = ""
        if order.get("promo_code"):
            discount_line = f"🏷 Promo: {order['promo_code']} (-{format_price(order['discount_amount'])} so'm)\n"
        admin_text = (
            f"🆕 <b>Yangi buyurtma #{order_id}</b>\n\n"
            f"{items_text}\n\n"
            f"{discount_line}"
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


@checkout_router.callback_query(F.data == "cancel_order", OrderStates.confirming)
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.")
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu_keyboard())
    await callback.answer()
