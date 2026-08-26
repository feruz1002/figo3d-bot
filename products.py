"""
Mahsulotlar katalogi.

Bu yerga o'zingizning haqiqiy mahsulotlaringizni qo'shishingiz mumkin - dasturlash
bilmasangiz ham, quyidagi ro'yxatga o'xshatib yangi qator qo'shsangiz yetarli.

Har bir mahsulot quyidagi maydonlarga ega:
  id          - takrorlanmas raqam (har bir mahsulotda boshqacha bo'lishi shart)
  category    - qaysi bo'limga tegishli (Katalog menyusida shu nom bilan chiqadi)
  name        - mahsulot nomi
  description - qisqacha tavsif
  price       - narxi (so'mda, oddiy son)
  photos      - rasmlar RO'YXATI (0 tadan 10 tagacha). Mijoz mahsulotni turli
                burchaklardan ko'rishi uchun 2-3 ta rasm qo'shish tavsiya etiladi.
                Bo'sh ro'yxat [] - rasmsiz, matn ko'rinishida chiqadi.
                Rasm qo'shish uchun: rasmni Telegram'da botga yuboring, botdan
                qaytgan "file_id"ni shu yerga yozing, YOKI internetdagi rasm
                havolasini (https://...) shu yerga qo'ying.
                Masalan: "photos": ["https://.../old.jpg", "https://.../orqa.jpg"]
  video       - (ixtiyoriy) mahsulotni aylantirib olingan qisqa video/GIF.
                file_id yoki havola. Yo'q bo'lsa None qoldiring.
                Bu "3D his" beradi - mijoz buyumni har tomondan ko'radi.
"""

PRODUCTS = [
    {
        "id": 1,
        "category": "Haykalchalar",
        "name": "Anime qahramon haykalchasi",
        "description": "15 sm balandlik, PLA plastik, qo'lda bo'yaladi",
        "price": 120000,
        "photos": [],
        "video": None,
    },
    {
        "id": 2,
        "category": "Haykalchalar",
        "name": "Shaxsiy portret haykalcha",
        "description": "Sizning rasmingiz asosida shaxsiylashtirilgan haykalcha, 12 sm",
        "price": 180000,
        "photos": [],
        "video": None,
    },
    {
        "id": 3,
        "category": "Kalitchalar",
        "name": "Ismli kalitcha",
        "description": "Istalgan ism yoki so'z bilan, rangli plastik",
        "price": 35000,
        "photos": [],
        "video": None,
    },
    {
        "id": 4,
        "category": "Sovg'alar",
        "name": "To'y uchun figurka (kelin-kuyov)",
        "description": "To'y stoli uchun maxsus buyurtma, 20 sm",
        "price": 250000,
        "photos": [],
        "video": None,
    },
    {
        "id": 5,
        "category": "Sovg'alar",
        "name": "Tug'ilgan kun sovg'a to'plami",
        "description": "Kichik haykalcha + ismli kalitcha to'plami",
        "price": 140000,
        "photos": [],
        "video": None,
    },
    {
        "id": 6,
        "category": "Uy dekori",
        "name": "Lampa asosi (geometrik)",
        "description": "Zamonaviy dizayndagi stol lampasi asosi",
        "price": 95000,
        "photos": [],
        "video": None,
    },
]


def get_categories():
    """Barcha noyob kategoriyalar ro'yxatini qaytaradi (tartib saqlangan holda)."""
    seen = []
    for p in PRODUCTS:
        if p["category"] not in seen:
            seen.append(p["category"])
    return seen


def get_products_by_category(category: str):
    return [p for p in PRODUCTS if p["category"] == category]


def get_product_by_id(product_id: int):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None
