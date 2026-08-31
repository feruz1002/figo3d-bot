"""Yetkazib berish (kurer/pochta) xizmatlari bilan bog'liq DOIMIY
ma'lumotlar (31-avgust, foydalanuvchi so'rovi: "mijoz mahsulot narxi
ichida yetkazib berishi deb o'ylamasligi kerak" - endi yetkazib berish
mahsulot narxidan ALOHIDA, aniq ko'rsatilib, qo'shiladi).

Bu yerda FAQAT o'zgarmas ro'yxatlar (qaysi pochta xizmatlari bor, qaysi
hudud qaysi masofa bosqichiga tegishli). Narxlarning o'zi (15 ta katak -
3 pochta x 3 bosqich x (Ofis/Uy)) `db.py`dagi `delivery_prices`
jadvalida saqlanadi va admin panelning "🚚 Yetkazib berish" bo'limida
jadval ko'rinishida tahrirlanadi.

MUHIM: UzPost faqat "ofisdan olib ketish"ni qo'llab-quvvatlaydi (uyga
yetkazib bermaydi) - `home_delivery=False`. BTS va EMU ikkalasini ham
qo'llab-quvvatlaydi."""

COURIERS = [
    {"code": "bts", "name": "BTS", "emoji": "🚀", "home_delivery": True},
    {"code": "emu", "name": "EMU", "emoji": "📮", "home_delivery": True},
    {"code": "uzpost", "name": "UzPost", "emoji": "📯", "home_delivery": False},
]

DELIVERY_TYPE_LABELS = {
    "office": "🏢 Ofisdan olib ketish",
    "home": "🏠 Uyga yetkazish",
}

# 3 bosqichli masofa (foydalanuvchi so'rovi bo'yicha): 1) Toshkent shahri
# ichida, 2) Toshkent shahridan tashqari, o'rtacha uzoqlikdagi hududlar
# (Buxoro viloyatigacha), 3) eng uzoq - Xorazm va Qoraqalpog'iston.
DISTANCE_TIERS = {
    1: "Toshkent shahri ichida",
    2: "Toshkent viloyati va boshqa hududlar (Buxorogacha)",
    3: "Xorazm va Qoraqalpog'iston (eng uzoq)",
}

REGIONS = [
    {"code": "tashkent_city", "name": "Toshkent shahri", "tier": 1},
    {"code": "tashkent_region", "name": "Toshkent viloyati", "tier": 2},
    {"code": "sirdaryo", "name": "Sirdaryo viloyati", "tier": 2},
    {"code": "jizzax", "name": "Jizzax viloyati", "tier": 2},
    {"code": "samarqand", "name": "Samarqand viloyati", "tier": 2},
    {"code": "qashqadaryo", "name": "Qashqadaryo viloyati", "tier": 2},
    {"code": "surxondaryo", "name": "Surxondaryo viloyati", "tier": 2},
    {"code": "navoiy", "name": "Navoiy viloyati", "tier": 2},
    {"code": "buxoro", "name": "Buxoro viloyati", "tier": 2},
    {"code": "fargona", "name": "Farg'ona viloyati", "tier": 2},
    {"code": "andijon", "name": "Andijon viloyati", "tier": 2},
    {"code": "namangan", "name": "Namangan viloyati", "tier": 2},
    {"code": "xorazm", "name": "Xorazm viloyati", "tier": 3},
    {"code": "qoraqalpogiston", "name": "Qoraqalpog'iston Respublikasi", "tier": 3},
]

_COURIER_BY_CODE = {c["code"]: c for c in COURIERS}
_REGION_BY_CODE = {r["code"]: r for r in REGIONS}

# Admin panelidagi jadvalni to'ldirish uchun barcha to'g'ri (courier,
# delivery_type) juftliklari - UzPost uchun faqat "office" bor.
VALID_TYPE_COMBOS = [
    (c["code"], t)
    for c in COURIERS
    for t in (("office", "home") if c["home_delivery"] else ("office",))
]


def get_courier(code):
    return _COURIER_BY_CODE.get(code)


def get_region(code):
    return _REGION_BY_CODE.get(code)


def is_valid_delivery_type(courier_code: str, delivery_type: str) -> bool:
    if delivery_type not in ("office", "home"):
        return False
    courier = get_courier(courier_code)
    if not courier:
        return False
    if delivery_type == "home" and not courier["home_delivery"]:
        return False
    return True


def delivery_label(courier_code: str, delivery_type: str, region_code: str) -> str:
    """Buyurtmaga "suratga olib" saqlanadigan, mijoz/admin uchun tayyor
    o'qiladigan bitta qatorlik matn - masalan:
    "🚀 BTS — 🏠 Uyga yetkazish — Toshkent viloyati"."""
    courier = get_courier(courier_code)
    region = get_region(region_code)
    type_label = DELIVERY_TYPE_LABELS.get(delivery_type, delivery_type or "")
    courier_label = (courier["emoji"] + " " + courier["name"]) if courier else (courier_code or "?")
    region_label = region["name"] if region else (region_code or "?")
    return f"{courier_label} — {type_label} — {region_label}"
