"""Foydalanuvchining oldingi buyurtmalari ro'yxati va ularning holati."""
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
        lines.append(
            f"#{order['id']} — {format_price(order['total_price'])} so'm — {status_label}"
        )
    await message.answer("\n".join(lines))
