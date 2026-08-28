"""Foydalanuvchining oldingi buyurtmalari ro'yxati va ularning holati."""
from html import escape as _html_escape

from aiogram import Router, F
from aiogram.types import Message

import db
from handlers.catalog import format_price
from keyboards import BTN_ORDERS
from order_service import CUSTOMER_STATUS_LABELS

orders_router = Router()


@orders_router.message(F.text == BTN_ORDERS)
async def show_orders(message: Message):
    orders = await db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("Sizda hali buyurtmalar yo'q. Katalogdan mahsulot tanlab, birinchi buyurtmangizni bering!")
        return

    lines = ["📦 <b>Buyurtmalaringiz:</b>\n"]
    for order in orders:
        status_label = CUSTOMER_STATUS_LABELS.get(order["status"], order["status"])
        line = f"#{order['id']} — {format_price(order['total_price'])} so'm — {status_label}"
        # Muammo bo'lsa va admin sabab yozgan bo'lsa - mijozga shu yerda ham
        # ko'rsatamiz (admin_service.notify_customer_order_problem orqali
        # xabar sifatida ham yuboriladi, lekin bu yerda tarix ichida ham
        # ko'rinib turishi qulay).
        if order.get("problem_reason"):
            line += f"\n   ↳ Sabab: {_html_escape(order['problem_reason'])}"
        lines.append(line)
    await message.answer("\n".join(lines))
