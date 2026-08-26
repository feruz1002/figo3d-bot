"""
DIQQAT: Bu fayl endi FAQAT bot birinchi marta ishga tushganda bazani
"dastlabki namuna" mahsulotlar bilan to'ldirish uchun ishlatiladi (SEED_PRODUCTS).

Mahsulot qo'shish/o'chirish endi bu faylni tahrirlash orqali EMAS, balki
to'g'ridan-to'g'ri botning o'zidan, admin sifatida /admin buyrug'ini yozib
amalga oshiriladi - rasm ham shu yerdan, botga yuborish orqali qo'shiladi.
Bu ancha ishonchli: qo'lda file_id nusxalab, kodga joylab, GitHub'ga yuklab,
qayta deploy qilishda xato qilish yoki eski nusxani tasodifan yuklab, avval
qo'shilgan rasmlarni "yo'qotib qo'yish" xavfi endi yo'q - hammasi bazada
saqlanadi va kod bilan hech qanday aloqasi yo'q.
"""

SEED_PRODUCTS = [
    {
        "category": "Haykalchalar",
        "name": "Anime qahramon haykalchasi",
        "description": "15 sm balandlik, PLA plastik, qo'lda bo'yaladi",
        "price": 120000,
    },
    {
        "category": "Haykalchalar",
        "name": "Shaxsiy portret haykalcha",
        "description": "Sizning rasmingiz asosida shaxsiylashtirilgan haykalcha, 12 sm",
        "price": 180000,
    },
    {
        "category": "Kalitchalar",
        "name": "Ismli kalitcha",
        "description": "Istalgan ism yoki so'z bilan, rangli plastik",
        "price": 35000,
    },
    {
        "category": "Sovg'alar",
        "name": "To'y uchun figurka (kelin-kuyov)",
        "description": "To'y stoli uchun maxsus buyurtma, 20 sm",
        "price": 250000,
    },
    {
        "category": "Sovg'alar",
        "name": "Tug'ilgan kun sovg'a to'plami",
        "description": "Kichik haykalcha + ismli kalitcha to'plami",
        "price": 140000,
    },
    {
        "category": "Uy dekori",
        "name": "Lampa asosi (geometrik)",
        "description": "Zamonaviy dizayndagi stol lampasi asosi",
        "price": 95000,
    },
]
