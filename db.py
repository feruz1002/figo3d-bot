"""
Ma'lumotlar bazasi (SQLite) bilan ishlash funksiyalari.

SQLite - bu alohida server talab qilmaydigan, oddiy fayl ko'rinishidagi baza
(figo3d.db). Kichik va o'rta hajmdagi botlar uchun juda mos, o'rnatish shart emas.

DIQQAT: Render'ning bepul tarifida disk "doimiy" emas - bot qayta ishga
tushganda (masalan yangi kod joylanganda) shu fayl tozalanishi mumkin. Bu
sinov bosqichida muammo emas, lekin real buyurtmalar/sharhlar ko'payganda
doimiy saqlanadigan baza (masalan tashqi Postgres) ga o'tish tavsiya etiladi.

Bu yerda jadvallar:
  products        - katalogdagi mahsulotlar (endi products.py emas, shu yerda
                     saqlanadi - admin /admin buyrug'i orqali qo'shadi/o'chiradi)
  product_photos  - har bir mahsulotning rasmlari (bir nechta bo'lishi mumkin)
  cart_items      - har bir foydalanuvchining savatidagi mahsulotlar
  orders          - rasmiylashtirilgan buyurtmalar
  reviews         - mahsulotlarga qoldirilgan baho/izohlar
  promo_codes     - chegirma kodlari
  custom_orders   - mijozning o'z rasmi asosidagi shaxsiy buyurtmalari
  users           - mijoz profili (ism/telefon/manzil) va hamyon balansi
  topup_requests  - hamyonni to'ldirish so'rovlari (admin tasdig'i kutiladi)
"""
import json
from datetime import datetime, timedelta, timezone

from products import SEED_PRODUCTS
from turso_db import get_db_connection

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    video_file_id TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS product_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    file_id TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    full_name TEXT,
    phone TEXT,
    address TEXT,
    items_json TEXT NOT NULL,
    total_price INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'yangi',
    created_at TEXT NOT NULL,
    promo_code TEXT,
    discount_amount INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_name TEXT,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS promo_codes (
    code TEXT PRIMARY KEY,
    discount_percent INTEGER NOT NULL,
    max_uses INTEGER,
    used_count INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS custom_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    photo_file_id TEXT NOT NULL,
    description TEXT,
    full_name TEXT,
    phone TEXT,
    address TEXT,
    status TEXT NOT NULL DEFAULT 'yangi',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    phone TEXT,
    address TEXT,
    balance INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS topup_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    screenshot_file_id TEXT,
    status TEXT NOT NULL DEFAULT 'kutilmoqda',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    photo_file_id TEXT,
    created_at TEXT NOT NULL
);
"""


async def _add_column_if_missing(conn, table: str, column_def: str):
    """Eski (oldin yaratilgan) bazaga yangi ustun qo'shadi, agar hali yo'q bo'lsa.
    SQLite'da "ADD COLUMN IF NOT EXISTS" yo'q, shuning uchun xatoni o'zimiz tutamiz."""
    column_name = column_def.split()[0]
    try:
        await conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        await conn.commit()
    except Exception as exc:
        if "duplicate column name" not in str(exc).lower():
            raise
    _ = column_name  # faqat o'qish uchun, xato xabarida foydali bo'lsin deb saqlandi


async def init_db():
    """Bot birinchi marta ishga tushganda jadvallarni yaratadi (agar hali yo'q bo'lsa)."""
    async with get_db_connection() as conn:
        await conn.executescript(CREATE_TABLES_SQL)
        await conn.commit()
        # Eski (promo qo'shilishidan oldin yaratilgan) orders jadvali bo'lsa ham ishlashi uchun:
        await _add_column_if_missing(conn, "orders", "promo_code TEXT")
        await _add_column_if_missing(conn, "orders", "discount_amount INTEGER NOT NULL DEFAULT 0")
        # 27-avgust: "Muammo" bosqichida admin yozadigan sabab (izoh) uchun.
        await _add_column_if_missing(conn, "orders", "problem_reason TEXT")
        # 28-avgust: moliyaviy hisobotda to'lov usuli bo'yicha taqsimot
        # ko'rsatish uchun - AVVAL to'lov usuli faqat "status" ichida
        # (masalan "to'landi (karta)") vaqtinchalik saqlanardi va buyurtma
        # bosqichdan o'tgach (masalan "qabul qilindi"ga o'tgach) bu
        # ma'lumot BUTUNLAY yo'qolib qolardi. Endi alohida ustunda doimiy
        # saqlanadi.
        await _add_column_if_missing(conn, "orders", "payment_method TEXT")
        # 27-avgust: "katalog ichida katalog" (kichik bo'lim) uchun - ixtiyoriy,
        # bo'sh (NULL) bo'lsa mahsulot to'g'ridan-to'g'ri bo'lim ichida turadi.
        await _add_column_if_missing(conn, "products", "subcategory TEXT")
        # 27-avgust: statistika uchun - foydalanuvchi /start bosgan zahoti
        # (hali profil to'ldirmagan bo'lsa ham) "botni ko'rgan odam" sifatida
        # qayd etiladi (touch_user_seen'ga qarang).
        await _add_column_if_missing(conn, "users", "first_seen_at TEXT")
        # 28-avgust: admin panelidagi "tg://user?id=..." havolasi Mini App
        # veb-sahifasi ICHIDA Telegram tomonidan BLOKLANGANI aniqlandi
        # ("This content is blocked" xatosi chiqqan) - shuning uchun endi
        # mijozning @username'i (bor bo'lsa) saqlanadi va o'rniga
        # https://t.me/<username> havolasi ishlatiladi (remember_username'ga
        # qarang) - bu haqiqiy https havola bo'lgani uchun bloklanmaydi.
        await _add_column_if_missing(conn, "users", "username TEXT")

        # Baza bo'sh bo'lsa (bot birinchi marta ishga tushganda) - namuna
        # mahsulotlar bilan to'ldiramiz, shunda katalog darhol bo'sh bo'lib
        # qolmaydi. Bundan keyingi barcha mahsulotlar /admin orqali qo'shiladi.
        cursor = await conn.execute("SELECT COUNT(*) FROM products")
        (count,) = await cursor.fetchone()
        if count == 0:
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            for p in SEED_PRODUCTS:
                await conn.execute(
                    """INSERT INTO products (category, name, description, price, active, created_at)
                       VALUES (?, ?, ?, ?, 1, ?)""",
                    (p["category"], p["name"], p["description"], p["price"], now),
                )
            await conn.commit()


# ---------- MAHSULOTLAR (PRODUCTS) ----------

async def _row_to_product(conn, row) -> dict:
    """DB qatorini eski (products.py'dagi) dict ko'rinishiga o'giradi, shu bilan
    keyboards.py/handlers kodlari o'zgarishsiz product['photos'] va h.k. dan
    foydalanishda davom etaveradi."""
    cursor = await conn.execute(
        "SELECT file_id FROM product_photos WHERE product_id = ? ORDER BY position, id",
        (row["id"],),
    )
    photo_rows = await cursor.fetchall()
    return {
        "id": row["id"],
        "category": row["category"],
        "subcategory": row["subcategory"] if "subcategory" in row.keys() else None,
        "name": row["name"],
        "description": row["description"] or "",
        "price": row["price"],
        "photos": [r[0] for r in photo_rows],
        "video": row["video_file_id"],
    }


async def get_categories() -> list:
    """Barcha faol bo'limlar ro'yxatini qaytaradi (birinchi qo'shilgan mahsulot
    tartibida)."""
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT category FROM products WHERE active = 1 GROUP BY category ORDER BY MIN(id)"
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]


async def get_subcategories(category: str) -> list:
    """Berilgan bo'lim ichidagi kichik bo'limlar ro'yxati (faqat kichik bo'limi
    BOR mahsulotlar hisobga olinadi - bo'sh/NULL bo'lganlar bu yerda chiqmaydi,
    ular bo'lim ichida to'g'ridan-to'g'ri ko'rinadi)."""
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT subcategory FROM products WHERE category = ? AND active = 1 "
            "AND subcategory IS NOT NULL AND subcategory != '' "
            "GROUP BY subcategory ORDER BY MIN(id)",
            (category,),
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]


async def get_products_by_category(category: str, subcategory: str | None = None) -> list:
    """subcategory berilmasa (None) - shu bo'limdagi HAMMA mahsulot (kichik
    bo'limi bor-yo'qligidan qat'i nazar) qaytadi - eski xatti-harakat saqlanadi,
    Mini App katalogi va admin ro'yxati shu funksiyaga tayanadi. subcategory
    berilsa - faqat aynan o'sha kichik bo'limdagi mahsulotlar qaytadi."""
    async with get_db_connection() as conn:
        if subcategory is not None:
            cursor = await conn.execute(
                "SELECT * FROM products WHERE category = ? AND subcategory = ? AND active = 1 ORDER BY id",
                (category, subcategory),
            )
        else:
            cursor = await conn.execute(
                "SELECT * FROM products WHERE category = ? AND active = 1 ORDER BY id", (category,)
            )
        rows = await cursor.fetchall()
        return [await _row_to_product(conn, row) for row in rows]


async def get_product_by_id(product_id: int):
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM products WHERE id = ? AND active = 1", (product_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return await _row_to_product(conn, row)


async def list_active_products() -> list:
    """Admin uchun: barcha faol mahsulotlar ro'yxati (rasmsiz, ro'yxat/o'chirish
    ko'rinishi uchun)."""
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM products WHERE active = 1 ORDER BY category, id"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def create_product(
    category: str, name: str, description: str, price: int, subcategory: str | None = None
) -> int:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            """INSERT INTO products (category, subcategory, name, description, price, active, created_at)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (category, subcategory or None, name, description, price, now),
        )
        await conn.commit()
        return cursor.lastrowid


async def add_product_photo(product_id: int, file_id: str, position: int = 0):
    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO product_photos (product_id, file_id, position) VALUES (?, ?, ?)",
            (product_id, file_id, position),
        )
        await conn.commit()


async def set_product_video(product_id: int, file_id: str):
    async with get_db_connection() as conn:
        await conn.execute(
            "UPDATE products SET video_file_id = ? WHERE id = ?", (file_id, product_id)
        )
        await conn.commit()


async def deactivate_product(product_id: int):
    """Mahsulotni butunlay o'chirmaydi (eski buyurtmalar/sharhlar uzilib
    qolmasligi uchun) - faqat katalogdan yashiradi."""
    async with get_db_connection() as conn:
        await conn.execute("UPDATE products SET active = 0 WHERE id = ?", (product_id,))
        await conn.commit()


# ---------- SAVAT (CART) ----------

async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        row = await cursor.fetchone()
        if row:
            new_qty = row[1] + quantity
            await conn.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?", (new_qty, row[0])
            )
        else:
            await conn.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, quantity),
            )
        await conn.commit()


async def get_cart(user_id: int):
    """Foydalanuvchi savatini qaytaradi: [{product: {...}, quantity: N}, ...]"""
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT product_id, quantity FROM cart_items WHERE user_id = ?",
            (user_id,),
        )
        rows = await cursor.fetchall()

    cart = []
    for product_id, quantity in rows:
        product = await get_product_by_id(product_id)
        if product:  # mahsulot katalogdan o'chirilgan bo'lishi ham mumkin
            cart.append({"product": product, "quantity": quantity})
    return cart


async def get_cart_total(user_id: int) -> int:
    cart = await get_cart(user_id)
    return sum(item["product"]["price"] * item["quantity"] for item in cart)


async def clear_cart(user_id: int):
    async with get_db_connection() as conn:
        await conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        await conn.commit()


async def remove_from_cart(user_id: int, product_id: int):
    async with get_db_connection() as conn:
        await conn.execute(
            "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        await conn.commit()


async def get_cart_item_quantity(user_id: int, product_id: int) -> int:
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def decrease_cart_item(user_id: int, product_id: int, amount: int = 1) -> int:
    """Miqdorni 'amount' ga kamaytiradi; 0 yoki kamiga tushsa, butunlay o'chiradi.
    Qolgan (yangi) miqdorni qaytaradi (0 = savatda qolmadi)."""
    current = await get_cart_item_quantity(user_id, product_id)
    new_qty = current - amount
    async with get_db_connection() as conn:
        if new_qty <= 0:
            await conn.execute(
                "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
                (user_id, product_id),
            )
            new_qty = 0
        else:
            await conn.execute(
                "UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ?",
                (new_qty, user_id, product_id),
            )
        await conn.commit()
    return new_qty


async def set_cart_item_quantity(user_id: int, product_id: int, quantity: int) -> int:
    """Miqdorni to'g'ridan-to'g'ri berilgan songa o'rnatadi (masalan veb-do'kondagi
    ➖/➕ bosqichlari uchun qulay). 0 yoki kamiga o'rnatilsa, butunlay o'chiradi.
    Yakuniy (haqiqiy) miqdorni qaytaradi."""
    async with get_db_connection() as conn:
        if quantity <= 0:
            await conn.execute(
                "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
                (user_id, product_id),
            )
            await conn.commit()
            return 0
        cursor = await conn.execute(
            "SELECT id FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        row = await cursor.fetchone()
        if row:
            await conn.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (quantity, row[0]))
        else:
            await conn.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, quantity),
            )
        await conn.commit()
        return quantity


# ---------- BUYURTMALAR (ORDERS) ----------

async def create_order(
    user_id: int,
    full_name: str,
    phone: str,
    address: str,
    promo_code: str | None = None,
    discount_amount: int = 0,
    payment_method: str | None = None,
) -> int:
    """Savatdagi mahsulotlar asosida buyurtma yaratadi va savatni tozalaydi.
    Yaratilgan buyurtma ID raqamini qaytaradi. `payment_method` - "balance" |
    "cash" | "card" (moliyaviy hisobotda to'lov usuli bo'yicha taqsimot
    uchun saqlanadi - status keyinchalik o'zgarsa ham bu maydon
    o'zgarmaydi)."""
    cart = await get_cart(user_id)
    subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart)
    total_price = max(subtotal - discount_amount, 0)
    items_snapshot = [
        {
            "name": item["product"]["name"],
            "price": item["product"]["price"],
            "quantity": item["quantity"],
        }
        for item in cart
    ]

    async with get_db_connection() as conn:
        cursor = await conn.execute(
            """INSERT INTO orders
               (user_id, full_name, phone, address, items_json, total_price, status,
                created_at, promo_code, discount_amount, payment_method)
               VALUES (?, ?, ?, ?, ?, ?, 'yangi', ?, ?, ?, ?)""",
            (
                user_id,
                full_name,
                phone,
                address,
                json.dumps(items_snapshot, ensure_ascii=False),
                total_price,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                promo_code,
                discount_amount,
                payment_method,
            ),
        )
        await conn.commit()
        order_id = cursor.lastrowid

    if promo_code:
        await increment_promo_usage(promo_code)

    await clear_cart(user_id)
    return order_id


async def get_order(order_id: int):
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_order_status(order_id: int, status: str):
    async with get_db_connection() as conn:
        await conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
        )
        await conn.commit()


async def set_order_problem(order_id: int, status: str, reason: str | None):
    """'⚠️ Muammo' deb belgilashda status BILAN BIRGA sababni (izohni) ham
    saqlaydi - admin panelda va mijozga yuboriladigan xabarda ko'rsatish uchun."""
    async with get_db_connection() as conn:
        await conn.execute(
            "UPDATE orders SET status = ?, problem_reason = ? WHERE id = ?",
            (status, reason, order_id),
        )
        await conn.commit()


async def get_user_orders(user_id: int, limit: int = 10):
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_all_orders(limit: int = 50, open_only: bool = False):
    """Admin panel uchun: barcha (yoki faqat hali "qabul qilindi"ga
    o'tmagan) buyurtmalar ro'yxati, eng yangisidan boshlab."""
    async with get_db_connection() as conn:
        if open_only:
            cursor = await conn.execute(
                "SELECT * FROM orders WHERE status NOT IN ('qabul qilindi', 'yetkazildi') "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        else:
            cursor = await conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
        rows = await cursor.fetchall()
    # MUHIM (xato tuzatildi): `_attach_customer_usernames` o'zi ham
    # `get_db_connection()`ni chaqiradi - shu SABABLI bu yerda `async with`
    # bloki ICHIDA turib chaqirilsa, ikkinchi marta bir xil `_lock`ni olishga
    # urinib DEADLOCK bo'lardi (lock qayta kirish - reentrant - emas). Shu
    # sabab avval `async with` blokidan CHIQAMIZ (yuqoridagi indentatsiyaga
    # qarang), keyin (lock bo'shatilgandan so'ng) chaqiramiz.
    return await _attach_customer_usernames([dict(r) for r in rows])


async def get_orders_by_statuses(statuses: list, limit: int = 100):
    """Admin panelning bosqichli (Kanban: Qabul qilish / Yig'ish / Chiqarib
    yuborilgan / Arxiv-Muammo) ko'rinishi uchun: berilgan status(lar)dagi
    buyurtmalar ro'yxati, eng yangisidan boshlab. `statuses` bo'sh bo'lsa,
    bo'sh ro'yxat qaytadi (SQL xatosiga yo'l qo'ymaslik uchun)."""
    if not statuses:
        return []
    async with get_db_connection() as conn:
        placeholders = ",".join("?" for _ in statuses)
        cursor = await conn.execute(
            f"SELECT * FROM orders WHERE status IN ({placeholders}) ORDER BY id DESC LIMIT ?",
            (*statuses, limit),
        )
        rows = await cursor.fetchall()
    # (qarang: get_all_orders'dagi izoh - deadlock'ning oldini olish uchun
    # `async with` blokidan CHIQIB keyin chaqiriladi.)
    return await _attach_customer_usernames([dict(r) for r in rows])


# ---------- SHARHLAR (REVIEWS) ----------

async def add_review(product_id: int, user_id: int, user_name: str, rating: int, comment: str | None):
    async with get_db_connection() as conn:
        await conn.execute(
            """INSERT INTO reviews (product_id, user_id, user_name, rating, comment, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                product_id,
                user_id,
                user_name,
                rating,
                comment,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        await conn.commit()


async def get_product_rating(product_id: int) -> tuple[float, int]:
    """(o'rtacha_baho, sharhlar_soni) qaytaradi. Sharh bo'lmasa (0.0, 0)."""
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?", (product_id,)
        )
        avg_rating, count = await cursor.fetchone()
        return (round(avg_rating, 1) if avg_rating else 0.0, count or 0)


async def get_reviews(product_id: int, limit: int = 5):
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM reviews WHERE product_id = ? ORDER BY id DESC LIMIT ?",
            (product_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ---------- PROMO-KODLAR ----------

async def create_promo(code: str, discount_percent: int, max_uses: int | None = None):
    async with get_db_connection() as conn:
        await conn.execute(
            """INSERT INTO promo_codes (code, discount_percent, max_uses, used_count, active)
               VALUES (?, ?, ?, 0, 1)
               ON CONFLICT(code) DO UPDATE SET
                   discount_percent = excluded.discount_percent,
                   max_uses = excluded.max_uses,
                   active = 1""",
            (code.upper(), discount_percent, max_uses),
        )
        await conn.commit()


async def get_promo(code: str):
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM promo_codes WHERE code = ? AND active = 1", (code.upper(),)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def increment_promo_usage(code: str):
    async with get_db_connection() as conn:
        await conn.execute(
            "UPDATE promo_codes SET used_count = used_count + 1 WHERE code = ?",
            (code.upper(),),
        )
        await conn.commit()


# ---------- SHAXSIY (CUSTOM) BUYURTMALAR ----------

async def create_custom_order(
    user_id: int, photo_file_id: str, description: str, full_name: str, phone: str, address: str
) -> int:
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            """INSERT INTO custom_orders
               (user_id, photo_file_id, description, full_name, phone, address, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'yangi', ?)""",
            (
                user_id,
                photo_file_id,
                description,
                full_name,
                phone,
                address,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        await conn.commit()
        return cursor.lastrowid


async def get_custom_order(order_id: int):
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT * FROM custom_orders WHERE id = ?", (order_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_custom_order_status(order_id: int, status: str):
    async with get_db_connection() as conn:
        await conn.execute(
            "UPDATE custom_orders SET status = ? WHERE id = ?", (status, order_id)
        )
        await conn.commit()


# ---------- FOYDALANUVCHI PROFILI (ism/telefon/manzil + hamyon) ----------

async def touch_user_seen(user_id: int):
    """Foydalanuvchi /start bosgan zahoti chaqiriladi - hali profilini
    to'ldirmagan (ism/telefon/manzil bermagan) bo'lsa ham, "botni ko'rgan
    odam" sifatida qayd etiladi (statistika uchun: get_total_bot_users'ga
    qarang). Mavjud profil ma'lumotlariga TEGMAYDI - faqat birinchi
    ko'rilgan vaqtni (agar hali yozilmagan bo'lsa) belgilaydi."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    async with get_db_connection() as conn:
        await conn.execute(
            """INSERT INTO users (user_id, balance, updated_at, first_seen_at)
               VALUES (?, 0, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   first_seen_at = COALESCE(users.first_seen_at, ?)""",
            (user_id, now, now, now),
        )
        await conn.commit()


async def remember_username(user_id: int, username: str | None):
    """Foydalanuvchining Telegram @username'ini (agar bo'lsa) eslab qolish -
    admin panelda "💬 Mijoz bilan bog'lanish" havolasini (https://t.me/<username>)
    qurish uchun kerak (tg://user?id=... Mini App ichida BLOKLANGANI
    aniqlandi - qarang: init_db()dagi izoh). `username` bo'sh/None bo'lsa -
    hech narsa qilinmaydi (avvalgi qiymat saqlanib qoladi, chunki bu funksiya
    ko'plab joydan "ehtiyot chorasi sifatida" chaqiriladi va har doim ham
    Telegram username'ni bermasligi mumkin)."""
    if not username:
        return
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    async with get_db_connection() as conn:
        await conn.execute(
            """INSERT INTO users (user_id, username, balance, updated_at)
               VALUES (?, ?, 0, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   username = ?,
                   updated_at = ?""",
            (user_id, username, now, username, now),
        )
        await conn.commit()


async def _attach_customer_usernames(rows: list[dict]) -> list[dict]:
    """Buyurtma/shaxsiy buyurtma ro'yxatidagi har bir yozuvga (agar ma'lum
    bo'lsa) mijozning Telegram @username'ini "customer_username" kaliti
    sifatida qo'shib beradi - admin panelning "Mijoz bilan bog'lanish"
    havolasi shundan foydalanadi."""
    user_ids = sorted({r["user_id"] for r in rows if r.get("user_id")})
    if not user_ids:
        return rows
    async with get_db_connection() as conn:
        placeholders = ",".join("?" for _ in user_ids)
        cursor = await conn.execute(
            f"SELECT user_id, username FROM users WHERE user_id IN ({placeholders})",
            tuple(user_ids),
        )
        urows = await cursor.fetchall()
    username_map = {r["user_id"]: r["username"] for r in urows if r["username"]}
    for r in rows:
        r["customer_username"] = username_map.get(r.get("user_id"))
    return rows


async def get_user_profile(user_id: int):
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def upsert_user_profile(
    user_id: int, full_name: str | None = None, phone: str | None = None, address: str | None = None
):
    """Profilni yaratadi (agar yo'q bo'lsa) yoki yangilaydi. Faqat berilgan
    (None bo'lmagan) maydonlar o'zgaradi - boshqalari eskicha qoladi.
    Balansga tegmaydi."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    async with get_db_connection() as conn:
        await conn.execute(
            """INSERT INTO users (user_id, full_name, phone, address, balance, updated_at)
               VALUES (?, ?, ?, ?, 0, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   full_name = COALESCE(?, users.full_name),
                   phone = COALESCE(?, users.phone),
                   address = COALESCE(?, users.address),
                   updated_at = ?""",
            (user_id, full_name, phone, address, now, full_name, phone, address, now),
        )
        await conn.commit()


async def get_balance(user_id: int) -> int:
    profile = await get_user_profile(user_id)
    return profile["balance"] if profile else 0


async def adjust_balance(user_id: int, delta: int) -> int:
    """Balansni delta ga o'zgartiradi (manfiy son - kamaytirish uchun).
    Yangilangan balansni qaytaradi."""
    await upsert_user_profile(user_id)  # profil hali yo'q bo'lsa, yaratib qo'yadi
    async with get_db_connection() as conn:
        await conn.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?", (delta, user_id)
        )
        await conn.commit()
        cursor = await conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0]


# ---------- HISOBNI TO'LDIRISH SO'ROVLARI ----------

async def create_topup_request(user_id: int, amount: int, screenshot_file_id: str | None) -> int:
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            """INSERT INTO topup_requests (user_id, amount, screenshot_file_id, status, created_at)
               VALUES (?, ?, ?, 'kutilmoqda', ?)""",
            (user_id, amount, screenshot_file_id, datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        await conn.commit()
        return cursor.lastrowid


async def get_topup_request(request_id: int):
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT * FROM topup_requests WHERE id = ?", (request_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_topup_status(request_id: int, status: str):
    async with get_db_connection() as conn:
        await conn.execute(
            "UPDATE topup_requests SET status = ? WHERE id = ?", (status, request_id)
        )
        await conn.commit()


async def get_pending_topup_requests(limit: int = 50):
    """Admin panel uchun: hali ko'rib chiqilmagan (kutilmoqda) hisob
    to'ldirish so'rovlari."""
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM topup_requests WHERE status = 'kutilmoqda' ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_open_custom_orders(limit: int = 50):
    """Admin panel uchun: hali "bog'lanildi" deb belgilanmagan shaxsiy
    buyurtma so'rovlari."""
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM custom_orders WHERE status != ? ORDER BY id DESC LIMIT ?",
            ("bog'lanildi", limit),
        )
        rows = await cursor.fetchall()
    # (deadlock'ning oldini olish uchun - get_all_orders'dagi izohga qarang)
    return await _attach_customer_usernames([dict(r) for r in rows])


# ---------- STATISTIKA (admin panel "📊 Statistika" bo'limi uchun) ----------

async def get_total_bot_users() -> int:
    """Botni kamida bir marta /start bosib ko'rgan (touch_user_seen orqali
    qayd etilgan) odamlar soni - buyurtma bermagan bo'lsa ham hisoblanadi."""
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM users")
        (count,) = await cursor.fetchone()
        return count or 0


async def get_all_user_ids() -> list:
    """Botni kamida bir marta ko'rgan HAMMA odamlarning ID ro'yxati -
    "📰 Yangiliklar" e'lon qilinganda hammaga xabarnoma yuborish uchun
    (admin_notify.notify_all_customers'ga qarang)."""
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [r["user_id"] for r in rows]


async def get_customer_count() -> int:
    """Kamida BITTA buyurtma bergan (haqiqiy xaridor bo'lgan) odamlar soni."""
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT COUNT(DISTINCT user_id) FROM orders")
        (count,) = await cursor.fetchone()
        return count or 0


async def get_order_count() -> int:
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM orders")
        (count,) = await cursor.fetchone()
        return count or 0


async def get_top_products(limit: int = 8) -> list:
    """Eng ko'p buyurtma qilingan mahsulotlar - barcha buyurtmalarning
    items_json'idagi nomlar bo'yicha yig'iladi (mahsulot keyinchalik
    o'chirilgan/o'zgargan bo'lsa ham, o'sha paytdagi nomi bilan hisoblanadi,
    chunki items_json - buyurtma vaqtidagi "suratga olingan" nusxa).
    Qaytadi: [{"name": ..., "quantity": ...}, ...] ko'pdan kamga qarab."""
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT items_json FROM orders")
        rows = await cursor.fetchall()

    counts: dict[str, int] = {}
    for row in rows:
        raw = row[0]
        if not raw:
            continue
        try:
            items = json.loads(raw)
        except (TypeError, ValueError):
            continue
        for item in items:
            name = (item or {}).get("name")
            qty = (item or {}).get("quantity") or 0
            if not name:
                continue
            counts[name] = counts.get(name, 0) + qty

    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [{"name": name, "quantity": qty} for name, qty in top]


async def get_all_order_addresses() -> list:
    """Barcha buyurtmalarning manzil matnlari - viloyat statistikasini
    (order_service.guess_region orqali) hisoblash uchun."""
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT address FROM orders WHERE address IS NOT NULL")
        rows = await cursor.fetchall()
        return [r[0] for r in rows if r[0]]


async def get_revenue_report() -> dict:
    """To'liq moliyaviy hisobot (admin panel "📊 Statistika" bo'limi
    uchun): jami/yakunlangan/jarayondagi tushum, davr bo'yicha (bugun/shu
    hafta/shu oy) va to'lov usuli bo'yicha taqsimot.

    MUHIM: "muammo" holatidagi buyurtmalar HISOBGA OLINMAYDI - ular
    yakunlanmagan/bekor bo'lgan hisoblanadi, shuning uchun moliyaviy
    hisobotni "shishirmasligi" kerak."""
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT total_price, status, payment_method, created_at FROM orders WHERE status != ?",
            ("muammo",),
        )
        rows = await cursor.fetchall()

    now = datetime.now(timezone.utc).date()
    week_start = now - timedelta(days=now.weekday())
    month_start = now.replace(day=1)

    total = 0
    archived_total = 0
    pending_total = 0
    today_total = 0
    week_total = 0
    month_total = 0
    order_count = 0
    payment_buckets: dict[str, dict] = {}

    for price, status, method, created_at in rows:
        price = price or 0
        total += price
        order_count += 1
        if status == "arxiv":
            archived_total += price
        else:
            pending_total += price

        created_date = None
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at).date()
            except ValueError:
                created_date = None
        if created_date:
            if created_date == now:
                today_total += price
            if created_date >= week_start:
                week_total += price
            if created_date >= month_start:
                month_total += price

        method_key = method or "eski/nomalum"
        bucket = payment_buckets.setdefault(method_key, {"count": 0, "total": 0})
        bucket["count"] += 1
        bucket["total"] += price

    average = round(total / order_count) if order_count else 0
    by_payment = [
        {"method": k, "count": v["count"], "total": v["total"]}
        for k, v in sorted(payment_buckets.items(), key=lambda kv: -kv[1]["total"])
    ]

    return {
        "total": total,
        "archived_total": archived_total,
        "pending_total": pending_total,
        "today_total": today_total,
        "week_total": week_total,
        "month_total": month_total,
        "order_count": order_count,
        "average_order_value": average,
        "by_payment": by_payment,
    }


async def get_archived_custom_orders(limit: int = 100):
    """Admin panel uchun: "✅ Bog'landim" deb belgilangan shaxsiy buyurma
    so'rovlari - AVVAL bular ro'yxatdan BUTUNLAY g'oyib bo'lardi (faqat
    "ochiq" ro'yxat ko'rsatilardi), endi "Arxiv" bo'limida ko'rib
    turish/mijoz bilan qayta bog'lanish uchun saqlanadi."""
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM custom_orders WHERE status = ? ORDER BY id DESC LIMIT ?",
            ("bog'lanildi", limit),
        )
        rows = await cursor.fetchall()
    # (deadlock'ning oldini olish uchun - get_all_orders'dagi izohga qarang)
    return await _attach_customer_usernames([dict(r) for r in rows])


# ---------- Yangiliklar/e'lonlar (28-avgust: mijozlar Mini App'idagi yangi
# "📰 Yangiliklar" bo'limi uchun - admin panel orqali matn+ixtiyoriy rasm
# bilan e'lon/aksiya joylashtiradi, mijozlar Mini App'da ko'radi) ----------

async def create_announcement(text: str, photo_file_id: str | None = None) -> int:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "INSERT INTO announcements (text, photo_file_id, created_at) VALUES (?, ?, ?)",
            (text, photo_file_id, now),
        )
        await conn.commit()
        return cursor.lastrowid


async def get_announcements(limit: int = 50):
    async with get_db_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM announcements ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def delete_announcement(announcement_id: int):
    async with get_db_connection() as conn:
        await conn.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
        await conn.commit()
