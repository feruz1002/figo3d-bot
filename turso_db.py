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
import glob
import logging
import os

import libsql

from config import DB_PATH, TURSO_AUTH_TOKEN, TURSO_DATABASE_URL

logger = logging.getLogger("figo3d_bot.db")

_TURSO_ENABLED = bool(TURSO_DATABASE_URL and TURSO_AUTH_TOKEN)
_turso_broken = False  # dastlabki ulanish muvaffaqiyatsiz tugasa True bo'ladi

_conn = None
_lock = asyncio.Lock()
_ever_connected = False  # birinchi ulanish allaqachon o'rnatilganmi (reconnectni aniqlash uchun)
_schema_ensure_hook = None  # db.py ro'yxatdan o'tkazadi (set_schema_ensure_hook)


def set_schema_ensure_hook(hook):
    """db.py o'zining `_ensure_schema(conn)` funksiyasini shu yerga (import
    vaqtida, module darajasida) ro'yxatdan o'tkazadi. Nima uchun kerak:
    agar mahalliy Turso replika fayli ISH VAQTIDA (process qayta ishga
    tushmasdan) buzilib, avtomatik tiklansa (pastdagi
    `_reset_connection_after_corruption`), YANGI ulanish Turso bulutidan
    to'liq qaytadan sinxronlanadi - lekin bulutdagi nusxa ayrim jadvallarni
    "ko'rmagan" bo'lishi mumkin (masalan mahalliy fayl bulutga TO'LIQ push
    qilinmasdan turib buzilgan bo'lsa) - production'da aynan shu sabab bilan
    "no such table: task_submissions" kabi xatolar chiqqan. Shuning uchun
    HAR bir QAYTA ulanishda (birinchi ulanishda EMAS - buni `db.init_db()`
    alohida, startup'da ta'minlaydi) sxema shu yerning o'zida qayta
    tekshiriladi/to'ldiriladi - process qayta ishga tushishini kutmasdan."""
    global _schema_ensure_hook
    _schema_ensure_hook = hook


def is_cloud_backup_unavailable() -> bool:
    """1-sentyabr (foydalanuvchi so'rovi, real production hodisasiga
    javoban): Turso SOZLANGAN, lekin HOZIRGI ulanish shu bulutga
    ULANOLMAYAPTI (masalan vaqtinchalik tarmoq xatosi yoki yuqoridagi
    "-info" fayl muammosi kabi holat) bo'lsa - True qaytaradi. db.py
    shu yerdan foydalanib, SHU HOLATDA bo'sh (mahalliy, hali Turso'dan
    sinxronlanmagan) products jadvalini "haqiqatan ham bo'sh" deb
    NOTO'G'RI xulosa chiqarib, uni SEED_PRODUCTS (namuna mahsulotlar)
    bilan to'ldirib yubormasligi uchun - aks holda haqiqiy mahsulotlar
    o'rniga vaqtincha soxta namuna mahsulotlar ko'rinib qolar edi, va
    Turso tiklangach bu soxta yozuvlar hatto bulutga sinxronlanib,
    haqiqiy ma'lumotlarni "ifloslashi" ham mumkin edi."""
    return _TURSO_ENABLED and _turso_broken


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
    global _conn, _ever_connected
    # MUHIM: `_conn is None` ikki xil holatda bo'ladi - (1) BOTNING ENG
    # BIRINCHI ulanishi (process hozirgina ishga tushdi), yoki (2) QAYTA
    # ulanish (oldingi ulanish buzilgan fayl sababli o'chirilgan va
    # tiklanmoqda). Ikkinchisini aniqlash uchun `_ever_connected` bayrog'i
    # ishlatiladi - faqat SHU holatda sxema pastda avtomatik qayta
    # ta'minlanadi (birinchisida buni `db.init_db()` alohida qiladi).
    is_reconnect = _ever_connected and _conn is None
    if _conn is None:
        _conn = await asyncio.to_thread(_open_sync_conn)
        _ever_connected = True
        if _TURSO_ENABLED and not _turso_broken:
            try:
                await asyncio.to_thread(_conn.sync)
                logger.info("Turso bilan dastlabki sinxronizatsiya muvaffaqiyatli.")
            except Exception:
                logger.exception(
                    "Turso bilan dastlabki sinxronizatsiya muvaffaqiyatsiz tugadi - "
                    "mahalliy nusxa bilan davom etiladi (keyingi urinishlarda tuzalishi mumkin)."
                )
        if is_reconnect and _schema_ensure_hook is not None:
            try:
                await _schema_ensure_hook(_ConnWrapper(_conn))
                logger.info("Qayta ulanishdan keyin sxema qayta ta'minlandi (ensure_schema).")
            except Exception:
                logger.exception(
                    "Qayta ulanishdan keyin sxemani ta'minlashda (ensure_schema) xatolik."
                )
    return _conn


_CORRUPTION_SIGNATURES = (
    "file is not a database",
    "database disk image is malformed",
    "database is corrupted",
    "malformed database schema",
)


def _looks_like_corruption(exc: Exception) -> bool:
    """Mahalliy replika fayli buzilganda libsql/sqlite chiqaradigan xato
    matnlarini aniqlaydi (masalan `ValueError: file is not a database`)."""
    msg = str(exc).lower()
    return any(sig in msg for sig in _CORRUPTION_SIGNATURES)


# 31-avgust (real production hodisasi asosida): bot.py'ning on_startup
# funksiyasi `db.init_db()` chaqirganda AYNAN shu turdagi xatoni (masalan
# server oldin to'satdan o'chirilgani sabab fayl buzilgan bo'lsa) tutib,
# darhol (Render jarayonni qayta ishga tushirishini kutmasdan) qayta
# urinishi uchun ochiq (public) nom bilan ham chiqaramiz.
is_corruption_error = _looks_like_corruption


async def _reset_connection_after_corruption():
    """Mahalliy replika fayli buzilganini aniqlagach chaqiriladi: eski
    (buzilgan) ulanishni yopib, `_conn`ni `None`ga qaytaradi - shu bilan
    KEYINGI so'rov `_ensure_conn()` orqali TOZA ulanish ochadi. Agar Turso
    sozlangan bo'lsa (ya'ni bulutda ishonchli nusxa bor), buzilgan mahalliy
    faylni (va uning -wal/-shm/-journal yordamchi fayllarini) o'chirib
    tashlaymiz - shunda keyingi ulanish uni Turso bulutidan qaytadan to'liq
    yuklab oladi (avtomatik "davolanish").

    MUHIM (xavfsizlik): Turso sozlanMAGAN bo'lsa (bulutda zaxira yo'q),
    faylni HECH QACHON o'chirmaymiz - aks holda do'konning YAGONA
    ma'lumotlar nusxasini butunlay yo'q qilib qo'yamiz. Bu holda faqat
    xatoni "critical" darajada logga yozamiz, qo'lda tiklash (backup'dan)
    kerak bo'ladi."""
    global _conn
    old_conn = _conn
    _conn = None
    if old_conn is not None:
        try:
            await asyncio.to_thread(old_conn.close)
        except Exception:
            pass  # eski ulanish allaqachon buzilgan bo'lishi mumkin - muhim emas

    if not (_TURSO_ENABLED and not _turso_broken):
        logger.critical(
            "MAHALLIY MA'LUMOTLAR BAZASI FAYLI BUZILDI ('file is not a database' "
            "yoki shunga o'xshash xato), LEKIN Turso sozlanmagan (yoki ulanish "
            "avval buzilgan edi) - shuning uchun faylni AVTOMATIK o'chirib "
            "bo'lmaydi (bu YAGONA ma'lumot nusxasini yo'qotishi mumkin edi). "
            "Bot ehtimol ishlamay qoladi - qo'lda tekshirish/tiklash (yoki "
            "TURSO_DATABASE_URL/TURSO_AUTH_TOKEN sozlab qayta deploy qilish) kerak."
        )
        return

    deleted_any = False
    # MUHIM (1-sentyabr, real production hodisasiga javoban): "file is not
    # a database" xatosidan keyin faqat ASOSIY .db faylini (va -wal/-shm/
    # -journal'ni) o'chirish YETARLI EMAS ekan - libsql "embedded replica"
    # rejimida sinxronlash holatini kuzatib turuvchi QO'SHIMCHA "-info"
    # metadata faylini HAM saqlaydi. Agar shu "-info" fayli QOLIB ketsa
    # (faqat asosiy fayl o'chirilsa), KEYINGI ulanish "invalid local
    # state: metadata file exists but db file does not" xatosi bilan
    # butunlay ULANIB BO'LMAY QOLADI - aynan shu sabab bilan 1-sentyabrda
    # Turso butunlay uzilib, bot bir muddat Turso'siz ("oddiy mahalliy
    # fayl", ya'ni bo'sh/sinxronlanmagan holatda) ishlab qolgan edi.
    known_suffixes = ("", "-wal", "-shm", "-journal", "-info")
    for suffix in known_suffixes:
        path = DB_PATH + suffix
        try:
            if os.path.exists(path):
                os.remove(path)
                deleted_any = True
        except Exception:
            logger.exception("Buzilgan mahalliy faylni o'chirishda xatolik: %s", path)

    # Qo'shimcha xavfsizlik to'ri: yuqoridagi ANIQ ro'yxatdan tashqari,
    # DB_PATH bilan boshlanadigan QOLGAN BARCHA yordamchi fayllarni ham
    # (masalan libsql kelajakda yangi turdagi metadata fayl qo'shib
    # qo'ysa) tozalaymiz - shunda xuddi shu turdagi uzilish boshqa
    # noma'lum sidecar fayl tufayli qaytalanmaydi.
    known_paths = {DB_PATH + s for s in known_suffixes}
    try:
        for path in glob.glob(DB_PATH + "*"):
            if path in known_paths:
                continue
            try:
                os.remove(path)
                deleted_any = True
                logger.warning("Qo'shimcha (oldindan kutilmagan) yordamchi fayl ham o'chirildi: %s", path)
            except Exception:
                logger.exception("Qo'shimcha yordamchi faylni o'chirishda xatolik: %s", path)
    except Exception:
        logger.exception("Yordamchi fayllarni (glob orqali) qidirishda xatolik.")

    logger.error(
        "Mahalliy ma'lumotlar bazasi replikasi BUZILGAN edi ('file is not a "
        "database') - buzilgan fayl(lar) o'chirildi (deleted_any=%s), keyingi "
        "so'rovda ulanish Turso bulutidan qaytadan to'liq sinxronlanadi. "
        "Ma'lumotlar xavfsiz (Turso'da saqlangan), faqat shu bir so'rov "
        "muvaffaqiyatsiz tugaydi.",
        deleted_any,
    )


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
        try:
            conn = await _ensure_conn()
        except Exception as exc:
            # DIQQAT: agar `_ensure_conn()`ning O'ZI xato bersa (masalan
            # ulanish ochilayotganda "file is not a database"), `__aexit__`
            # HECH QACHON chaqirilmaydi (Python'ning async context manager
            # qoidasi shunday) - shuning uchun bu yerda ham buzilishni
            # aniqlab, tozalab, keyin `_lock`ni albatta bo'shatishimiz kerak.
            if _looks_like_corruption(exc):
                await _reset_connection_after_corruption()
            _lock.release()
            raise
        return _ConnWrapper(conn)

    async def __aexit__(self, exc_type, exc, tb):
        # `async with get_db_connection() as conn:` blokining ICHIDA
        # (execute/fetchone/fetchall/commit/sync paytida) chiqqan har qanday
        # xato shu yerga keladi - shu jumladan replika buzilishi. Aniqlansa,
        # keyingi so'rov toza ulanish olishi uchun tozalaymiz; asl xatoni esa
        # baribir yuqoriga (joriy so'rovga) qaytaramiz - False qaytarish shuni
        # bildiradi.
        if exc is not None and _looks_like_corruption(exc):
            try:
                await _reset_connection_after_corruption()
            except Exception:
                logger.exception("Ulanishni tiklashda (corruption reset) qo'shimcha xatolik.")
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
    hech narsa qilmaydi.

    MUHIM (xato tuzatildi): bu funksiya ILGARI `_lock`ni OLMASDAN to'g'ridan-
    to'g'ri `conn.sync()` chaqirar edi. Shu payt aynan shu `_conn` obyekti
    ustida (boshqa oqimda) bir vaqtning o'zida `execute`/`fetchall`/`commit`
    ishlab turgan bo'lishi mumkin edi (masalan mijoz "/api/cart" so'rovi
    yuborgan payt) - `libsql`/SQLite ulanishi bir nechta OS-thread'dan BIR
    VAQTDA ishlatilishi xavfsiz emas va mahalliy replika faylini buzib
    qo'yishi mumkin edi (production'da aynan shu sabab bilan
    `ValueError: file is not a database` xatosi chiqqan va savat/checkout
    "qotib qolgan" edi). Endi `_ConnCtx` bilan bir xil `_lock` orqali
    himoyalanadi - shu bilan sinxronlash va so'rovlar hech qachon bir vaqtda
    bitta ulanishga tegmaydi."""
    if not _TURSO_ENABLED:
        return
    while True:
        await asyncio.sleep(interval_seconds)
        if _turso_broken:
            continue
        try:
            async with _lock:
                conn = await _ensure_conn()
                await asyncio.to_thread(conn.sync)
        except Exception as exc:
            logger.exception("Davriy Turso sinxronlashda xatolik.")
            if _looks_like_corruption(exc):
                await _reset_connection_after_corruption()
