"""Bot tugmalari (klaviaturalar) shu yerda yig'ilgan."""
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from products import get_categories, get_products_by_category

# ---------- Asosiy menyu (pastdagi doimiy tugmalar) ----------

BTN_CATALOG = "🗂 Katalog"
BTN_CART = "🛒 Savat"
BTN_ORDERS = "📦 Buyurtmalarim"
BTN_CONTACT = "☎️ Aloqa"
BTN_CUSTOM = "🎨 Shaxsiy buyurtma"

BTN_SKIP_PROMO = "➡️ O'tkazib yuborish"
BTN_CANCEL = "❌ Bekor qilish"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_CATALOG), KeyboardButton(text=BTN_CART))
    builder.row(KeyboardButton(text=BTN_ORDERS), KeyboardButton(text=BTN_CONTACT))
    builder.row(KeyboardButton(text=BTN_CUSTOM))
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


# ---------- Katalog uchun inline tugmalar ----------

def categories_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in get_categories():
        builder.button(text=category, callback_data=f"cat:{category}")
    builder.adjust(2)
    return builder.as_markup()


def products_keyboard(category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in get_products_by_category(category):
        price_fmt = f"{product['price']:,}".replace(",", " ")
        builder.button(
            text=f"{product['name']} — {price_fmt} so'm",
            callback_data=f"prod:{product['id']}",
        )
    builder.button(text="⬅️ Bo'limlarga qaytish", callback_data="back_categories")
    builder.adjust(1)
    return builder.as_markup()


def product_detail_keyboard(
    product_id: int, category: str, has_reviews: bool = False
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Savatga qo'shish", callback_data=f"add:{product_id}")
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
        builder.button(
            text=f"❌ {product['name']} ({item['quantity']} dona)",
            callback_data=f"remove:{product['id']}",
        )
    if cart_items:
        builder.button(text="✅ Buyurtma berish", callback_data="checkout")
        builder.button(text="🗑 Savatni tozalash", callback_data="clear_cart")
    builder.adjust(1)
    return builder.as_markup()


def confirm_order_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash va yuborish", callback_data="confirm_order")
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
