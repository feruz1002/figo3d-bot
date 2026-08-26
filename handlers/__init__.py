"""Barcha routerlarni bir joyga yig'ib, bot.py'ga qulay import qilish uchun.

DIQQAT: tartib muhim! menu_guard_router har doim BIRINCHI bo'lishi kerak -
u foydalanuvchi jarayon o'rtasida menyu tugmasini bossa, holatni to'g'ri
tozalab, keyingi routerlarga o'tkazib beradi (handlers/menu_guard.py'dagi
izohga qarang)."""
from handlers.menu_guard import menu_guard_router
from handlers.admin_tools import admin_tools_router
from handlers.start import start_router
from handlers.catalog import catalog_router
from handlers.cart import cart_router
from handlers.checkout import checkout_router
from handlers.reviews import reviews_router
from handlers.custom_order import custom_router
from handlers.orders_history import orders_router
from handlers.contact import contact_router
from handlers.admin import admin_router

all_routers = [
    menu_guard_router,
    admin_tools_router,
    start_router,
    catalog_router,
    cart_router,
    checkout_router,
    reviews_router,
    custom_router,
    orders_router,
    contact_router,
    admin_router,
]
