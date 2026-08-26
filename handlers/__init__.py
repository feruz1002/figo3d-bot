"""Barcha routerlarni bir joyga yig'ib, bot.py'ga qulay import qilish uchun."""
from handlers.start import start_router
from handlers.catalog import catalog_router
from handlers.cart import cart_router
from handlers.checkout import checkout_router
from handlers.orders_history import orders_router
from handlers.contact import contact_router
from handlers.admin import admin_router

all_routers = [
    start_router,
    catalog_router,
    cart_router,
    checkout_router,
    orders_router,
    contact_router,
    admin_router,
]
