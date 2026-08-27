"""aiosqlite'ga o'xshash ASYNC qatlam - lekin orqasida Turso (libsql) bilan
ishlaydi, shu bilan ma'lumotlar Render'ning vaqtinchalik diskiga bog'liq
bo'lmay, doimiy saqlanadi.

Nima uchun kerak: `libsql` python kutubxonasining o'zi ASINXRON emas (oddiy
sqlite3 modeliga o'xshab ishlaydi) - shuning uchun har bir chaqiruvni
`asyncio.to_thread` orqali alohida oqimda bajaramiz (aiogram kutish tsiklini
"bloklab" qo'ymasligi uchun). Bundan tashqari, kod bazasi (db.py) hozircha
`aiosqlite.Row` orqali qatorlarni HAM ro'yxat (`row[0]`) HAM lug'at
(`row["nomi"]`) sifatida o'qiydi - `libsql` esa qatorlarni oddiy tuple
sifatida qaytaradi, shuning uchun quyidagi `Row` klassi shu ikkala
ko'rinishni ham qo'llab-quvvatlaydi.

Ishlash tartibi:
- Agar TURSO_DATABASE_URL/TURSO_AUTH_TOKEN sozlanmagan bo'lsa - oddiy
  mahalliy fayl (avvalgidek) ishlatiladi, hech narsa o'zgarmaydi.
- Sozlangan bo'lsa - "embedded replica" rejimi ishlatiladi: o'qish/yozish
  TEZKOR mahalliy nusxada bo'ladi, har COMMIT'dan keyin esa darhol Turso
  bulutiga sinxronlanadi (`.sync()`) - shu bilan Render qayta ishga
  tushgan/diskni tozalagan taqdirda ham, oxirgi yozuvlar allaqachon
  bulutda xavfsiz saqlangan bo'ladi. Qo'shimcha xavfsizlik uchun fonda
  davriy sinxronlash ham ishlaydi (pastga qarang, start_periodic_sync).
- MUHIM (xavfsizlik to'ri): agar TURSO_DATABASE_URL/TURSO_AUTH_TOKEN
  NOTO'G'RI bo'lsa (masalan token muddati o'tgan, xato nusxalangan yoki
  Turso tomonidan bekor qilingan) - bot BUTUNLAY ishdan to'xtab qolmaydi.
  Dastlabki ulanish muvaffaqiyatsiz tugasa, xatoni "Logs"ga aniq yozib,
  avtomatik ravishda oddiy mahalliy fayl rejimiga tushib qoladi (Turso
  to'g'rilangunicha). Aks holda bitta xato ADMIN_IDS/tokenlarni to'g'ri
  yozganingizga qaramay butun mijozlar oqimini (buyurtma berish, katalog,
  admin panel - hammasi) to'xtatib qo'yishi mumkin edi.
"""
import asyncio
import logging

import libsql

from config import DB_PATH, TURSO_AUTH_TOKEN, TURSO_DATABASE_URL

logger = logging.getLogger("figo3d_bot.db")

_TURSO_ENABLED = bool(TURSO_DATABASE_URL and TURSO_AUTH_TOKEN)
_turso_broken = False  # dastlabki ulanish muvaffaqiyatsiz tugasa True bo'ladi

_conn = None
_lock = asyncio.Lock()


class Row(tuple):
    """`aiosqlite.Row`'ning o'rnini bosadi: HAM `row[0]` (tartib raqami),
    HAM `row["ustun_nomi"]` (lug'atdek) orqali o'qish mumkin."""

    def __new__(cls, values, cols):
        obj = super().__new__(cls, values)
        obj._cols = cols
        return obj

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                idx = self._cols.index(key)
            except ValueError:
                raise KeyError(key)
            return tuple.__getitem__(self, idx)
        return tuple.__getitem__(self, key)

    def keys(self):
        return self._cols

    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, IndexError):
            return default


def _wrap_row(row, description):
    if row is None:
        return None
    cols = tuple(d[0] for d in description) if description else ()
    return Row(row, cols)


def _open_sync_conn():
    """DIQQAT: `libsql.connect(..., sync_url=...)` chaqiruvining o'zi ICHKARIDA
    darhol Turso bilan bog'lanib, dastlabki sinxronlashga urinadi - shuning
    uchun token/manzil noto'g'ri bo'lsa, xato AYNAN shu qatorda (keyingi
    alohida `.sync()` chaqiruvida emas) chiqadi. Shu sababli bu funksiyaning
    o'zi ham xatoni tutib, mahalliy (Turso'siz) ulanishga tushib qoladi -
    aks holda noto'g'ri token butun botni ishga tushmay qo'yardi."""
    global _turso_broken
    if _TURSO_ENABLED and not _turso_broken:
        try:
            return libsql.connect(DB_PATH, sync_url=TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)
        except Exception:
            _turso_broken = True
            logger.exception(
                "Turso bilan ULANIB BO'LMADI (TURSO_DATABASE_URL yoki TURSO_AUTH_TOKEN "
                "noto'g'ri bo'lishi mumkin - Render'ning Environment Variables bo'limini "
                "tekshiring). Bot HOZIRCHA oddiy mahalliy fayl bilan davom etadi (hech narsa "
                "buzilmaydi, faqat Turso'ga sinxronlash to'xtaydi) - tuzatib, qayta deploy "
                "qilganingizda avtomatik tiklanadi."
            )
    return libsql.connect(DB_PATH)


async def _ensure_conn():
    global _conn
    if _conn is None:
        _conn = await asyncio.to_thread(_open_sync_conn)
        if _TURSO_ENABLED and not _turso_broken:
            try:
                await asyncio.to_thread(_conn.sync)
                logger.info("Turso bilan dastlabki sinxronizatsiya muvaffaqiyatli.")
            except Exception:
                logger.exception(
                    "Turso bilan dastlabki sinxronizatsiya muvaffaqiyatsiz tugadi - "
                    "mahalliy nusxa bilan davom etiladi (keyingi urinishlarda tuzalishi mumkin)."
                )
    return _conn


class _CursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    async def fetchone(self):
        row = await asyncio.to_thread(self._cursor.fetchone)
        return _wrap_row(row, self._cursor.description)

    async def fetchall(self):
        rows = await asyncio.to_thread(self._cursor.fetchall)
        description = self._cursor.description
        return [_wrap_row(r, description) for r in rows]

    @property
    def lastrowid(self):
        return self._cursor.lastrowid


class _ConnWrapper:
    def __init__(self, conn):
        self._conn = conn
        self.row_factory = None  # moslik uchun - aslida hech narsa qilmaydi

    async def execute(self, sql, params=()):
        cursor = await asyncio.to_thread(self._conn.execute, sql, params)
        return _CursorWrapper(cursor)

    async def executescript(self, sql):
        await asyncio.to_thread(self._conn.executescript, sql)

    async def commit(self):
        await asyncio.to_thread(self._conn.commit)
        if _TURSO_ENABLED and not _turso_broken:
            try:
                await asyncio.to_thread(self._conn.sync)
            except Exception:
                # Yozuvning o'zi mahalliy nusxada muvaffaqiyatli saqlandi -
                # faqat bulutga sinxronlash kechikdi (masalan vaqtincha
                # tarmoq muammosi). Davriy sinxronlash (start_periodic_sync)
                # buni tez orada tuzatadi, shuning uchun bu yerda xatoni
                # ko'tarib, foydalanuvchining butun so'rovini buzmaymiz.
                logger.exception("Turso'ga sinxronlashda vaqtinchalik xatolik.")


class _ConnCtx:
    async def __aenter__(self):
        await _lock.acquire()
        conn = await _ensure_conn()
        return _ConnWrapper(conn)

    async def __aexit__(self, exc_type, exc, tb):
        _lock.release()
        return False


def get_db_connection() -> _ConnCtx:
    """`async with aiosqlite.connect(DB_PATH) as conn:` o'rnini bosadi."""
    return _ConnCtx()


async def start_periodic_sync(interval_seconds: int = 25):
    """Fonda doimiy ishlaydigan qo'shimcha xavfsizlik chorasi: har commit'dan
    keyingi sinxronlash allaqachon ishlaydi, lekin agar u vaqtincha
    muvaffaqiyatsiz tugasa (masalan tarmoq uzilib qolsa), shu davriy vazifa
    keyingi urinishda baribir bulutga yetkazib beradi. Turso sozlanmagan
    bo'lsa, yoki dastlabki ulanish allaqachon muvaffaqiyatsiz tugagan bo'lsa
    (masalan noto'g'ri token - qayta urinib, loglarni "ifloslashning" hojati
    yo'q, chunki token faqat qayta deploy qilingandagina o'qib olinadi),
    hech narsa qilmaydi."""
    if not _TURSO_ENABLED:
        return
    while True:
        await asyncio.sleep(interval_seconds)
        if _turso_broken:
            continue
        try:
            conn = await _ensure_conn()
            await asyncio.to_thread(conn.sync)
        except Exception:
            logger.exception("Davriy Turso sinxronlashda xatolik.")
