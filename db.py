"""
Ma'lumotlar bazasi (SQLite) bilan ishlash funksiyalari.

SQLite - bu alohida server talab qilmaydigan, oddiy fayl ko'rinishidagi baza
(figo3d.db). Kichik va o'rta hajmdagi botlar uchun juda mos, o'rnatish shart emas.

Bu yerda ikkita jadval bor:
  cart_items - har bir foydalanuvchining savatidagi mahsulotlar
  orders     - rasmiylashtirilgan buyurtmalar
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
    created_at TEXT NOT NULL
);
"""


async def init_db():
    """Bot birinchi marta ishga tushganda jadvallarni yaratadi (agar hali yo'q bo'lsa)."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.executescript(CREATE_TABLES_SQL)
        await conn.commit()


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


# ---------- BUYURTMALAR (ORDERS) ----------

async def create_order(user_id: int, full_name: str, phone: str, address: str) -> int:
    """Savatdagi mahsulotlar asosida buyurtma yaratadi va savatni tozalaydi.
    Yaratilgan buyurtma ID raqamini qaytaradi."""
    cart = await get_cart(user_id)
    total_price = sum(item["product"]["price"] * item["quantity"] for item in cart)
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
               (user_id, full_name, phone, address, items_json, total_price, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'yangi', ?)""",
            (
                user_id,
                full_name,
                phone,
                address,
                json.dumps(items_snapshot, ensure_ascii=False),
                total_price,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        await conn.commit()
        order_id = cursor.lastrowid

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
