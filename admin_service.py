"""Admin amallari (buyurtmani qabul qilish, hisob to'ldirishni
tasdiqlash/rad etish, shaxsiy buyurtma bo'yicha bog'lanilgani belgilash) -
bu mantiq endi ham chatdagi tugmalar (handlers/admin.py), ham admin
veb-panel (admin_webapp_api.py) orqali ISHLATILADI, shu bilan ikkalasi
doim bir xil qoidalar bilan (masalan status "kutilmoqda" bo'lmasa qayta
tasdiqlanmaydi) ishlaydi."""
import db
import order_service
from handlers.catalog import format_price


async def accept_order(order_id: int):
    """Qaytaradi: (order, None) muvaffaqiyatda, yoki (None, sabab).
    Admin panelning "🆕 Qabul qilish" bo'limidagi amal - buyurtma shu bilan
    "🛠 Yig'ish" bo'limiga o'tadi (STATUS_ACCEPTED)."""
    order = await db.get_order(order_id)
    if not order:
        return None, "not_found"
    await db.update_order_status(order_id, order_service.STATUS_ACCEPTED)
    return order, None


async def notify_customer_order_accepted(bot, order):
    try:
        await bot.send_message(
            order["user_id"], f"✅ Buyurtmangiz #{order['id']} qabul qilindi va tayyorlanmoqda!"
        )
    except Exception:
        pass


async def ship_order(order_id: int):
    """Admin panelning "🛠 Yig'ish" bo'limidagi amal - buyurtma "🚚 Chiqarib
    yuborilgan" bo'limiga o'tadi."""
    order = await db.get_order(order_id)
    if not order:
        return None, "not_found"
    await db.update_order_status(order_id, order_service.STATUS_SHIPPED)
    return order, None


async def notify_customer_order_shipped(bot, order):
    try:
        await bot.send_message(
            order["user_id"],
            f"🚚 Buyurtmangiz #{order['id']} chiqarib yuborildi — tez orada yetib boradi!",
        )
    except Exception:
        pass


async def archive_order(order_id: int):
    """Admin panelning "🚚 Chiqarib yuborilgan" bo'limidagi "✅ Yetkazildi"
    amali - buyurtma "📁 Arxiv"ga o'tadi (yakunlangan)."""
    order = await db.get_order(order_id)
    if not order:
        return None, "not_found"
    await db.update_order_status(order_id, order_service.STATUS_ARCHIVED)
    return order, None


async def notify_customer_order_archived(bot, order):
    try:
        await bot.send_message(
            order["user_id"], f"📦 Buyurtmangiz #{order['id']} yetkazildi. Xaridingiz uchun rahmat!"
        )
    except Exception:
        pass


async def flag_order_problem(order_id: int, reason: str | None = None):
    """Buyurtmada muammo bo'lsa (masalan mijoz bilan bog'lanib bo'lmayapti,
    mahsulot yo'q va h.k.) - istalgan faol bosqichdan "⚠️ Muammo"ga
    o'tkazish uchun. Admin panelda bu amal "🆕 Qabul qilish", "🛠 Yig'ish"
    va "🚚 Chiqarib yuborilgan" bo'limlarining barchasida mavjud.
    `reason` - admin yozgan qisqa izoh (ixtiyoriy, None bo'lishi mumkin)."""
    order = await db.get_order(order_id)
    if not order:
        return None, "not_found"
    await db.set_order_problem(order_id, order_service.STATUS_PROBLEM, reason)
    # Yangilangan (sabab yozilgan) buyurtmani qaytaramiz, shu bilan
    # chaqiruvchi (handlers/admin.py, admin_webapp_api.py) darhol
    # order["problem_reason"]dan foydalana oladi.
    return await db.get_order(order_id), None


async def notify_customer_order_problem(bot, order):
    reason = (order or {}).get("problem_reason")
    text = f"⚠️ Buyurtmangiz #{order['id']} bo'yicha savol/muammo yuzaga keldi — tez orada operator siz bilan bog'lanadi."
    if reason:
        text += f"\n\n📝 Sabab: {reason}"
    try:
        await bot.send_message(order["user_id"], text)
    except Exception:
        pass


async def get_dashboard_stats() -> dict:
    """Admin panelning "📊 Statistika" bo'limi uchun umumiy ko'rsatkichlar:
    botni ko'rgan/xarid qilgan odamlar soni, jami buyurtmalar, eng ko'p
    buyurtma qilinayotgan mahsulotlar, viloyat bo'yicha taqsimot (manzil
    matnidan taxminan aniqlangan) va pul bo'yicha to'liq hisobot (jami,
    arxivlangan, kutilayotgan, bugun/hafta/oy, to'lov usuli bo'yicha)."""
    total_users, customers, order_count, top_products, addresses, revenue = (
        await db.get_total_bot_users(),
        await db.get_customer_count(),
        await db.get_order_count(),
        await db.get_top_products(limit=8),
        await db.get_all_order_addresses(),
        await db.get_revenue_report(),
    )

    region_counts: dict[str, int] = {}
    for address in addresses:
        region = order_service.guess_region(address)
        region_counts[region] = region_counts.get(region, 0) + 1
    # "Aniqlanmadi" ro'yxat oxirida chiqsin (aniq viloyatlar avval ko'rinsin)
    regions_sorted = sorted(
        region_counts.items(), key=lambda kv: (kv[0] == "Aniqlanmadi", -kv[1])
    )

    # Frontend uchun to'lov usuli kodlarini o'qiladigan nomga aylantiramiz
    revenue_by_payment = [
        {
            "method": item["method"],
            "label": order_service.PAYMENT_METHOD_REPORT_LABELS.get(
                item["method"], item["method"]
            ),
            "count": item["count"],
            "total": item["total"],
        }
        for item in revenue.get("by_payment", [])
    ]

    return {
        "total_users": total_users,
        "customers": customers,
        "order_count": order_count,
        "top_products": top_products,
        "regions": [{"name": name, "count": count} for name, count in regions_sorted],
        "revenue": {
            "total": revenue["total"],
            "archived_total": revenue["archived_total"],
            "pending_total": revenue["pending_total"],
            "today_total": revenue["today_total"],
            "week_total": revenue["week_total"],
            "month_total": revenue["month_total"],
            "order_count": revenue["order_count"],
            "average_order_value": revenue["average_order_value"],
            "by_payment": revenue_by_payment,
        },
    }


async def mark_custom_order_contacted(custom_order_id: int):
    order = await db.get_custom_order(custom_order_id)
    if not order:
        return None, "not_found"
    await db.update_custom_order_status(custom_order_id, "bog'lanildi")
    return order, None


async def approve_topup(request_id: int, amount: int | None = None):
    """Qaytaradi: (request, new_balance, None) muvaffaqiyatda, yoki
    (None, None, sabab) - sabab "not_found", "already_processed" yoki
    "invalid_amount".

    MUHIM (29-avgust, foydalanuvchi so'rovi): `amount` berilsa - mijoz
    SO'RAGAN summa (`req["amount"]`) o'rniga aynan SHU summa hamyonga
    qo'shiladi. Bu skrinshotda/tranzaksiyada ko'rsatilgan summa so'ralgan
    summadan farq qilganda (kam/ko'p tushgan yoki tranzaksiyada xatolik
    bo'lganda) admin haqiqiy summani qo'lda kiritib tasdiqlashi uchun -
    handlers/admin.py ("✏️ Boshqa summa") va admin_webapp_api.py'ga
    qarang."""
    req = await db.get_topup_request(request_id)
    if not req:
        return None, None, "not_found"
    if req["status"] != "kutilmoqda":
        return None, None, "already_processed"

    final_amount = req["amount"] if amount is None else amount
    if not isinstance(final_amount, int) or final_amount <= 0:
        return None, None, "invalid_amount"

    new_balance = await db.adjust_balance(req["user_id"], final_amount)
    await db.update_topup_status(request_id, "tasdiqlandi", approved_amount=final_amount)
    req = dict(req)
    req["approved_amount"] = final_amount
    return req, new_balance, None


async def notify_customer_topup_approved(bot, req, new_balance):
    approved = req.get("approved_amount") or req["amount"]
    requested = req["amount"]
    # Agar admin so'ralganidan FARQLI summa tasdiqlagan bo'lsa (masalan
    # tranzaksiyada kam/ko'p tushgan) - mijoz nega summa farqli ekanini
    # tushunishi uchun buni ANIQ aytib o'tamiz, jimgina qoldirmaymiz.
    note = ""
    if approved != requested:
        note = (
            f"\n\nℹ️ Siz {format_price(requested)} so'm so'ragan edingiz, "
            f"lekin to'lov tafsilotlariga ko'ra {format_price(approved)} so'm tasdiqlandi. "
            "Savol bo'lsa, operator bilan bog'laning."
        )
    try:
        await bot.send_message(
            req["user_id"],
            f"✅ Hisobingiz {format_price(approved)} so'mga to'ldirildi!{note}\n"
            f"💰 Joriy balans: {format_price(new_balance)} so'm",
        )
    except Exception:
        pass


async def manual_balance_adjust(user_id: int, delta: int, note: str | None = None):
    """29-avgust: admin panelidan, HECH QANDAY topup so'roviga bog'liq
    bo'lmagan holda, istalgan mijozning hamyoniga to'g'ridan-to'g'ri pul
    qo'shish/ayirish uchun (masalan tranzaksiyada xatolik bo'lib, lekin
    hech qanday so'rov yaratilmagan holatlar uchun). Faqat botni kamida
    bir marta ko'rgan (users jadvalida yozuvi bor) foydalanuvchilar uchun
    ishlaydi - tasodifiy/noto'g'ri ID kiritilganda xato qaytaradi.
    Qaytaradi: (new_balance, None) yoki (None, "not_found")."""
    profile = await db.get_user_profile(user_id)
    if not profile:
        return None, "not_found"
    new_balance = await db.adjust_balance(user_id, delta)
    return new_balance, None


async def notify_customer_balance_adjusted(bot, user_id: int, delta: int, new_balance: int, note: str | None):
    sign = "+" if delta >= 0 else "−"
    note_line = f"\nIzoh: {note}" if note else ""
    try:
        await bot.send_message(
            user_id,
            f"💰 Hamyoningizga o'zgartirish kiritildi: {sign}{format_price(abs(delta))} so'm.{note_line}\n"
            f"Joriy balans: {format_price(new_balance)} so'm",
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
