"""Buyurtma yaratish, to'lovni qo'llash va adminga xabar berish - bu mantiq
endi ham chatdagi buyurtma jarayoni (handlers/checkout.py), ham veb-do'kon
(Mini App, webapp_api.py) orqali buyurtma berishda BIR XIL ishlatiladi, shu
bilan ikkalasi doim izchil (bir xil qoidalar bilan) ishlaydi."""
import json

from aiogram import Bot
from aiogram.types import LabeledPrice

import db
from admin_notify import notify_admins
from config import ADMIN_IDS, PAYMENT_PROVIDER_TOKEN
from keyboards import admin_order_keyboard


def format_price(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


# holat matni, admin xabaridagi "to'lov usuli" qatori
PAYMENT_LABELS = {
    "balance": ("to'landi (hamyondan)", "💰 To'lov: hamyondan (to'langan)\n"),
    "cash": ("yangi", "💵 To'lov: naqd/karta (operator bilan)\n"),
    "card": ("to'lov kutilmoqda (karta)", "💳 To'lov: karta orqali (kutilmoqda)\n"),
    "card_paid": ("to'landi (karta)", "💳 To'lov: karta orqali (to'langan)\n"),
}


async def create_order_and_apply_payment(
    user_id: int,
    full_name: str,
    phone: str,
    address: str,
    promo_code: str | None,
    discount_amount: int,
    payment_method: str,
):
    """payment_method: "balance" | "cash" | "card".
    Qaytaradi: (order_id, "ok") muvaffaqiyatda, yoki (None, sabab) — sabab
    "empty_cart" yoki "insufficient_balance" bo'lishi mumkin.

    "card" uchun: buyurtma "to'lov kutilmoqda" holatida yaratiladi (savat
    shu zahoti tozalanadi) - to'lov muvaffaqiyatli bo'lganda uni chaqiruvchi
    keyinroq "to'landi" holatiga o'tkazadi (pastdagi mark_card_order_paid)."""
    cart = await db.get_cart(user_id)
    if not cart:
        return None, "empty_cart"

    subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart)
    total = max(subtotal - discount_amount, 0)

    if payment_method == "balance":
        balance = await db.get_balance(user_id)
        if balance < total:
            return None, "insufficient_balance"

    order_id = await db.create_order(
        user_id, full_name, phone, address,
        promo_code=promo_code, discount_amount=discount_amount,
    )

    if payment_method == "balance":
        await db.adjust_balance(user_id, -total)
        await db.update_order_status(order_id, PAYMENT_LABELS["balance"][0])
    elif payment_method == "card":
        await db.update_order_status(order_id, PAYMENT_LABELS["card"][0])
    # "cash": create_order() dan kelgan standart "yangi" holati yetarli

    await db.upsert_user_profile(user_id, full_name=full_name, phone=phone, address=address)
    return order_id, "ok"


async def mark_card_order_paid(order_id: int):
    await db.update_order_status(order_id, PAYMENT_LABELS["card_paid"][0])


async def create_card_invoice_link(bot: Bot, order_id: int, item_count: int, total: int) -> str:
    return await bot.create_invoice_link(
        title="Figo3D buyurtma",
        description=f"Buyurtma #{order_id} — {item_count} xil mahsulot, jami {format_price(total)} so'm",
        payload=f"order:{order_id}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="UZS",
        prices=[LabeledPrice(label="Buyurtma", amount=total * 100)],
    )


async def notify_customer_order_placed(bot: Bot, order_id: int):
    """Mini App orqali (chatga chiqmasdan) berilgan buyurtmalar uchun -
    mijozning o'ziga ham buyurtma qabul qilingani haqida alohida xabar
    yuboramiz. Bu ikki sabab bilan muhim: (1) Mini App ekrani yopilgach
    "buyurtma ketdimi-yo'qmi" degan noaniqlik qolmasin, (2) chatda doimiy
    yozib qoluvchi tasdiq/hujjat bo'lsin. Karta orqali to'langan
    buyurtmalar buni Telegram'ning o'z "successful_payment" xabari orqali
    allaqachon olishadi, shuning uchun bu funksiya faqat naqd/hamyon
    (cash/balance) orqali berilgan buyurtmalar uchun chaqiriladi."""
    order = await db.get_order(order_id)
    if not order:
        return
    try:
        await bot.send_message(
            order["user_id"],
            f"✅ Buyurtmangiz qabul qilindi! Buyurtma raqami: #{order_id}\n\n"
            f"💰 Jami: {format_price(order['total_price'])} so'm\n\n"
            "Tez orada operator siz bilan bog'lanadi. Holatini \"📦 "
            "Buyurtmalarim\" bo'limidan kuzatib borishingiz mumkin.",
        )
    except Exception:
        # Mijoz botni bloklagan yoki hali /start bosmagan bo'lishi mumkin -
        # bu holatda ham buyurtmaning o'zi bazada saqlanib qolaveradi.
        pass


async def notify_admin_new_order(bot: Bot, order_id: int, payment_method: str):
    """payment_method: "balance" | "cash" | "card" | "card_paid" (successful_payment kelganda).
    ADMIN_IDS ro'yxatidagi HAMMASIGA xabar yuboriladi (bir nechta admin
    bo'lishi mumkin)."""
    if not ADMIN_IDS:
        return
    order = await db.get_order(order_id)
    if not order:
        return

    items = json.loads(order["items_json"])
    items_text = "\n".join(f"• {i['name']} x{i['quantity']}" for i in items)
    discount_line = ""
    if order.get("promo_code"):
        discount_line = f"🏷 Promo: {order['promo_code']} (-{format_price(order['discount_amount'])} so'm)\n"
    _, payment_line = PAYMENT_LABELS.get(payment_method, ("", ""))
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
    await notify_admins(bot, text=admin_text, reply_markup=admin_order_keyboard(order_id))
