"""
Botning asosiy ishga tushirish fayli.

Bu fayl ikki xil rejimda ishlashi mumkin - hech narsa qo'lda o'zgartirish shart emas,
u avtomatik aniqlanadi:

1) POLLING rejimi - mahalliy kompyuteringizda sinaganda ishlatiladi.
   Bunda internetdan doimiy so'rov yuborib turadi, alohida domen/SSL kerak emas.

2) WEBHOOK rejimi - Render.com'da ishga tushirilganda avtomatik yoqiladi
   (Render RENDER_EXTERNAL_URL degan sozlamani o'zi qo'yib beradi).
   Bunda Telegram to'g'ridan-to'g'ri serverimizga xabar yuboradi - tezroq va
   doimiy serverlar uchun tavsiya etiladigan usul.
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

import db
from config import BOT_TOKEN, RENDER_EXTERNAL_URL, PORT, WEBAPP_URL
from handlers import all_routers
from webapp_api import register_webapp_routes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("figo3d_bot")

WEBHOOK_PATH = "/webhook"
WEBAPP_INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webapp", "index.html")


async def on_startup(bot: Bot):
    await db.init_db()
    if RENDER_EXTERNAL_URL:
        webhook_url = RENDER_EXTERNAL_URL.rstrip("/") + WEBHOOK_PATH
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info("Webhook rejimi yoqildi: %s", webhook_url)
        if WEBAPP_URL:
            try:
                await bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(text="🛍 Do'kon", web_app=WebAppInfo(url=WEBAPP_URL))
                )
                logger.info("Veb-do'kon (Mini App) menyu tugmasi yoqildi: %s", WEBAPP_URL)
            except Exception:
                logger.exception("Menyu tugmasini o'rnatib bo'lmadi (muhim emas, bot ishlashda davom etadi).")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Polling rejimida ishga tushmoqda (mahalliy sinov).")


async def health_check(request: web.Request) -> web.Response:
    """Render bu manzilga vaqti-vaqti bilan so'rov yuborib, server tirikligini tekshiradi."""
    return web.Response(text="Figo3D bot ishlayapti ✅")


def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    for router in all_routers:
        dp.include_router(router)
    dp.startup.register(on_startup)
    return bot, dp


def build_web_app(bot: Bot, dp: Dispatcher) -> web.Application:
    """aiohttp ilovasini yig'adi: webhook, health-check va veb-do'kon
    (Mini App sahifasi + API) - bularning barchasi bitta server ichida
    ishlaydi, shuning uchun Mini App'ning API'ga so'rovlari CORS muammosiz
    ishlaydi (bir xil manzildan)."""
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/", health_check)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    register_webapp_routes(app, WEBAPP_INDEX_PATH)
    return app


def run_webhook(bot: Bot, dp: Dispatcher):
    app = build_web_app(bot, dp)
    web.run_app(app, host="0.0.0.0", port=PORT)


def main():
    bot, dp = create_bot_and_dispatcher()
    if RENDER_EXTERNAL_URL:
        run_webhook(bot, dp)
    else:
        asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
