"""Admin amallari (buyurtmani qabul qilish, hisob to'ldirishni
tasdiqlash/rad etish, shaxsiy buyurtma bo'yicha bog'lanilgani belgilash) -
bu mantiq endi ham chatdagi tugmalar (handlers/admin.py), ham admin
veb-panel (admin_webapp_api.py) orqali ISHLATILADI, shu bilan ikkalasi
doim bir xil qoidalar bilan (masalan status "kutilmoqda" bo'lmasa qayta
tasdiqlanmaydi) ishlaydi."""
import db
from handlers.catalog import format_price


async def accept_order(order_id: int):
    """Qaytaradi: (order, None) muvaffaqiyatda, yoki (None, sabab)."""
    order = await db.get_order(order_id)
    if not order:
        return None, "not_found"
    await db.update_order_status(order_id, "qabul qilindi")
    return order, None


async def notify_customer_order_accepted(bot, order):
    try:
        await bot.send_message(
            order["user_id"], f"✅ Buyurtmangiz #{order['id']} qabul qilindi va tayyorlanmoqda!"
        )
    except Exception:
        pass


async def mark_custom_order_contacted(custom_order_id: int):
    order = await db.get_custom_order(custom_order_id)
    if not order:
        return None, "not_found"
    await db.update_custom_order_status(custom_order_id, "bog'lanildi")
    return order, None


async def approve_topup(request_id: int):
    """Qaytaradi: (request, new_balance, None) muvaffaqiyatda, yoki
    (None, None, sabab) - sabab "not_found" yoki "already_processed"."""
    req = await db.get_topup_request(request_id)
    if not req:
        return None, None, "not_found"
    if req["status"] != "kutilmoqda":
        return None, None, "already_processed"
    new_balance = await db.adjust_balance(req["user_id"], req["amount"])
    await db.update_topup_status(request_id, "tasdiqlandi")
    return req, new_balance, None


async def notify_customer_topup_approved(bot, req, new_balance):
    try:
        await bot.send_message(
            req["user_id"],
            f"✅ Hisobingiz {format_price(req['amount'])} so'mga to'ldirildi!\n"
            f"💰 Joriy balans: {format_price(new_balance)} so'm",
        )
    except Exception:
        pass


async def reject_topup(request_id: int):
    req = await db.get_topup_request(request_id)
    if not req:
        return None, "not_found"
    if req["status"] != "kutilmoqda":
        return None, "already_processed"
    await db.update_topup_status(request_id, "rad etildi")
    return req, None


async def notify_customer_topup_rejected(bot, req):
    try:
        await bot.send_message(
            req["user_id"],
            "❌ Hisobni to'ldirish so'rovingiz rad etildi. Savol bo'lsa, operator bilan bog'laning.",
        )
    except Exception:
        pass
