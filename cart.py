"""Savatni ko'rish, miqdorni +/- qilish, savatni tozalash."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

import db
from keyboards import BTN_CART, cart_keyboard
from handlers.catalog import format_price

cart_router = Router()


def format_cart_text(cart: list) -> str:
    if not cart:
        return "🛒 Savatingiz bo'sh.\n\nKatalogdan mahsulot tanlab qo'shing."

    lines = ["🛒 <b>Savatingiz:</b>\n"]
    total = 0
    for item in cart:
        product = item["product"]
        subtotal = product["price"] * item["quantity"]
        total += subtotal
        lines.append(
            f"• {product['name']} x{item['quantity']} = {format_price(subtotal)} so'm"
        )
    lines.append(f"\n💰 <b>Jami: {format_price(total)} so'm</b>")
    return "\n".join(lines)


async def _refresh_cart_message(callback: CallbackQuery, cart: list):
    try:
        await callback.message.edit_text(format_cart_text(cart), reply_markup=cart_keyboard(cart))
    except Exception:
        # Matn o'zgarmagan bo'lsa Telegram xato qaytaradi - buni e'tiborsiz qoldiramiz
        pass


@cart_router.message(F.text == BTN_CART)
async def show_cart(message: Message):
    cart = await db.get_cart(message.from_user.id)
    await message.answer(format_cart_text(cart), reply_markup=cart_keyboard(cart))


@cart_router.callback_query(F.data.startswith("inc:"))
async def increase_item(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    await db.add_to_cart(callback.from_user.id, product_id, quantity=1)
    cart = await db.get_cart(callback.from_user.id)
    await _refresh_cart_message(callback, cart)
    await callback.answer("➕ Qo'shildi")


@cart_router.callback_query(F.data.startswith("dec:"))
async def decrease_item(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    new_qty = await db.decrease_cart_item(callback.from_user.id, product_id, amount=1)
    cart = await db.get_cart(callback.from_user.id)
    await _refresh_cart_message(callback, cart)
    await callback.answer("O'chirildi" if new_qty == 0 else "➖ Kamaytirildi")


@cart_router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    # Savatdagi "N ta - nomi" yozuvi bosilganda hech narsa qilmaymiz,
    # faqat Telegram'ning "yuklanmoqda" belgisini yo'qotish uchun javob beramiz.
    await callback.answer()


@cart_router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery):
    await db.clear_cart(callback.from_user.id)
    await callback.message.edit_text(format_cart_text([]), reply_markup=cart_keyboard([]))
    await callback.answer("Savat tozalandi")
