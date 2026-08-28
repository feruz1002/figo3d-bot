"""Admin uchun mahsulot boshqaruvi: qo'shish, ro'yxatini ko'rish, o'chirish.

Bu endi katalogni o'zgartirishning YAGONA va TAVSIYA ETILGAN usuli - products.py
faylini qo'lda tahrirlash, GitHub'ga yuklash va qayta deploy qilish SHART EMAS.
Mahsulot va uning rasmlari to'g'ridan-to'g'ri shu bot orqali bazaga saqlanadi va
darhol (qayta ishga tushirmasdan) katalogda ko'rinadi.

Buyruq: /admin (faqat config.ADMIN_IDS ro'yxatidagilar uchun ishlaydi)."""
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, KeyboardButton, Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import db
from config import ADMIN_PANEL_URL, is_admin as _is_admin
from handlers.catalog import format_price
from handlers.states import AdminProductStates
from keyboards import BTN_ADMIN, BTN_CANCEL, cancel_only_keyboard, main_menu_keyboard

admin_products_router = Router()

BTN_DONE_PHOTOS = "✅ Rasmlar tayyor"
BTN_SKIP_VIDEO = "➡️ Videosiz davom etish"


def _admin_panel_keyboard():
    builder = InlineKeyboardBuilder()
    if ADMIN_PANEL_URL:
        # Buyurtmalar, hisob to'ldirish so'rovlari va mahsulotlarni bitta
        # chiroyli veb-sahifadan boshqarish - faqat Render'da (https bilan)
        # ishlaydi, chatdagi eski usul (pastdagi ikkita tugma) hamon ishlayveradi.
        builder.row(InlineKeyboardButton(text="🖥 Boshqaruv panelini ochish", web_app=WebAppInfo(url=ADMIN_PANEL_URL)))
    builder.button(text="➕ Yangi mahsulot qo'shish", callback_data="admin_add_product")
    builder.button(text="📋 Mahsulotlar ro'yxati", callback_data="admin_list_products")
    builder.adjust(1)
    return builder.as_markup()


def _photos_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_DONE_PHOTOS))
    builder.row(KeyboardButton(text=BTN_CANCEL))
    return builder.as_markup(resize_keyboard=True)


def _video_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_SKIP_VIDEO))
    builder.row(KeyboardButton(text=BTN_CANCEL))
    return builder.as_markup(resize_keyboard=True)


@admin_products_router.message(Command("admin"))
@admin_products_router.message(F.text == BTN_ADMIN)
async def admin_panel(message: Message):
    # MUHIM: /admin buyrug'i BILAN BIRGA endi pastdagi "🛠 Admin panel"
    # tugmasi orqali ham ochiladi (faqat is_admin bo'lganlarga - main_menu_keyboard
    # shu tugmani faqat admin uchun qo'shadi). Oddiy mijoz shu matnni yozib
    # yuborsa ham (masalan tasodifan) - pastdagi tekshiruv uni to'xtatadi.
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "🛠 <b>Admin panel</b>\n\nBu yerdan mahsulot qo'shishingiz yoki "
        "o'chirishingiz mumkin - kod yozish yoki qayta deploy qilish shart emas.",
        reply_markup=_admin_panel_keyboard(),
    )


# ---------- Mahsulot qo'shish ----------

@admin_products_router.callback_query(F.data == "admin_add_product")
async def start_add_product(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    categories = await db.get_categories()
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.button(text=c, callback_data=f"admin_cat:{c}")
    builder.button(text="✏️ Yangi bo'lim nomi", callback_data="admin_cat_new")
    builder.adjust(1)

    await state.set_state(AdminProductStates.waiting_category)
    await callback.message.answer(
        "Qaysi bo'limga tegishli? Mavjudlaridan tanlang, yoki yangi bo'lim "
        "nomini yozish uchun pastdagi tugmani bosing:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@admin_products_router.callback_query(F.data.startswith("admin_cat:"), AdminProductStates.waiting_category)
async def choose_existing_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":", 1)[1]
    await state.update_data(category=category)
    await state.set_state(AdminProductStates.waiting_name)
    await callback.message.answer(
        f"Bo'lim: <b>{category}</b>\n\nMahsulot nomini yozing:",
        reply_markup=cancel_only_keyboard(),
    )
    await callback.answer()


@admin_products_router.callback_query(F.data == "admin_cat_new", AdminProductStates.waiting_category)
async def choose_new_category(callback: CallbackQuery):
    await callback.message.answer(
        "Yangi bo'lim nomini yozing (masalan: \"Sovg'alar\"):",
        reply_markup=cancel_only_keyboard(),
    )
    await callback.answer()


@admin_products_router.message(F.text == BTN_CANCEL, StateFilter(AdminProductStates))
async def cancel_add_product(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_keyboard(is_admin=True))


@admin_products_router.message(AdminProductStates.waiting_category)
async def process_category_text(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Iltimos, bo'lim nomini matn ko'rinishida yozing.")
        return
    await state.update_data(category=message.text.strip())
    await state.set_state(AdminProductStates.waiting_name)
    await message.answer("Mahsulot nomini yozing:", reply_markup=cancel_only_keyboard())


@admin_products_router.message(AdminProductStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Iltimos, nomini matn ko'rinishida yozing.")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminProductStates.waiting_description)
    await message.answer("Qisqacha tavsif yozing:", reply_markup=cancel_only_keyboard())


@admin_products_router.message(AdminProductStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, matn ko'rinishida yozing.")
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminProductStates.waiting_price)
    await message.answer(
        "Narxini so'mda, raqam bilan yozing (masalan: 120000):",
        reply_markup=cancel_only_keyboard(),
    )


@admin_products_router.message(AdminProductStates.waiting_price)
async def process_price(message: Message, state: FSMContext):
    text = (message.text or "").replace(" ", "").replace("so'm", "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Iltimos, faqat musbat son kiriting (masalan: 120000).")
        return

    await state.update_data(price=int(text), photos=[])
    await state.set_state(AdminProductStates.waiting_photos)
    await message.answer(
        "Endi mahsulot rasmlarini birma-bir yuboring (kamida 1 ta tavsiya "
        f"etiladi, bir nechtasini ham yuborishingiz mumkin). Tugatgach "
        f"\"{BTN_DONE_PHOTOS}\" tugmasini bosing:",
        reply_markup=_photos_keyboard(),
    )


@admin_products_router.message(AdminProductStates.waiting_photos, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(
        f"✅ Qabul qilindi ({len(photos)} ta rasm). Yana yuborishingiz mumkin, "
        f"yoki \"{BTN_DONE_PHOTOS}\" tugmasini bosing."
    )


@admin_products_router.message(AdminProductStates.waiting_photos, F.text == BTN_DONE_PHOTOS)
async def finish_photos(message: Message, state: FSMContext):
    await state.set_state(AdminProductStates.waiting_video)
    await message.answer(
        "Agar mahsulotni aylantirib olingan qisqa VIDEO bo'lsa yuboring "
        "(GIF emas, video fayl sifatida yuboring), bo'lmasa pastdagi tugmani "
        f"bosib o'tkazib yuboring:",
        reply_markup=_video_keyboard(),
    )


@admin_products_router.message(AdminProductStates.waiting_photos)
async def process_photos_invalid(message: Message):
    await message.answer(
        f"Iltimos, rasm yuboring, yoki \"{BTN_DONE_PHOTOS}\" tugmasini bosing."
    )


async def _show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    video_label = "bor" if data.get("video") else "yo'q"
    text = (
        "📋 <b>Yangi mahsulotni tekshiring:</b>\n\n"
        f"Bo'lim: {data['category']}\n"
        f"Nomi: {data['name']}\n"
        f"Tavsif: {data['description']}\n"
        f"Narxi: {format_price(data['price'])} so'm\n"
        f"Rasmlar soni: {len(data.get('photos', []))}\n"
        f"Video: {video_label}\n\n"
        "Saqlaymizmi?"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Saqlash", callback_data="admin_save_product")
    builder.button(text="❌ Bekor qilish", callback_data="admin_cancel_product")
    builder.adjust(1)
    await state.set_state(AdminProductStates.confirming)
    await message.answer(text, reply_markup=builder.as_markup())


@admin_products_router.message(AdminProductStates.waiting_video, F.video)
async def process_video(message: Message, state: FSMContext):
    await state.update_data(video=message.video.file_id)
    await _show_confirm(message, state)


@admin_products_router.message(AdminProductStates.waiting_video, F.text == BTN_SKIP_VIDEO)
async def skip_video(message: Message, state: FSMContext):
    await _show_confirm(message, state)


@admin_products_router.message(AdminProductStates.waiting_video)
async def process_video_invalid(message: Message):
    await message.answer(
        f"Iltimos, video yuboring (fayl sifatida, GIF emas), yoki "
        f"\"{BTN_SKIP_VIDEO}\" tugmasini bosing."
    )


@admin_products_router.callback_query(F.data == "admin_cancel_product", AdminProductStates.confirming)
async def cancel_confirm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu_keyboard(is_admin=True))
    await callback.answer()


@admin_products_router.callback_query(F.data == "admin_save_product", AdminProductStates.confirming)
async def save_product(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = await db.create_product(
        data["category"], data["name"], data["description"], data["price"]
    )
    for i, file_id in enumerate(data.get("photos", [])):
        await db.add_product_photo(product_id, file_id, position=i)
    if data.get("video"):
        await db.set_product_video(product_id, data["video"])
    await state.clear()

    await callback.message.edit_text(
        f"✅ Mahsulot qo'shildi! (#{product_id})\n\n"
        "Endi u katalogda darhol ko'rinadi — hech narsa qayta deploy qilish shart emas."
    )
    await callback.message.answer("Bosh menyu:", reply_markup=main_menu_keyboard(is_admin=True))
    await callback.answer()


# ---------- Ro'yxat / o'chirish ----------

@admin_products_router.callback_query(F.data == "admin_list_products")
async def list_products(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    products = await db.list_active_products()
    if not products:
        await callback.answer("Hozircha mahsulot yo'q", show_alert=True)
        return

    await callback.message.answer("📋 <b>Mahsulotlar:</b>")
    for p in products:
        builder = InlineKeyboardBuilder()
        builder.button(text="🗑 O'chirish", callback_data=f"admin_del:{p['id']}")
        builder.adjust(1)
        await callback.message.answer(
            f"#{p['id']} <b>{p['name']}</b> — {p['category']} — {format_price(p['price'])} so'm",
            reply_markup=builder.as_markup(),
        )
    await callback.answer()


@admin_products_router.callback_query(F.data.startswith("admin_del:"))
async def confirm_delete(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    product_id = int(callback.data.split(":", 1)[1])
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, o'chirish", callback_data=f"admin_del_yes:{product_id}")
    builder.button(text="❌ Yo'q", callback_data=f"admin_del_no:{product_id}")
    builder.adjust(1)
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback.answer()


@admin_products_router.callback_query(F.data.startswith("admin_del_yes:"))
async def do_delete(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    product_id = int(callback.data.split(":", 1)[1])
    await db.deactivate_product(product_id)
    await callback.message.edit_text((callback.message.text or "") + "\n\n🗑 O'chirildi")
    await callback.answer("O'chirildi")


@admin_products_router.callback_query(F.data.startswith("admin_del_no:"))
async def cancel_delete(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 O'chirish", callback_data=f"admin_del:{product_id}")
    builder.adjust(1)
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback.answer("Bekor qilindi")
