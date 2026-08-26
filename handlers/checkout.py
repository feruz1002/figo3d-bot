"""Buyurtma berish jarayoni:
(saqlangan profil bo'lsa) o'zim uchun / sovg'a -> ism -> telefon -> manzil ->
promo -> tasdiqlash (hamyondan yoki naqd/karta) -> saqlash."""
import json

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

import db
from config import ADMIN_CHAT_ID, PAYMENT_PROVIDER_TOKEN
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
        reply_markup=payment_choice_keyboard(balance, total, card_enabled=bool(PAYMENT_PROVIDER_TOKEN)),
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


PAYMENT_LABELS = {
    "balance": ("to'landi (hamyondan)", "💰 To'lov: hamyondan (to'langan)\n"),
    "card": ("to'landi (karta)", "💳 To'lov: karta orqali (to'langan)\n"),
    "cash": ("yangi", "💵 To'lov: naqd/karta (operator bilan)\n"),
}


async def _create_order_from_state(user_id: int, state: FSMContext, payment_method: str):
    """Umumiy yadro: state'dagi ma'lumotlar asosida buyurtma yaratadi.
    payment_method: "balance" | "card" | "cash".
    Qaytaradi: (order_id, "ok") muvaffaqiyatda, yoki (None, sabab) muvaffaqiyatsizlikda
    ("empty_cart" yoki "insufficient_balance")."""
    data = await state.get_data()
    cart = await db.get_cart(user_id)
    if not cart:
        return None, "empty_cart"

    subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart)
    discount = data.get("discount", 0)
    total = max(subtotal - discount, 0)

    if payment_method == "balance":
        balance = await db.get_balance(user_id)
        if balance < total:
            return None, "insufficient_balance"

    order_id = await db.create_order(
        user_id,
        data["full_name"],
        data["phone"],
        data["address"],
        promo_code=data.get("promo_code"),
        discount_amount=discount,
    )

    if payment_method == "balance":
        await db.adjust_balance(user_id, -total)
    status, _ = PAYMENT_LABELS[payment_method]
    await db.update_order_status(order_id, status)

    # Keyingi safar qayta kiritmasligi uchun ma'lumotlarni saqlaymiz
    # (bu "o'zim uchun" bo'lmasa ham zarari yo'q - eng oxirgi kiritilgan
    # ma'lumot sifatida saqlanib qoladi, xohlasa Profil bo'limidan tahrirlaydi).
    await db.upsert_user_profile(
        user_id, full_name=data["full_name"], phone=data["phone"], address=data["address"]
    )

    return order_id, "ok"


async def _notify_admin_new_order(bot: Bot, order_id: int, payment_method: str):
    if not ADMIN_CHAT_ID:
        return
    order = await db.get_order(order_id)
    items = json.loads(order["items_json"])
    items_text = "\n".join(f"• {i['name']} x{i['quantity']}" for i in items)
    discount_line = ""
    if order.get("promo_code"):
        discount_line = f"🏷 Promo: {order['promo_code']} (-{format_price(order['discount_amount'])} so'm)\n"
    _, payment_line = PAYMENT_LABELS[payment_method]
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
        await bot.send_message(ADMIN_CHAT_ID, admin_text, reply_markup=admin_order_keyboard(order_id))
    except Exception:
        # Admin hali botga /start bosmagan bo'lishi mumkin - bot unga yoza olmaydi.
        pass


async def _finalize_order(callback: CallbackQuery, state: FSMContext, bot: Bot, payment_method: str):
    order_id, reason = await _create_order_from_state(callback.from_user.id, state, payment_method)

    if reason == "insufficient_balance":
        await callback.answer("Hamyoningizda mablag' yetarli emas", show_alert=True)
        return
    if reason == "empty_cart" or order_id is None:
        await state.clear()
        await callback.message.edit_text("Savatingiz bo'sh qolgan, buyurtma bekor qilindi.")
        await callback.message.answer("Bosh menyu:", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    await state.clear()

    payment_note = {
        "balance": "💰 To'lov hamyoningizdan amalga oshirildi.",
        "cash": "Tez orada operator to'lov bo'yicha siz bilan bog'lanadi.",
    }[payment_method]
    await callback.message.edit_text(
        f"✅ Buyurtmangiz qabul qilindi! Buyurtma raqami: #{order_id}\n\n{payment_note}"
    )
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu_keyboard())
    await _notify_admin_new_order(bot, order_id, payment_method)
    await callback.answer()


@checkout_router.callback_query(F.data == "confirm_balance", OrderStates.confirming)
async def confirm_balance(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await _finalize_order(callback, state, bot, payment_method="balance")


@checkout_router.callback_query(F.data == "confirm_cash", OrderStates.confirming)
async def confirm_cash(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await _finalize_order(callback, state, bot, payment_method="cash")


@checkout_router.callback_query(F.data == "confirm_card", OrderStates.confirming)
async def confirm_card(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not PAYMENT_PROVIDER_TOKEN:
        await callback.answer("Karta orqali to'lov hali sozlanmagan", show_alert=True)
        return

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
    if total <= 0:
        await callback.answer("Jami summa 0, karta orqali to'lash shart emas", show_alert=True)
        return

    await callback.answer()
    try:
        # UZS Telegram Payments'da "bo'linmaydigan" valyuta emas, shuning
        # uchun summa 100 ga ko'paytiriladi (Telegram talabi).
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title="Figo3D buyurtma",
            description=f"{len(cart)} xil mahsulot, jami {format_price(total)} so'm",
            payload=f"figo3d_order:{callback.from_user.id}",
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="UZS",
            prices=[LabeledPrice(label="Buyurtma", amount=total * 100)],
        )
    except Exception:
        await callback.message.answer(
            "❌ To'lov oynasini ochib bo'lmadi. Iltimos, boshqa to'lov usulini tanlang."
        )


@checkout_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    # Telegram shu javobni 10 soniya ichida kutadi - shuning uchun qo'shimcha
    # tekshiruvsiz darhol tasdiqlaymiz (savat/manzil allaqachon tekshirilgan).
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@checkout_router.message(F.successful_payment, OrderStates.confirming)
async def process_successful_payment(message: Message, state: FSMContext, bot: Bot):
    order_id, reason = await _create_order_from_state(message.from_user.id, state, "card")

    if order_id is None:
        # To'lov Telegram tomonidan allaqachon qabul qilingan, lekin savat
        # bo'sh qolgan bo'lsa (kamdan-kam holat) - adminga xabar berib qo'yamiz,
        # pul mijozdan olingan, operator qo'lda hal qiladi.
        await message.answer(
            "✅ To'lovingiz qabul qilindi, lekin buyurtmani avtomatik "
            "rasmiylashtirishda muammo yuz berdi. Operatorimiz tez orada siz "
            "bilan bog'lanadi.",
            reply_markup=main_menu_keyboard(),
        )
        if ADMIN_CHAT_ID:
            try:
                await bot.send_message(
                    ADMIN_CHAT_ID,
                    f"⚠️ Mijoz {message.from_user.id} to'lov qildi, lekin buyurtma "
                    f"avtomatik yaratilmadi (sabab: {reason}). Tekshiring!",
                )
            except Exception:
                pass
        await state.clear()
        return

    await state.clear()
    await message.answer(
        f"✅ To'lov qabul qilindi! Buyurtmangiz raqami: #{order_id}\n\n"
        "💳 To'lov karta orqali amalga oshirildi.",
        reply_markup=main_menu_keyboard(),
    )
    await _notify_admin_new_order(bot, order_id, "card")


@checkout_router.callback_query(F.data == "cancel_order", OrderStates.confirming)
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.")
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu_keyboard())
    await callback.answer()
