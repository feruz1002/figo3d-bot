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


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_CATALOG), KeyboardButton(text=BTN_CART))
    builder.row(KeyboardButton(text=BTN_ORDERS), KeyboardButton(text=BTN_CONTACT))
    return builder.as_markup(resize_keyboard=True)


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)
    )
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


def cancel_only_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
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


def product_detail_keyboard(product_id: int, category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Savatga qo'shish", callback_data=f"add:{product_id}")
    builder.button(text="⬅️ Ro'yxatga qaytish", callback_data=f"cat:{category}")
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
