"""Katalogni ko'rsatish: bo'limlar -> mahsulotlar -> mahsulot tafsiloti."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

import db
from keyboards import (
    BTN_CATALOG,
    categories_keyboard,
    products_keyboard,
    product_detail_keyboard,
)
from products import get_products_by_category, get_product_by_id

catalog_router = Router()


def format_price(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


@catalog_router.message(F.text == BTN_CATALOG)
async def show_categories(message: Message):
    await message.answer("Qaysi bo'limni ko'rmoqchisiz?", reply_markup=categories_keyboard())


@catalog_router.callback_query(F.data == "back_categories")
async def back_to_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "Qaysi bo'limni ko'rmoqchisiz?", reply_markup=categories_keyboard()
    )
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("cat:"))
async def show_products(callback: CallbackQuery):
    category = callback.data.split(":", 1)[1]
    products = get_products_by_category(category)
    if not products:
        await callback.answer("Bu bo'limda hozircha mahsulot yo'q", show_alert=True)
        return
    await callback.message.edit_text(
        f"<b>{category}</b>\n\nMahsulotni tanlang:",
        reply_markup=products_keyboard(category),
    )
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("prod:"))
async def show_product(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    product = get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    text = (
        f"<b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 Narxi: {format_price(product['price'])} so'm"
    )
    kb = product_detail_keyboard(product_id, product["category"])

    if product.get("photo"):
        # Rasm bo'lsa - eski matnli xabarni o'chirib, rasm bilan qayta yuboramiz
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product["photo"], caption=text, reply_markup=kb
        )
    else:
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("add:"))
async def add_to_cart_handler(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    await db.add_to_cart(callback.from_user.id, product_id)
    await callback.answer("✅ Savatga qo'shildi!")
