"""Admin (yoki 3D-print hamkor) buyurtmani 'Qabul qildim' deb belgilashi."""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

import db

admin_router = Router()


@admin_router.callback_query(F.data.startswith("order_accept:"))
async def order_accept(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    await db.update_order_status(order_id, "qabul qilindi")

    # html_text - Telegram formatlashini (qalin harflar va h.k.) HTML ko'rinishida qayta tiklaydi
    old_text = callback.message.html_text or ""
    await callback.message.edit_text(old_text + "\n\n✅ <b>Qabul qilindi</b>")

    try:
        await bot.send_message(
            order["user_id"],
            f"✅ Buyurtmangiz #{order_id} qabul qilindi va tayyorlanmoqda!",
        )
    except Exception:
        pass

    await callback.answer("Belgilandi")
