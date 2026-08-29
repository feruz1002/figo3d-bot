"""Admin boshqaruv paneli (Mini App) uchun JSON API.

XAVFSIZLIK: har bir so'rov ikki bosqichda tekshiriladi - (1) Telegram
initData imzosi haqiqiyligi (webapp_auth.validate_init_data - soxta ID
yuborib bo'lmasligi uchun), (2) shu ID config.ADMIN_IDS ro'yxatidami
(is_admin) - ikkalasi ham to'g'ri bo'lmasa 401/403 qaytariladi. Shunday
qilib panelga FAQAT ruxsat etilgan Telegram ID'lar kira oladi, hatto
havolani bilib olgan boshqa odam ham kira olmaydi."""
import base64
from datetime import datetime, timezone

from aiogram.types import BufferedInputFile
from aiohttp import web

import admin_service
import db
import order_service
from admin_notify import notify_all_customers
from config import BOT_TOKEN, is_admin
from webapp_auth import validate_init_data


def _authed_admin_id(request: web.Request):
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    data = validate_init_data(init_data, BOT_TOKEN)
    if not data or not data.get("user"):
        return None
    user_id = data["user"].get("id")
    if not is_admin(user_id):
        return None
    return user_id


def _unauthorized():
    return web.json_response({"error": "unauthorized"}, status=401)


# MUHIM: xuddi mijozning Mini App sahifasidagi kabi (webapp_api.py'dagi
# izohga qarang) - Telegram WebView admin panel HTML/JS faylini ham
# keshlab qo'yishi mumkin, shuning uchun kodni yangilab qayta deploy
# qilingandan keyin ham admin ESKI ko'rinishni ko'rishda davom etishi
# mumkin edi. Shu sabab bu sahifa ham har doim "keshlanmasin" deb ANIQ
# belgilanadi.
_NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
}


async def admin_page(request: web.Request):
    return web.FileResponse(request.app["admin_index_path"], headers=_NO_CACHE_HEADERS)


async def api_admin_orders(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    open_only = request.query.get("open") == "1"
    orders = await db.get_all_orders(limit=100, open_only=open_only)
    return web.json_response({"orders": orders})


# Admin panelning bosqichli (Kanban) "Buyurtmalar" ko'rinishi uchun -
# har bir bo'lim (tab) shu lug'atdagi status ro'yxatiga mos keladi.
# MUHIM (27-avgust, 2-marta o'zgartirildi): "Arxiv" va "Muammo" endi
# ALOHIDA bo'lim ("final" kaliti endi ishlatilmaydi - order_service.py'dagi
# izohga qarang).
_ORDER_STAGES = {
    "new": order_service.STAGE_NEW_STATUSES,
    "accepted": order_service.STAGE_ACCEPTED_STATUSES,
    "shipped": order_service.STAGE_SHIPPED_STATUSES,
    "archived": order_service.STAGE_ARCHIVED_STATUSES,
    "problem": order_service.STAGE_PROBLEM_STATUSES,
}


async def api_admin_orders_by_stage(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    stage = request.match_info["stage"]
    statuses = _ORDER_STAGES.get(stage)
    if statuses is None:
        return web.json_response({"error": "bad_request"}, status=400)
    orders = await db.get_orders_by_statuses(statuses, limit=100)
    return web.json_response({"orders": orders})


async def api_admin_order_accept(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        order_id = int(request.match_info["order_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    order, reason = await admin_service.accept_order(order_id)
    if order is None:
        return web.json_response({"error": reason}, status=404)
    await admin_service.notify_customer_order_accepted(request.app["bot"], order)
    return web.json_response({"ok": True})


async def api_admin_order_ship(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        order_id = int(request.match_info["order_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    order, reason = await admin_service.ship_order(order_id)
    if order is None:
        return web.json_response({"error": reason}, status=404)
    await admin_service.notify_customer_order_shipped(request.app["bot"], order)
    return web.json_response({"ok": True})


async def api_admin_order_archive(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        order_id = int(request.match_info["order_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    order, reason = await admin_service.archive_order(order_id)
    if order is None:
        return web.json_response({"error": reason}, status=404)
    await admin_service.notify_customer_order_archived(request.app["bot"], order)
    return web.json_response({"ok": True})


async def api_admin_order_problem(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        order_id = int(request.match_info["order_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)

    # Sabab (izoh) ixtiyoriy - admin panelning "⚠️ Muammo" formasi orqali
    # yuboriladi. Body bo'sh/JSON emas bo'lsa ham xato bermaymiz (sababsiz
    # belgilash sifatida qaraymiz).
    reason = None
    try:
        body = await request.json()
        raw = (body.get("reason") or "").strip()
        reason = raw or None
    except Exception:
        pass

    order, err = await admin_service.flag_order_problem(order_id, reason)
    if order is None:
        return web.json_response({"error": err}, status=404)
    await admin_service.notify_customer_order_problem(request.app["bot"], order)
    return web.json_response({"ok": True})


async def api_admin_stats(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    stats = await admin_service.get_dashboard_stats()
    return web.json_response(stats)


async def api_admin_custom_orders(request: web.Request):
    """MUHIM (27-avgust, 2-marta o'zgartirildi): mijoz bilan "✅ Bog'landim"
    deb belgilangan shaxsiy buyurtmalar ENDI yo'qolib qolmaydi - ular
    arxivga o'tadi va shu yerdan ?archived=1 bilan ko'rish mumkin (admin
    panelning "🎨 Shaxsiy" bo'limidagi ikkinchi tab)."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    if request.query.get("archived") == "1":
        orders = await db.get_archived_custom_orders(limit=100)
    else:
        orders = await db.get_open_custom_orders(limit=100)
    return web.json_response({"orders": orders})


async def api_admin_custom_order_contacted(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        custom_order_id = int(request.match_info["order_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    order, reason = await admin_service.mark_custom_order_contacted(custom_order_id)
    if order is None:
        return web.json_response({"error": reason}, status=404)
    return web.json_response({"ok": True})


async def api_admin_topups(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    topups = await db.get_pending_topup_requests(limit=100)
    return web.json_response({"topups": topups})


async def api_admin_topup_approve(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        request_id = int(request.match_info["request_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    req, new_balance, reason = await admin_service.approve_topup(request_id)
    if req is None:
        status = 409 if reason == "already_processed" else 404
        return web.json_response({"error": reason}, status=status)
    await admin_service.notify_customer_topup_approved(request.app["bot"], req, new_balance)
    return web.json_response({"ok": True})


async def api_admin_topup_reject(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        request_id = int(request.match_info["request_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    req, reason = await admin_service.reject_topup(request_id)
    if req is None:
        status = 409 if reason == "already_processed" else 404
        return web.json_response({"error": reason}, status=status)
    await admin_service.notify_customer_topup_rejected(request.app["bot"], req)
    return web.json_response({"ok": True})


async def api_admin_products(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    products = await db.list_active_products()
    # Har biriga rasm(lar)ini ham qo'shamiz (webapp'dagi kabi photo proksi orqali ko'rsatish uchun)
    result = []
    for p in products:
        product = await db.get_product_by_id(p["id"])
        result.append(product or {**p, "photos": []})
    return web.json_response({"products": result})


def _decode_photo(data_url: str) -> bytes:
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    return base64.b64decode(data_url)


async def api_admin_product_create(request: web.Request):
    admin_id = _authed_admin_id(request)
    if admin_id is None:
        return _unauthorized()

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    category = (body.get("category") or "").strip()
    subcategory = (body.get("subcategory") or "").strip() or None
    name = (body.get("name") or "").strip()
    description = (body.get("description") or "").strip()
    photos = body.get("photos") or []

    try:
        price = int(body.get("price"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_input"}, status=400)

    if not category or not name or price <= 0:
        return web.json_response({"error": "invalid_input"}, status=400)
    if not isinstance(photos, list) or not photos:
        return web.json_response({"error": "photo_required"}, status=400)
    if len(photos) > 8:
        return web.json_response({"error": "too_many_photos"}, status=400)

    bot = request.app["bot"]
    file_ids = []
    for i, photo_data_url in enumerate(photos):
        try:
            raw = _decode_photo(photo_data_url)
            if len(raw) > 10 * 1024 * 1024:
                return web.json_response({"error": "photo_too_large"}, status=400)
            input_file = BufferedInputFile(raw, filename=f"product_{i}.jpg")
            msg = await bot.send_photo(
                admin_id, photo=input_file,
                caption="🗂 Admin panel orqali qo'shilayotgan mahsulot rasmi" if i == 0 else None,
            )
            file_ids.append(msg.photo[-1].file_id)
        except Exception:
            return web.json_response({"error": "photo_upload_failed"}, status=502)

    product_id = await db.create_product(category, name, description, price, subcategory=subcategory)
    for position, file_id in enumerate(file_ids):
        await db.add_product_photo(product_id, file_id, position)

    return web.json_response({"ok": True, "product_id": product_id})


async def api_admin_product_delete(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        product_id = int(request.match_info["product_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    await db.deactivate_product(product_id)
    return web.json_response({"ok": True})


# ---------- Yangiliklar/e'lonlar (28-avgust) ----------

_UZ_MONTHS = [
    "", "yanvar", "fevral", "mart", "aprel", "may", "iyun",
    "iyul", "avgust", "sentyabr", "oktyabr", "noyabr", "dekabr",
]


def _format_uz_datetime(iso_str: str) -> str:
    """"2026-08-28T15:40:00+00:00" kabi ISO vaqtni "28-avgust, 15:40"
    ko'rinishiga o'tkazadi - "📰 Yangiliklar" xabarnomasida qachon
    joylanganini ko'rsatish uchun."""
    try:
        dt = datetime.fromisoformat(iso_str)
    except ValueError:
        return iso_str
    month_name = _UZ_MONTHS[dt.month] if 1 <= dt.month <= 12 else str(dt.month)
    return f"{dt.day}-{month_name}, {dt.hour:02d}:{dt.minute:02d}"


async def api_admin_announcements(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    announcements = await db.get_announcements(limit=100)
    return web.json_response({"announcements": announcements})


async def api_admin_announcement_create(request: web.Request):
    admin_id = _authed_admin_id(request)
    if admin_id is None:
        return _unauthorized()

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    text = (body.get("text") or "").strip()
    photo_data_url = body.get("photo")
    if not text:
        return web.json_response({"error": "invalid_input"}, status=400)

    bot = request.app["bot"]
    photo_file_id = None
    if photo_data_url:
        try:
            raw = _decode_photo(photo_data_url)
            if len(raw) > 10 * 1024 * 1024:
                return web.json_response({"error": "photo_too_large"}, status=400)
            input_file = BufferedInputFile(raw, filename="announcement.jpg")
            msg = await bot.send_photo(
                admin_id, photo=input_file,
                caption="📰 Admin panel orqali qo'shilayotgan yangilik rasmi",
            )
            photo_file_id = msg.photo[-1].file_id
        except Exception:
            return web.json_response({"error": "photo_upload_failed"}, status=502)

    announcement_id = await db.create_announcement(text, photo_file_id=photo_file_id)

    # 28-avgust (foydalanuvchi so'rovi): e'lon joylashtirilgan zahoti BARCHA
    # botni ko'rgan odamlarga xabarnoma yuboriladi - qachon qo'yilganini
    # ham bilib turishsin. `announcements` jadvalida biz endigina yozgan
    # yozuvni qayta o'qib (created_at aniq vaqtni olish uchun), keyin
    # broadcast qilamiz - bitta odamga yetkazib bo'lmasligi (bloklagan/hali
    # /start bosmagan) boshqalarga to'sqinlik qilmaydi.
    items = await db.get_announcements(limit=1)
    created_at = items[0]["created_at"] if items else None
    time_line = f"\n\n🕓 {_format_uz_datetime(created_at)}" if created_at else ""
    broadcast_text = f"📰 <b>Yangilik!</b>\n\n{text}{time_line}"
    user_ids = await db.get_all_user_ids()
    if photo_file_id:
        await notify_all_customers(bot, user_ids, photo=photo_file_id, caption=broadcast_text)
    else:
        await notify_all_customers(bot, user_ids, text=broadcast_text)

    return web.json_response({"ok": True, "announcement_id": announcement_id})


async def api_admin_announcement_delete(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        announcement_id = int(request.match_info["announcement_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    await db.delete_announcement(announcement_id)
    return web.json_response({"ok": True})


def register_admin_routes(app: web.Application, admin_index_path: str):
    app["admin_index_path"] = admin_index_path
    app.router.add_get("/admin-panel", admin_page)
    app.router.add_get("/admin/api/orders", api_admin_orders)
    app.router.add_get("/admin/api/orders/stage/{stage}", api_admin_orders_by_stage)
    app.router.add_post("/admin/api/orders/{order_id}/accept", api_admin_order_accept)
    app.router.add_post("/admin/api/orders/{order_id}/ship", api_admin_order_ship)
    app.router.add_post("/admin/api/orders/{order_id}/archive", api_admin_order_archive)
    app.router.add_post("/admin/api/orders/{order_id}/problem", api_admin_order_problem)
    app.router.add_get("/admin/api/custom_orders", api_admin_custom_orders)
    app.router.add_post("/admin/api/custom_orders/{order_id}/contacted", api_admin_custom_order_contacted)
    app.router.add_get("/admin/api/topups", api_admin_topups)
    app.router.add_post("/admin/api/topups/{request_id}/approve", api_admin_topup_approve)
    app.router.add_post("/admin/api/topups/{request_id}/reject", api_admin_topup_reject)
    app.router.add_get("/admin/api/products", api_admin_products)
    app.router.add_post("/admin/api/products", api_admin_product_create)
    app.router.add_post("/admin/api/products/{product_id}/delete", api_admin_product_delete)
    app.router.add_get("/admin/api/stats", api_admin_stats)
    app.router.add_get("/admin/api/announcements", api_admin_announcements)
    app.router.add_post("/admin/api/announcements", api_admin_announcement_create)
    app.router.add_post("/admin/api/announcements/{announcement_id}/delete", api_admin_announcement_delete)
