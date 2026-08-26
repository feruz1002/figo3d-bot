"""
Ma'lumotlar bazasi (SQLite) bilan ishlash funksiyalari.

SQLite - bu alohida server talab qilmaydigan, oddiy fayl ko'rinishidagi baza
(figo3d.db). Kichik va o'rta hajmdagi botlar uchun juda mos, o'rnatish shart emas.

DIQQAT: Render'ning bepul tarifida disk "doimiy" emas - bot qayta ishga
tushganda (masalan yangi kod joylanganda) shu fayl tozalanishi mumkin. Bu
sinov bosqichida muammo emas, lekin real buyurtmalar/sharhlar ko'payganda
doimiy saqlanadigan baza (masalan tashqi Postgres) ga o'tish tavsiya etiladi.

Bu yerda jadvallar:
  cart_items      - har bir foydalanuvchining savatidagi mahsulotlar
  orders          - rasmiylashtirilgan buyurtmalar
  reviews         - mahsulotlarga qoldirilgan baho/izohlar
  promo_codes     - chegirma kodlari
  custom_orders   - mijozning o'z rasmi asosidagi shaxsiy buyurtmalari
  users           - mijoz profili (ism/telefon/manzil) va hamyon balansi
  topup_requests  - hamyonni to'ldirish so'rovlari (admin tasdig'i kutiladi)
"""
import json
from datetime import datetime, timezone

import aiosqlite

from config import DB_PATH
from products import get_product_by_id

CREATE_TABLES_SQL = """
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
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.executescript(CREATE_TABLES_SQL)
        await conn.commit()
        # Eski (promo qo'shilishidan oldin yaratilgan) orders jadvali bo'lsa ham ishlashi uchun:
        await _add_column_if_missing(conn, "orders", "promo_code TEXT")
        await _add_column_if_missing(conn, "orders", "discount_amount INTEGER NOT NULL DEFAULT 0")


# ---------- SAVAT (CART) ----------

async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    async with aiosqlite.connect(DB_PATH) as conn:
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
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT product_id, quantity FROM cart_items WHERE user_id = ?",
            (user_id,),
        )
        rows = await cursor.fetchall()

    cart = []
    for product_id, quantity in rows:
        product = get_product_by_id(product_id)
        if product:  # mahsulot katalogdan o'chirilgan bo'lishi ham mumkin
            cart.append({"product": product, "quantity": quantity})
    return cart


async def get_cart_total(user_id: int) -> int:
    cart = await get_cart(user_id)
    return sum(item["product"]["price"] * item["quantity"] for item in cart)


async def clear_cart(user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        await conn.commit()


async def remove_from_cart(user_id: int, product_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        await conn.commit()


async def get_cart_item_quantity(user_id: int, product_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
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
    async with aiosqlite.connect(DB_PATH) as conn:
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


# ---------- BUYURTMALAR (ORDERS) ----------

async def create_order(
    user_id: int,
    full_name: str,
    phone: str,
    address: str,
    promo_code: str | None = None,
    discount_amount: int = 0,
) -> int:
    """Savatdagi mahsulotlar asosida buyurtma yaratadi va savatni tozalaydi.
    Yaratilgan buyurtma ID raqamini qaytaradi."""
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

    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            """INSERT INTO orders
               (user_id, full_name, phone, address, items_json, total_price, status,
                created_at, promo_code, discount_amount)
               VALUES (?, ?, ?, ?, ?, ?, 'yangi', ?, ?, ?)""",
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
            ),
        )
        await conn.commit()
        order_id = cursor.lastrowid

    if promo_code:
        await increment_promo_usage(promo_code)

    await clear_cart(user_id)
    return order_id


async def get_order(order_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
        )
        await conn.commit()


async def get_user_orders(user_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ---------- SHARHLAR (REVIEWS) ----------

async def add_review(product_id: int, user_id: int, user_name: str, rating: int, comment: str | None):
    async with aiosqlite.connect(DB_PATH) as conn:
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
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?", (product_id,)
        )
        avg_rating, count = await cursor.fetchone()
        return (round(avg_rating, 1) if avg_rating else 0.0, count or 0)


async def get_reviews(product_id: int, limit: int = 5):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM reviews WHERE product_id = ? ORDER BY id DESC LIMIT ?",
            (product_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ---------- PROMO-KODLAR ----------

async def create_promo(code: str, discount_percent: int, max_uses: int | None = None):
    async with aiosqlite.connect(DB_PATH) as conn:
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
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM promo_codes WHERE code = ? AND active = 1", (code.upper(),)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def increment_promo_usage(code: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE promo_codes SET used_count = used_count + 1 WHERE code = ?",
            (code.upper(),),
        )
        await conn.commit()


# ---------- SHAXSIY (CUSTOM) BUYURTMALAR ----------

async def create_custom_order(
    user_id: int, photo_file_id: str, description: str, full_name: str, phone: str, address: str
) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
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
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM custom_orders WHERE id = ?", (order_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_custom_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE custom_orders SET status = ? WHERE id = ?", (status, order_id)
        )
        await conn.commit()


# ---------- FOYDALANUVCHI PROFILI (ism/telefon/manzil + hamyon) ----------

async def get_user_profile(user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
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
    async with aiosqlite.connect(DB_PATH) as conn:
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
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?", (delta, user_id)
        )
        await conn.commit()
        cursor = await conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0]


# ---------- HISOBNI TO'LDIRISH SO'ROVLARI ----------

async def create_topup_request(user_id: int, amount: int, screenshot_file_id: str | None) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            """INSERT INTO topup_requests (user_id, amount, screenshot_file_id, status, created_at)
               VALUES (?, ?, ?, 'kutilmoqda', ?)""",
            (user_id, amount, screenshot_file_id, datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        await conn.commit()
        return cursor.lastrowid


async def get_topup_request(request_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM topup_requests WHERE id = ?", (request_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_topup_status(request_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE topup_requests SET status = ? WHERE id = ?", (status, request_id)
        )
        await conn.commit()
