"""Katalogni ko'rsatish: bo'limlar -> (bor bo'lsa) kichik bo'limlar -> mahsulotlar -> mahsulot tafsiloti."""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo

import db
from keyboards import (
    BTN_CATALOG,
    categories_keyboard,
    subcategories_keyboard,
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


async def _show_products_list(callback: CallbackQuery, category: str, subcategory: str | None):
    products = await db.get_products_by_category(category, subcategory=subcategory)
    if not products:
        await callback.answer("Bu bo'limda hozircha mahsulot yo'q", show_alert=True)
        return
    title = f"<b>{category}</b>" + (f" — {subcategory}" if subcategory else "")
    await _safe_edit(
        callback, f"{title}\n\nMahsulotni tanlang:", products_keyboard(category, products, subcategory)
    )
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("cat:"))
async def show_category(callback: CallbackQuery):
    """Bo'lim bosilganda: agar ichida kichik bo'limlar bo'lsa - avval
    ularning ro'yxati ko'rsatiladi; bo'lmasa - to'g'ridan-to'g'ri
    mahsulotlar ro'yxati (eski xatti-harakat)."""
    category = callback.data.split(":", 1)[1]
    subcategories = await db.get_subcategories(category)
    if subcategories:
        await _safe_edit(
            callback,
            f"<b>{category}</b>\n\nQaysi kichik bo'limni ko'rmoqchisiz?",
            subcategories_keyboard(category, subcategories),
        )
        await callback.answer()
        return
    await _show_products_list(callback, category, subcategory=None)


@catalog_router.callback_query(F.data.startswith("subcat:"))
async def show_subcategory_products(callback: CallbackQuery):
    _, category, subcategory = callback.data.split(":", 2)
    await _show_products_list(callback, category, subcategory=subcategory)


@catalog_router.callback_query(F.data.startswith("catall:"))
async def show_all_in_category(callback: CallbackQuery):
    """Kichik bo'limlar ro'yxatidagi "📦 Hammasini ko'rish" - shu bo'limdagi
    BARCHA mahsulotlarni (kichik bo'limi bor-yo'qligidan qat'i nazar) birga
    ko'rsatadi."""
    category = callback.data.split(":", 1)[1]
    await _show_products_list(callback, category, subcategory=None)


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
    kb = product_detail_keyboard(product_id, has_reviews=review_count > 0, cart_qty=cart_qty)

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


@catalog_router.callback_query(F.data.startswith("backto:"))
async def back_to_product_list(callback: CallbackQuery):
    """Mahsulot tafsilotidagi "⬅️ Ro'yxatga qaytish" - mahsulotning o'zi
    (kichik bo'limi bor-yo'qligi) orqali qaysi ro'yxatga tegishli ekanini
    server tomonda aniqlaydi va o'sha yerga qaytaradi."""
    product_id = int(callback.data.split(":", 1)[1])
    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return
    await _show_products_list(callback, product["category"], subcategory=product.get("subcategory"))


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
    kb = product_detail_keyboard(product_id, has_reviews=review_count > 0, cart_qty=new_qty)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass

    await callback.answer(f"✅ Savatga qo'shildi! Savatda: {new_qty} ta")
