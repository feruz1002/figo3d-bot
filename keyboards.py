"""Bot tugmalari (klaviaturalar) shu yerda yig'ilgan.

DIQQAT (tugma o'lchami haqida): Telegram bot tugmalarining shrift/piksel
o'lchamini bot dasturi orqali o'zgartirib bo'lmaydi - bu Telegram ilovasining
o'zi tomonidan belgilanadi. Bot faqat tugmalarning QATORLARGA JOYLASHUVINI
belgilay oladi - shuning uchun bosh menyu 2 tadan qilib, ko'zga chiroyliroq
va tekis (kvadratsimon) ko'rinadigan qilib joylashtirilgan.
"""
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from config import WEBAPP_URL

# ---------- Asosiy menyu (pastdagi doimiy tugmalar) ----------

BTN_CATALOG = "🗂 Katalog"
BTN_CART = "🛒 Savat"
BTN_ORDERS = "📦 Buyurtmalarim"
BTN_PROFILE = "👤 Profil"
BTN_CONTACT = "☎️ Aloqa"
BTN_CUSTOM = "🎨 Shaxsiy buyurtma"

BTN_SKIP_PROMO = "➡️ O'tkazib yuborish"
BTN_CANCEL = "❌ Bekor qilish"
BTN_SKIP_PROOF = "📎 Skrinshotsiz yuborish"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    # 2 tadan qatorga - tekis, ko'zga yoqimli va baribir yetarlicha katta
    # (resize_keyboard=True Telegram'ga mavjud joyni to'liq egallashni aytadi)
    builder = ReplyKeyboardBuilder()
    if WEBAPP_URL:
        # Production'da (Render, https mavjud) "Katalog" haqiqiy veb-do'kon
        # (Mini App) sifatida ochiladi - rasm-kartochkalar, tab bo'limlar,
        # bosib tanlash. Mahalliy sinovda (https yo'q) avvalgi tugmali
        # ko'rinishga tushadi (pastdagi else).
        builder.row(
            KeyboardButton(text=BTN_CATALOG, web_app=WebAppInfo(url=WEBAPP_URL)),
            KeyboardButton(text=BTN_CART),
        )
    else:
        builder.row(KeyboardButton(text=BTN_CATALOG), KeyboardButton(text=BTN_CART))
    builder.row(KeyboardButton(text=BTN_ORDERS), KeyboardButton(text=BTN_PROFILE))
    builder.row(KeyboardButton(text=BTN_CUSTOM), KeyboardButton(text=BTN_CONTACT))
    return builder.as_markup(resize_keyboard=True)


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)
    )
    builder.row(KeyboardButton(text=BTN_CANCEL))
    return builder.as_markup(resize_keyboard=True)


def cancel_only_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_CANCEL))
    return builder.as_markup(resize_keyboard=True)


def skip_promo_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_SKIP_PROMO))
    builder.row(KeyboardButton(text=BTN_CANCEL))
    return builder.as_markup(resize_keyboard=True)


def skip_proof_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_SKIP_PROOF))
    builder.row(KeyboardButton(text=BTN_CANCEL))
    return builder.as_markup(resize_keyboard=True)


# ---------- Katalog uchun inline tugmalar ----------

def categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category, callback_data=f"cat:{category}")
    builder.adjust(1)
    return builder.as_markup()


def products_keyboard(category: str, products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        price_fmt = f"{product['price']:,}".replace(",", " ")
        builder.button(
            text=f"{product['name']} — {price_fmt} so'm",
            callback_data=f"prod:{product['id']}",
        )
    builder.button(text="⬅️ Bo'limlarga qaytish", callback_data="back_categories")
    builder.adjust(1)
    return builder.as_markup()


def product_detail_keyboard(
    product_id: int, category: str, has_reviews: bool = False, cart_qty: int = 0
) -> InlineKeyboardMarkup:
    add_text = "➕ Savatga qo'shish" if cart_qty == 0 else f"➕ Yana qo'shish (savatda: {cart_qty} ta)"
    builder = InlineKeyboardBuilder()
    builder.button(text=add_text, callback_data=f"add:{product_id}")
    builder.button(text="⭐ Baho berish", callback_data=f"review:{product_id}")
    if has_reviews:
        builder.button(text="💬 Sharhlarni ko'rish", callback_data=f"viewreviews:{product_id}")
    builder.button(text="⬅️ Ro'yxatga qaytish", callback_data=f"cat:{category}")
    builder.adjust(1)
    return builder.as_markup()


# ---------- Sharh (review) uchun inline tugmalar ----------

def rating_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for n in range(1, 6):
        builder.button(text="⭐" * n, callback_data=f"rate:{product_id}:{n}")
    builder.adjust(1)
    return builder.as_markup()


def skip_comment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Izohsiz saqlash", callback_data="skip_comment")
    builder.adjust(1)
    return builder.as_markup()


# ---------- Savat uchun inline tugmalar ----------

def cart_keyboard(cart_items: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in cart_items:
        product = item["product"]
        pid = product["id"]
        # Har bir mahsulot uchun: [➖] [N dona - nomi] [➕] bitta qatorda
        builder.row(
            InlineKeyboardButton(text="➖", callback_data=f"dec:{pid}"),
            InlineKeyboardButton(
                text=f"{item['quantity']} ta — {product['name']}", callback_data="noop"
            ),
            InlineKeyboardButton(text="➕", callback_data=f"inc:{pid}"),
        )
    if cart_items:
        builder.row(InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="checkout"))
        builder.row(InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="clear_cart"))
    return builder.as_markup()


def payment_choice_keyboard(balance: int, total: int, card_enabled: bool = False) -> InlineKeyboardMarkup:
    """Buyurtmani qanday to'lash: hamyondan (agar yetarli bo'lsa), Telegram
    ichida karta orqali (Click/Payme ulangan bo'lsa) yoki operator bilan."""
    builder = InlineKeyboardBuilder()
    if balance >= total and total > 0:
        builder.button(text="💰 Hamyondan to'lash", callback_data="confirm_balance")
    if card_enabled and total > 0:
        builder.button(text="💳 Karta orqali (Click/Payme)", callback_data="confirm_card")
    builder.button(text="💵 Naqd/karta (operator bilan)", callback_data="confirm_cash")
    builder.button(text="❌ Bekor qilish", callback_data="cancel_order")
    builder.adjust(1)
    return builder.as_markup()


def admin_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Admin/hamkorga yuboriladigan xabar ostidagi tugmalar."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Qabul qildim", callback_data=f"order_accept:{order_id}")
    builder.adjust(1)
    return builder.as_markup()


def custom_admin_keyboard(custom_order_id: int) -> InlineKeyboardMarkup:
    """Shaxsiy buyurtma haqidagi admin xabari ostidagi tugma."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Mijoz bilan bog'landim", callback_data=f"custom_contacted:{custom_order_id}"
    )
    builder.adjust(1)
    return builder.as_markup()


# ---------- Profil va hamyon uchun tugmalar ----------

def profile_choice_keyboard() -> InlineKeyboardMarkup:
    """Checkout boshida: o'zi uchunmi (saqlangan ma'lumot) yoki sovg'a/boshqa manzilgami."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🙋 O'zim uchun (saqlangan ma'lumot)", callback_data="use_saved_profile")
    builder.button(text="🎁 Sovg'a / boshqa manzil", callback_data="new_manual_profile")
    builder.adjust(1)
    return builder.as_markup()


def profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Hisobni to'ldirish", callback_data="topup_start")
    builder.button(text="✏️ Ma'lumotlarni yangilash", callback_data="edit_profile")
    builder.adjust(1)
    return builder.as_markup()


def topup_admin_keyboard(request_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"topup_approve:{request_id}")
    builder.button(text="❌ Rad etish", callback_data=f"topup_reject:{request_id}")
    builder.adjust(2)
    return builder.as_markup()
