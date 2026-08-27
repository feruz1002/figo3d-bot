"""Katalogni ko'rsatish: bo'limlar -> mahsulotlar -> mahsulot tafsiloti."""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo

import db
from keyboards import (
    BTN_CATALOG,
    categories_keyboard,
    products_keyboard,
    product_detail_keyboard,
)

catalog_router = Router()


def format_price(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


async def _safe_edit(callback: CallbackQuery, text: str, kb):
    """Xabarni joyida tahrirlashga urinadi; agar bu xabar rasm/video bo'lsa
    (ustiga matn yozib bo'lmaydi), uni o'chirib, o'rniga yangi matnli xabar yuboradi."""
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=kb)


@catalog_router.message(F.text == BTN_CATALOG)
async def show_categories(message: Message):
    categories = await db.get_categories()
    if not categories:
        await message.answer("Hozircha katalogda mahsulot yo'q. Tez orada qo'shiladi!")
        return
    await message.answer("Qaysi bo'limni ko'rmoqchisiz?", reply_markup=categories_keyboard(categories))


@catalog_router.callback_query(F.data == "back_categories")
async def back_to_categories(callback: CallbackQuery):
    categories = await db.get_categories()
    await _safe_edit(callback, "Qaysi bo'limni ko'rmoqchisiz?", categories_keyboard(categories))
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("cat:"))
async def show_products(callback: CallbackQuery):
    category = callback.data.split(":", 1)[1]
    products = await db.get_products_by_category(category)
    if not products:
        await callback.answer("Bu bo'limda hozircha mahsulot yo'q", show_alert=True)
        return
    await _safe_edit(
        callback, f"<b>{category}</b>\n\nMahsulotni tanlang:", products_keyboard(category, products)
    )
    await callback.answer()


def _rating_line(avg_rating: float, review_count: int) -> str:
    if review_count == 0:
        return "☆ Hali sharh yo'q — birinchi bo'lib baho bering!"
    stars = "⭐" * round(avg_rating)
    return f"{stars} {avg_rating} ({review_count} ta sharh)"


@catalog_router.callback_query(F.data.startswith("prod:"))
async def show_product(callback: CallbackQuery, bot: Bot):
    product_id = int(callback.data.split(":", 1)[1])
    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    avg_rating, review_count = await db.get_product_rating(product_id)
    cart_qty = await db.get_cart_item_quantity(callback.from_user.id, product_id)
    text = (
        f"<b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 Narxi: {format_price(product['price'])} so'm\n"
        f"{_rating_line(avg_rating, review_count)}"
    )
    kb = product_detail_keyboard(
        product_id, product["category"], has_reviews=review_count > 0, cart_qty=cart_qty
    )

    photos = product.get("photos") or []
    video = product.get("video")
    media_count = len(photos) + (1 if video else 0)

    if media_count == 0:
        # Rasm/video yo'q - xabarni joyida tahrirlaymiz (yangi xabar yaratmaymiz)
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        return

    await callback.message.delete()

    if media_count == 1:
        # Bitta rasm YOKI bitta video - izoh (caption) va tugmalar bilan birga yuboramiz
        if photos:
            await callback.message.answer_photo(photo=photos[0], caption=text, reply_markup=kb)
        else:
            await callback.message.answer_video(video=video, caption=text, reply_markup=kb)
    else:
        # Bir nechta rasm/video - albom (media group) sifatida yuboriladi.
        # DIQQAT: Telegram albomga tugma (reply_markup) qo'yishga ruxsat bermaydi,
        # shuning uchun albomdan keyin alohida matnli xabar + tugmalar yuboramiz.
        media_group = []
        for i, photo in enumerate(photos):
            media_group.append(InputMediaPhoto(media=photo, caption=text if i == 0 else None))
        if video:
            media_group.append(InputMediaVideo(media=video))
        await bot.send_media_group(chat_id=callback.message.chat.id, media=media_group)
        await callback.message.answer("👆 Mahsulot rasmlari", reply_markup=kb)

    await callback.answer()


@catalog_router.callback_query(F.data.startswith("add:"))
async def add_to_cart_handler(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    await db.add_to_cart(callback.from_user.id, product_id)
    new_qty = await db.get_cart_item_quantity(callback.from_user.id, product_id)

    # Tugmani darhol yangilaymiz - shu bilan foydalanuvchi savatga qo'shilganini
    # yozuv o'zgarganidan darrov ko'radi (masalan "savatda: 2 ta" bo'lib qoladi).
    _, review_count = await db.get_product_rating(product_id)
    kb = product_detail_keyboard(
        product_id, product["category"], has_reviews=review_count > 0, cart_qty=new_qty
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass

    await callback.answer(f"✅ Savatga qo'shildi! Savatda: {new_qty} ta")
