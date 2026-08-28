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
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# ---------- Asosiy menyu (pastdagi doimiy tugmalar) ----------

BTN_CATALOG = "🗂 Katalog"
BTN_CART = "🛒 Savat"
BTN_ORDERS = "📦 Buyurtmalarim"
BTN_PROFILE = "👤 Profil"
BTN_CONTACT = "☎️ Aloqa"
BTN_CUSTOM = "🎨 Shaxsiy buyurtma"
BTN_ADMIN = "🛠 Admin panel"

BTN_SKIP_PROMO = "➡️ O'tkazib yuborish"
BTN_CANCEL = "❌ Bekor qilish"
BTN_SKIP_PROOF = "📎 Skrinshotsiz yuborish"


def main_menu_keyboard(is_admin: bool = False):
    # MUHIM (foydalanuvchi so'rovi bilan qaytarildi): ILGARI production'da
    # (WEBAPP_URL mavjud bo'lganda) bu pastdagi matnli tugmalar butunlay
    # OLIB TASHLANGAN edi - hammasi faqat Mini App (veb-do'kon) ichida
    # ishlashi kerak edi. Lekin amalda Mini App'ning veb-ko'rinishi (JS/
    # webview) ba'zan ishonchsiz chiqib qoldi (savat/buyurtma "qotib
    # qolishi" kabi muammolar) - shuning uchun ENDI bu tugmalar HAR DOIM
    # (production'da ham) ko'rsatiladi: ular oddiy Telegram xabar
    # almashinuvi orqali ishlagani uchun ancha ishonchli. "🛍 Do'kon" Mini
    # App tugmasi ham alohida qoladi (bot.py'da MenuButtonWebApp orqali),
    # lekin endi u FAQAT katalogni ko'rish va savatga qo'shish uchun -
    # buyurtma berish/profil/buyurtmalar/shaxsiy buyurtma/aloqa esa ENDI
    # faqat shu pastdagi chat tugmalari orqali ishlaydi.
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_CATALOG), KeyboardButton(text=BTN_CART))
    builder.row(KeyboardButton(text=BTN_ORDERS), KeyboardButton(text=BTN_PROFILE))
    builder.row(KeyboardButton(text=BTN_CUSTOM), KeyboardButton(text=BTN_CONTACT))
    if is_admin:
        # FAQAT adminlarga ko'rinadigan qo'shimcha qator - oddiy mijozlar
        # bu tugmani umuman ko'rmaydi (chaqiruvchi `is_admin` ni to'g'ri
        # berishi shart, pastga qarang: handlers/start.py).
        builder.row(KeyboardButton(text=BTN_ADMIN))
    return builder.as_markup(resize_keyboard=True)


def contact_request_keyboard(saved_phone: str | None = None) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)
    )
    if saved_phone:
        # Avvalgi (profilda saqlangan) raqamni ham TUGMA sifatida ko'rsatamiz -
        # mijoz shuni ko'rib, bosib tasdiqlashi yoki yangisini yozishi mumkin.
        # Hech qachon buni ko'rsatmasdan, chetlab o'tib avtomatik ishlatilmaydi.
        builder.row(KeyboardButton(text=saved_phone))
    builder.row(KeyboardButton(text=BTN_CANCEL))
    return builder.as_markup(resize_keyboard=True)


def prefill_or_cancel_keyboard(saved_value: str | None) -> ReplyKeyboardMarkup:
    """Checkout'da ism/manzil so'ralganda ishlatiladi: agar profilda saqlangan
    qiymat bo'lsa, uni TUGMA sifatida ko'rsatadi (bosilsa xuddi shu matn
    yuborilgani kabi ishlaydi) - shu bilan mijoz qiymatni HAR DOIM ko'radi va
    bitta tugma bilan tasdiqlashi yoki qo'lda boshqasini yozishi mumkin.

    MUHIM (BUZILMASIN): avval bu o'rniga "🙋 O'zim uchun / 🎁 Sovg'a" degan
    oraliq tanlov ekrani bor edi - u bosilganda manzil HECH QACHON
    ko'rsatilmasdan, sinovsiz to'g'ridan-to'g'ri ishlatilardi. Mijoz
    "manzil so'ramadi" deb shikoyat qilgani uchun bu OLIB TASHLANGAN edi -
    qaytarilmasin. Qiymat har doim shu tugmada KO'RINADI, hech qachon
    ko'rsatmasdan avtomatik ishlatilmaydi."""
    builder = ReplyKeyboardBuilder()
    if saved_value:
        builder.row(KeyboardButton(text=saved_value))
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
# MUHIM (27-avgust, "katalog ichida katalog" so'roviga javoban): endi
# bo'lim (category) ichida ixtiyoriy ravishda kichik bo'lim (subcategory)
# ham bo'lishi mumkin - 2 daraja: Bo'lim -> Kichik bo'lim -> Mahsulotlar.
# Kichik bo'limi yo'q mahsulotlar bo'lim ichida to'g'ridan-to'g'ri
# ko'rinaveradi (eski xatti-harakat buzilmaydi). DIQQAT: Telegram
# callback_data uzunligi 64 BAYTdan oshmasligi kerak - shuning uchun
# bo'lim/kichik bo'lim nomlarini juda uzun qilib qo'ymaslik tavsiya etiladi.

def categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category, callback_data=f"cat:{category}")
    builder.adjust(1)
    return builder.as_markup()


def subcategories_keyboard(category: str, subcategories: list) -> InlineKeyboardMarkup:
    """Bo'lim ichida kichik bo'limlar bo'lsa, avval shular ro'yxati
    ko'rsatiladi. "📦 Hammasini ko'rish" - kichik bo'limga ega bo'lmagan
    mahsulotlar ham (agar bo'lsa) shu bo'limda bo'lsa, hammasini birga
    ko'rish uchun."""
    builder = InlineKeyboardBuilder()
    for sub in subcategories:
        builder.button(text=sub, callback_data=f"subcat:{category}:{sub}")
    builder.button(text="📦 Hammasini ko'rish", callback_data=f"catall:{category}")
    builder.button(text="⬅️ Bo'limlarga qaytish", callback_data="back_categories")
    builder.adjust(1)
    return builder.as_markup()


def products_keyboard(category: str, products: list, subcategory: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        price_fmt = f"{product['price']:,}".replace(",", " ")
        builder.button(
            text=f"{product['name']} — {price_fmt} so'm",
            callback_data=f"prod:{product['id']}",
        )
    if subcategory:
        builder.button(text="⬅️ Kichik bo'limlarga qaytish", callback_data=f"cat:{category}")
    else:
        builder.button(text="⬅️ Bo'limlarga qaytish", callback_data="back_categories")
    builder.adjust(1)
    return builder.as_markup()


def product_detail_keyboard(
    product_id: int, has_reviews: bool = False, cart_qty: int = 0
) -> InlineKeyboardMarkup:
    """DIQQAT: "Ro'yxatga qaytish" endi mahsulotning O'ZIGA (backto:{id})
    tayanadi, category matnini qayta kodlamaydi - shu bilan mahsulot qaysi
    kichik bo'limdan ochilgan bo'lsa, aynan o'sha ro'yxatga qaytadi (server
    tomonda product_id orqali qayta aniqlanadi, handlers/catalog.py'ga
    qarang)."""
    add_text = "➕ Savatga qo'shish" if cart_qty == 0 else f"➕ Yana qo'shish (savatda: {cart_qty} ta)"
    builder = InlineKeyboardBuilder()
    builder.button(text=add_text, callback_data=f"add:{product_id}")
    builder.button(text="⭐ Baho berish", callback_data=f"review:{product_id}")
    if has_reviews:
        builder.button(text="💬 Sharhlarni ko'rish", callback_data=f"viewreviews:{product_id}")
    builder.button(text="⬅️ Ro'yxatga qaytish", callback_data=f"backto:{product_id}")
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


def _add_contact_button(builder: InlineKeyboardBuilder, user_id: int | None):
    """DIQQAT: `tg://user?id=...` havolasi Telegram tomonidan har doim ham
    ochilishi kafolatlanmagan (agar mijoz hech qachon admin bilan umumiy
    chatda/kontaktda bo'lmagan bo'lsa, ba'zi Telegram versiyalarida
    ishlamasligi mumkin) - lekin bu hozircha ENG YAQIN, botsiz mumkin
    bo'lgan "mijozga o'tish" usuli, shuning uchun qo'shilgan."""
    if user_id:
        builder.button(text="💬 Mijoz bilan bog'lanish", url=f"tg://user?id={user_id}")


def admin_order_keyboard(order_id: int, user_id: int | None = None) -> InlineKeyboardMarkup:
    """Yangi buyurtma xabari ostidagi tugmalar (🆕 Qabul qilish bosqichi)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Qabul qildim", callback_data=f"order_accept:{order_id}")
    builder.button(text="⚠️ Muammo", callback_data=f"order_problem:{order_id}")
    _add_contact_button(builder, user_id)
    builder.adjust(1)
    return builder.as_markup()


def admin_order_shipping_keyboard(order_id: int, user_id: int | None = None) -> InlineKeyboardMarkup:
    """Qabul qilingandan keyingi tugmalar (🛠 Yig'ish bosqichi)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🚚 Chiqarib yubordim", callback_data=f"order_ship:{order_id}")
    builder.button(text="⚠️ Muammo", callback_data=f"order_problem:{order_id}")
    _add_contact_button(builder, user_id)
    builder.adjust(1)
    return builder.as_markup()


def admin_order_archive_keyboard(order_id: int, user_id: int | None = None) -> InlineKeyboardMarkup:
    """Chiqarib yuborilgandan keyingi tugmalar (🚚 Chiqarib yuborilgan bosqichi)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yetkazildi", callback_data=f"order_archive:{order_id}")
    builder.button(text="⚠️ Muammo", callback_data=f"order_problem:{order_id}")
    _add_contact_button(builder, user_id)
    builder.adjust(1)
    return builder.as_markup()


def empty_keyboard(user_id: int | None = None) -> InlineKeyboardMarkup:
    """Yakunlangan (arxiv/muammo) buyurtma xabaridagi tugmalarni deyarli
    butunlay olib tashlash uchun - `reply_markup`ni chaqirmasdan qoldirish
    Telegram tomonidan "o'zgarishsiz qoldirish" deb talqin qilinadi, shuning
    uchun haqiqatan ham OLIB TASHLASH uchun bo'sh (yoki faqat bog'lanish
    tugmali) klaviatura YUBORILISHI kerak. `user_id` berilsa - yakunlangan
    buyurtmada ham admin mijoz bilan bog'lanish imkoniyatini yo'qotmaydi."""
    builder = InlineKeyboardBuilder()
    _add_contact_button(builder, user_id)
    builder.adjust(1)
    return builder.as_markup()


def custom_admin_keyboard(custom_order_id: int, user_id: int | None = None) -> InlineKeyboardMarkup:
    """Shaxsiy buyurtma haqidagi admin xabari ostidagi tugma."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Mijoz bilan bog'landim", callback_data=f"custom_contacted:{custom_order_id}"
    )
    _add_contact_button(builder, user_id)
    builder.adjust(1)
    return builder.as_markup()


# ---------- Profil va hamyon uchun tugmalar ----------
# DIQQAT: bu yerda ataylab "🙋 O'zim uchun / 🎁 Sovg'a" degan oraliq tanlov
# klaviaturasi YO'Q - u avval shu yerda bo'lgan, lekin manzilni HECH
# KO'RSATMASDAN sinovsiz ishlatib yuborgani uchun OLIB TASHLANGAN (yuqorida,
# prefill_or_cancel_keyboard izohiga qarang). Qaytarilmasin.


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
