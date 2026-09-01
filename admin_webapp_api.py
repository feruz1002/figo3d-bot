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
import delivery
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
    """29-avgust: endi ixtiyoriy `amount` (JSON tanasida) qabul qiladi -
    berilsa, mijoz SO'RAGAN summa o'rniga shu (admin qo'lda kiritgan)
    summa hamyonga qo'shiladi. Bu skrinshotda/tranzaksiyada ko'rsatilgan
    summa so'ralgandan farq qilganda (kam/ko'p tushgan yoki tranzaksiyada
    xatolik bo'lganda) ishlatiladi - webapp/admin.html'dagi "💰 To'ldirish"
    bo'limida har bir so'rov yonida summani TAHRIRLASH mumkin."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        request_id = int(request.match_info["request_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)

    amount = None
    try:
        body = await request.json()
    except Exception:
        body = {}
    if body and body.get("amount") is not None:
        try:
            amount = int(body["amount"])
        except (TypeError, ValueError):
            return web.json_response({"error": "invalid_amount"}, status=400)

    req, new_balance, reason = await admin_service.approve_topup(request_id, amount=amount)
    if req is None:
        status = 409 if reason == "already_processed" else (400 if reason == "invalid_amount" else 404)
        return web.json_response({"error": reason}, status=status)
    await admin_service.notify_customer_topup_approved(request.app["bot"], req, new_balance)
    return web.json_response({"ok": True, "approved_amount": req["approved_amount"]})


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


async def api_admin_balance_adjust(request: web.Request):
    """29-avgust: mijozning hamyoniga HECH QANDAY hisob to'ldirish
    so'roviga bog'liq bo'lmagan holda to'g'ridan-to'g'ri pul qo'shish/
    ayirish - masalan tranzaksiyada xatolik bo'lib, lekin mijoz botga
    so'rov yubormagan (yoki so'rovi yo'qolgan/xato ketgan) holatlar uchun.
    Faqat botni kamida bir marta ko'rgan (users jadvalida yozuvi bor)
    foydalanuvchi ID'lari uchun ishlaydi."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    try:
        user_id = int(body.get("user_id"))
        delta = int(body.get("delta"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_input"}, status=400)
    if delta == 0:
        return web.json_response({"error": "invalid_input"}, status=400)
    note = (body.get("note") or "").strip() or None

    new_balance, reason = await admin_service.manual_balance_adjust(user_id, delta, note)
    if new_balance is None:
        return web.json_response({"error": reason}, status=404)

    await admin_service.notify_customer_balance_adjusted(request.app["bot"], user_id, delta, new_balance, note)
    return web.json_response({"ok": True, "new_balance": new_balance})


# ---------- VAZIFALAR ("🎯 Vazifalar" - tanga/mukofot tizimi, 29-avgust) ----------
# Admin bu yerdan Instagram/YouTube kabi tarmoqlarda like/obuna/komentariya
# kabi vazifalar yaratadi (rasm shart emas - faqat matn/havola/mukofot).
# Mijoz Mini App'da bajarib skrinshot yuboradi (webapp_api.api_task_submit),
# u shu yerdagi "🆕 Tekshirish" navbatiga tushadi - screenshot orqali
# haqiqiyligini 100% avtomatik tekshirib bo'lmaydi (Instagram/YouTube bu
# ma'lumotni tashqi dasturga bermaydi), shuning uchun HAR DOIM admin ko'rib
# tasdiqlaydi/rad etadi (find_duplicate_submission_by_hash orqali bir xil
# rasm ikkinchi marta ishlatilgani sezilsa - javobda ogohlantirish beriladi).

async def api_admin_tasks(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    tasks = await db.get_all_tasks_admin(limit=200)
    return web.json_response({"tasks": tasks})


async def api_admin_task_create(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    platform = (body.get("platform") or "").strip()
    task_type = (body.get("task_type") or "").strip()
    title = (body.get("title") or "").strip()
    description = (body.get("description") or "").strip() or None
    target_url = (body.get("target_url") or "").strip()
    try:
        reward_amount = int(body.get("reward_amount"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_input"}, status=400)

    if not platform or not task_type or not title or not target_url or reward_amount <= 0:
        return web.json_response({"error": "invalid_input"}, status=400)

    task_id = await db.create_task(platform, task_type, title, description, target_url, reward_amount)
    return web.json_response({"ok": True, "task_id": task_id})


async def api_admin_task_toggle(request: web.Request):
    """Vazifani "faol" <-> "tugagan" holatiga o'tkazadi (o'chirilmaydi -
    eski topshirilgan skrinshotlar tarixi/mukofotlar bilan bog'liqligi
    saqlanib qolishi uchun)."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        task_id = int(request.match_info["task_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    task = await db.get_task(task_id)
    if not task:
        return web.json_response({"error": "not_found"}, status=404)
    new_status = "tugagan" if task["status"] == "faol" else "faol"
    await db.set_task_status(task_id, new_status)
    return web.json_response({"ok": True, "status": new_status})


_KNOWN_SETTINGS = {
    # 29-avgust (foydalanuvchi so'rovi): oldin faqat AI tekshiruvi uchun
    # bo'lgan alohida on/off endpoint umumiy "Sozlamalar" tizimiga
    # aylantirildi - kelajakda yana shunga o'xshash switch'lar shu yerga
    # qo'shiladi (admin panelning "⚙️ Sozlamalar" bo'limiga qarang).
    "ai_task_review_enabled": {
        "label": "🤖 AI tekshiruvi (vazifa skrinshotlarini avtomatik baholaydi)",
    },
    "task_submission_chat_notify": {
        "label": "🎯 Vazifa bajarilgani haqida chatga xabar kelsin",
    },
}


async def api_admin_settings_list(request: web.Request):
    """29-avgust: admin panel "⚙️ Sozlamalar" bo'limi uchun barcha
    switch/toggle sozlamalarning joriy holatini qaytaradi. `api_key_configured`
    - Render'da ANTHROPIC_API_KEY sozlanmagan bo'lsa, admin AI tekshiruvini
    "yoqilgan" qilib qo'ysa ham u jimgina qo'lda rejimga tushib qolishini
    oldindan tushuntirish uchun (ai_verify.py/webapp_api.api_task_submit'ga
    qarang)."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    # MUHIM (30-avgust, "Sozlamalar yuklanmayapti" xatosi tuzatildi): AVVAL
    # bu yerda "from config import ANTHROPIC_API_KEY" ishlatilgan edi - agar
    # admin AI (Claude) tekshiruvi qo'shilgan versiyani hali joylashtirmagan
    # bo'lsa (masalan hozircha eski config.py'da qolgan bo'lsa), config.py'da
    # bu nom umuman YO'Q bo'lib, ImportError bilan butun so'rov 500 xatosi
    # bilan qulab tushardi - shuning uchun "⚙️ Sozlamalar" bo'limi HECH QACHON
    # yuklanmasdi. Endi getattr bilan - nom yo'q bo'lsa ham xato bermaydi,
    # shunchaki "sozlanmagan" deb hisoblanadi.
    import config
    api_key_configured = bool(getattr(config, "ANTHROPIC_API_KEY", None))
    result = []
    for key, meta in _KNOWN_SETTINGS.items():
        value = await db.get_setting(key, "0")
        result.append({"key": key, "label": meta["label"], "enabled": value == "1"})
    return web.json_response({"settings": result, "ai_api_key_configured": api_key_configured})


async def api_admin_settings_update(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)
    key = body.get("key")
    if key not in _KNOWN_SETTINGS:
        return web.json_response({"error": "unknown_setting"}, status=400)
    enabled = bool(body.get("enabled"))
    await db.set_setting(key, "1" if enabled else "0")
    return web.json_response({"ok": True, "key": key, "enabled": enabled})


async def api_admin_ai_approved_task_submissions(request: web.Request):
    """29-avgust: AI o'zi (adminsiz) avtomatik tasdiqlagan so'nggi
    so'rovlar ro'yxati - tasodifiy tekshirib (audit) turish uchun. Bu
    yerda hech qanday amal (tasdiqlash/rad etish) yo'q - faqat ko'rish."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    submissions = await db.get_recent_ai_approved_submissions(limit=100)
    return web.json_response({"submissions": submissions})


async def api_admin_task_submissions_pending_count(request: web.Request):
    """29-avgust (foydalanuvchi so'rovi): admin chatida HAR BIR yuborilgan
    vazifa uchun alohida xabar kelishi minglab vazifa bo'lganda chatni
    to'ldirib tashlashi mumkin edi - shuning uchun endi yangi so'rov haqida
    ALOHIDA CHAT XABARI umuman yuborilmaydi (webapp_api.api_task_submit'ga
    qarang). Buning o'rniga admin panel sidebar'idagi "🎯 Vazifalar" yonida
    shu son (badge) ko'rinadi - admin panelni ochib turgan holda darhol
    nechta yangi so'rov borligini ko'radi."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    count = await db.count_pending_task_submissions()
    return web.json_response({"count": count})


async def api_admin_task_submissions(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    submissions = await db.get_pending_task_submissions(limit=200)
    # Har biriga - agar rasmi boshqa yozuvda ham uchragan bo'lsa - ogohlantirish belgisini qo'shamiz.
    for s in submissions:
        duplicate = await db.find_duplicate_submission_by_hash(s.get("image_hash"), s["id"])
        s["duplicate_of"] = duplicate
    return web.json_response({"submissions": submissions})


async def api_admin_task_submission_approve(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        submission_id = int(request.match_info["submission_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    submission, task, new_balance, reason = await admin_service.approve_task_submission(submission_id)
    if submission is None:
        status = 409 if reason == "already_processed" else 404
        return web.json_response({"error": reason}, status=status)
    await admin_service.notify_customer_task_approved(request.app["bot"], submission, task, new_balance)
    return web.json_response({"ok": True})


async def api_admin_task_submission_reject(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        submission_id = int(request.match_info["submission_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    submission, task, reason = await admin_service.reject_task_submission(submission_id)
    if submission is None:
        status = 409 if reason == "already_processed" else 404
        return web.json_response({"error": reason}, status=status)
    await admin_service.notify_customer_task_rejected(request.app["bot"], submission, task)
    return web.json_response({"ok": True})


# ---------- Mijoz murojaatlari / arizalar (29-avgust) ----------
# Mijoz Mini App'dagi "💬 Operatorga yozish" orqali yozgan xabarlar - ishi
# bitmaguncha ("ochiq") shu yerda ko'rinib turadi (webapp_api.api_contact_message
# xabarni yaratadi, admin uni shu yerdan yoki chatdagi "✅ Bajarildi"
# tugmasi orqali yopadi - handlers/admin.py'ga qarang).

async def api_admin_contact_messages(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    status = "yopilgan" if request.query.get("resolved") == "1" else "ochiq"
    messages = await db.get_contact_messages(status=status, limit=100)
    return web.json_response({"messages": messages})


async def api_admin_contact_message_resolve(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        message_id = int(request.match_info["message_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    ok = await db.resolve_contact_message(message_id)
    if not ok:
        return web.json_response({"error": "not_found_or_already_resolved"}, status=404)
    return web.json_response({"ok": True})


# ---------- Mijozlar (admin panel "👥 Mijozlar" bo'limi, 29-avgust) ----------
# Qidiruv (ID/ism/telefon/username bo'yicha), to'liq ma'lumot (profil +
# buyurtmalar + hisob to'ldirish tarixi), profilni tahrirlash va
# bloklash/blokdan chiqarish.

async def api_admin_customers_search(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    query = request.query.get("q", "")
    users = await db.search_users(query, limit=30)
    return web.json_response({"users": users})


async def api_admin_customer_detail(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        user_id = int(request.match_info["user_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    profile = await db.get_user_profile(user_id)
    if not profile:
        return web.json_response({"error": "not_found"}, status=404)
    orders = await db.get_user_orders(user_id, limit=20)
    topups = await db.get_user_topup_history(user_id, limit=20)
    return web.json_response({"profile": profile, "orders": orders, "topups": topups})


async def api_admin_customer_profile_update(request: web.Request):
    """Admin panelidan mijozning ism/telefon/manzilini TO'G'RIDAN-TO'G'RI
    tahrirlash uchun (masalan mijoz noto'g'ri kiritgan yoki operator
    telefon orqali kelishib, yangilashi kerak bo'lganda)."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        user_id = int(request.match_info["user_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    profile = await db.get_user_profile(user_id)
    if not profile:
        return web.json_response({"error": "not_found"}, status=404)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    full_name = (body.get("full_name") or "").strip() or None
    phone = (body.get("phone") or "").strip() or None
    address = (body.get("address") or "").strip() or None
    await db.upsert_user_profile(user_id, full_name=full_name, phone=phone, address=address)
    return web.json_response({"ok": True})


async def api_admin_customer_block(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        user_id = int(request.match_info["user_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    profile = await db.get_user_profile(user_id)
    if not profile:
        return web.json_response({"error": "not_found"}, status=404)

    try:
        body = await request.json()
        blocked = bool(body.get("blocked"))
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    await db.set_user_blocked(user_id, blocked)
    try:
        text = (
            "🚫 Hisobingiz vaqtincha bloklandi. Savol bo'lsa, operator bilan bog'laning."
            if blocked else
            "✅ Hisobingiz blokdan chiqarildi — botdan qaytadan to'liq foydalanishingiz mumkin."
        )
        await request.app["bot"].send_message(user_id, text)
    except Exception:
        pass
    return web.json_response({"ok": True, "blocked": blocked})


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


def _parse_text_customization_fields(body: dict):
    """30-avgust (foydalanuvchi so'rovi): "matn yozdirish" xizmati - HAMMA
    mahsulotda emas, admin har birida alohida yoqadi. Yoqilgan bo'lsa,
    MAJBURIY ravishda ikkalasini ham kiritishi kerak: maksimal necha belgi
    yozish mumkinligi va yozilsa qancha qo'shimcha to'lanadi. Qaytaradi:
    (allow, max_len, text_price, error_response|None) - xato bo'lsa
    birinchi uchtasi mazmunsiz, chaqiruvchi to'g'ridan-to'g'ri
    error_response'ni qaytarishi kerak."""
    allow = bool(body.get("allow_text_customization"))
    if not allow:
        return False, None, None, None
    try:
        max_len = int(body.get("max_text_length"))
        text_price = int(body.get("text_price"))
    except (TypeError, ValueError):
        return None, None, None, web.json_response(
            {"error": "invalid_text_customization"}, status=400
        )
    if max_len <= 0 or text_price < 0:
        return None, None, None, web.json_response(
            {"error": "invalid_text_customization"}, status=400
        )
    return True, max_len, text_price, None


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
    # 29-avgust (foydalanuvchi so'rovi): mahsulotga 3D model (STL) fayli
    # havolasi - ixtiyoriy. Admin buyurtmani yig'ayotganda shu havoladan
    # to'g'ridan-to'g'ri STL faylni yuklab olishi uchun (buyurtma
    # kartochkasidagi "🧊 STL" tugmasiga qarang).
    stl_url = (body.get("stl_url") or "").strip() or None

    allow_text, max_text_length, text_price, text_err = _parse_text_customization_fields(body)
    if text_err is not None:
        return text_err

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

    product_id = await db.create_product(
        category, name, description, price, subcategory=subcategory, stl_url=stl_url,
        allow_text_customization=allow_text, max_text_length=max_text_length, text_price=text_price,
    )
    for position, file_id in enumerate(file_ids):
        await db.add_product_photo(product_id, file_id, position)

    return web.json_response({"ok": True, "product_id": product_id})


async def api_admin_product_update(request: web.Request):
    """30-avgust (foydalanuvchi so'rovi): mahsulot QO'SHILGANDAN SO'NG
    tahrirlash - avval faqat o'chirish mumkin edi. DIQQAT: rasmlar bu
    yerda o'zgartirilmaydi (alohida imkoniyat emas) - faqat matn/narx/
    STL havolasi/matn yozdirish sozlamalari."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        product_id = int(request.match_info["product_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    category = (body.get("category") or "").strip()
    subcategory = (body.get("subcategory") or "").strip() or None
    name = (body.get("name") or "").strip()
    description = (body.get("description") or "").strip()
    stl_url = (body.get("stl_url") or "").strip() or None

    allow_text, max_text_length, text_price, text_err = _parse_text_customization_fields(body)
    if text_err is not None:
        return text_err

    try:
        price = int(body.get("price"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_input"}, status=400)
    if not category or not name or price <= 0:
        return web.json_response({"error": "invalid_input"}, status=400)

    ok = await db.update_product(
        product_id, category, name, description, price,
        subcategory=subcategory, stl_url=stl_url,
        allow_text_customization=allow_text, max_text_length=max_text_length, text_price=text_price,
    )
    if not ok:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})


async def api_admin_product_delete(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        product_id = int(request.match_info["product_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    await db.deactivate_product(product_id)
    return web.json_response({"ok": True})


# ---------- Filament ranglari (30-avgust, foydalanuvchi so'rovi) ----------
# Mijoz buyurtma qilayotganda savatdagi har bir mahsulot uchun shu ro'yxatdan
# rang tanlaydi (yoki "Avtomatik" qoldiradi). Admin shu yerda mavjud ranglar
# ro'yxatini boshqaradi - o'chirilmaydi, faqat faol/nofaol qilinadi (rang
# vaqtincha omborda tugab qolsa, keyin qayta yoqish uchun).

async def api_admin_colors(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    colors = await db.get_all_filament_colors_admin()
    return web.json_response({"colors": colors})


async def api_admin_color_create(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)
    name = (body.get("name") or "").strip()
    if not name:
        return web.json_response({"error": "invalid_input"}, status=400)
    color_id = await db.create_filament_color(name)
    return web.json_response({"ok": True, "color_id": color_id})


async def api_admin_color_toggle(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        color_id = int(request.match_info["color_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    colors = await db.get_all_filament_colors_admin()
    color = next((c for c in colors if c["id"] == color_id), None)
    if not color:
        return web.json_response({"error": "not_found"}, status=404)
    new_active = not color["active"]
    await db.set_filament_color_active(color_id, new_active)
    return web.json_response({"ok": True, "active": new_active})


async def api_admin_color_rename(request: web.Request):
    """30-avgust (foydalanuvchi so'rovi): rang nomida xato bo'lsa, uni
    o'chirib qayta qo'shmasdan to'g'ridan-to'g'ri tahrirlash uchun."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        color_id = int(request.match_info["color_id"])
    except ValueError:
        return web.json_response({"error": "bad_request"}, status=400)
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)
    name = (body.get("name") or "").strip()
    if not name:
        return web.json_response({"error": "invalid_input"}, status=400)
    ok = await db.rename_filament_color(color_id, name)
    if not ok:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True, "name": name})


# ---------- Yetkazib berish narxlari (31-avgust, foydalanuvchi so'rovi) ----------
# Admin panelning "🚚 Yetkazib berish" bo'limi: 3 pochta (BTS/EMU/UzPost) x
# 3 masofa bosqichi x (Ofis/Uy, UzPost'da faqat Ofis) = 15 ta katakli
# jadval - admin narxlarni to'g'ridan-to'g'ri shu yerda tahrirlaydi.

async def api_admin_delivery_prices_list(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    prices = await db.get_delivery_prices()
    return web.json_response({
        "couriers": delivery.COURIERS,
        "distance_tiers": delivery.DISTANCE_TIERS,
        "prices": prices,
    })


async def api_admin_delivery_prices_update(request: web.Request):
    """Butun jadvalni BIR SO'ROVDA saqlaydi (har katak uchun alohida
    so'rov emas - admin "💾 Saqlash"ni bosganda hammasi birga yuboriladi).
    Body: {"prices": [{"courier": "bts", "delivery_type": "office",
    "distance_tier": 1, "price": 15000}, ...]}."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    items = body.get("prices")
    if not isinstance(items, list) or not items:
        return web.json_response({"error": "invalid_input"}, status=400)

    # Avval HAMMASINI tekshiramiz (bittasi noto'g'ri bo'lsa, hech narsani
    # yarim-yorti saqlamasdan butunlay rad etamiz - shunda admin panelda
    # "qisman saqlandi" degan chalkash holat bo'lmaydi).
    parsed = []
    for item in items:
        if not isinstance(item, dict):
            return web.json_response({"error": "invalid_input"}, status=400)
        courier = item.get("courier")
        dtype = item.get("delivery_type")
        try:
            tier = int(item.get("distance_tier"))
            price = int(item.get("price"))
        except (TypeError, ValueError):
            return web.json_response({"error": "invalid_input"}, status=400)
        if not delivery.is_valid_delivery_type(courier, dtype):
            return web.json_response({"error": "invalid_delivery_type", "courier": courier, "delivery_type": dtype}, status=400)
        if tier not in delivery.DISTANCE_TIERS:
            return web.json_response({"error": "invalid_distance_tier", "distance_tier": tier}, status=400)
        if price < 0:
            return web.json_response({"error": "negative_price"}, status=400)
        parsed.append((courier, dtype, tier, price))

    for courier, dtype, tier, price in parsed:
        await db.set_delivery_price(courier, dtype, tier, price)

    return web.json_response({"ok": True})


# ---------- Kategoriyalar (bo'limlar) - joyi/rangi/tavsifi (1-sentyabr) ----------
# Foydalanuvchi so'rovi: "mijozga ko'rinadigan kattaloglarni joyini
# rangini va qisqa desprition qo'shish imkoniyati bo'lishi kerak".
# Bo'lim NOMLARI hamon "🗂 Mahsulotlar" bo'limida mahsulot qo'shish/
# tahrirlashda erkin matn sifatida kiritiladi - bu yerda faqat MAVJUD
# bo'lim nomlarining TARTIBI/RANGI/TAVSIFI boshqariladi.

async def api_admin_categories_list(request: web.Request):
    if _authed_admin_id(request) is None:
        return _unauthorized()
    return web.json_response({"categories": await db.get_categories_meta()})


def _is_valid_hex_color(value) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip()
    if len(v) != 7 or not v.startswith("#"):
        return False
    hex_part = v[1:]
    return all(c in "0123456789abcdefABCDEF" for c in hex_part)


async def api_admin_categories_update(request: web.Request):
    """Butun ro'yxatni BIR SO'ROVDA saqlaydi (🚚 Yetkazib berish
    jadvalidagi "💾 Hammasini saqlash" bilan bir xil naqsh - har qator
    uchun alohida so'rov emas). Body: {"categories": [{"name": "...",
    "color": "#2ea6ff" yoki null, "description": "..." yoki null}, ...]}
    - RO'YXATDAGI TARTIB = mijozga ko'rinadigan yangi TARTIB (ekrandagi
    joyi)."""
    if _authed_admin_id(request) is None:
        return _unauthorized()
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    items = body.get("categories")
    if not isinstance(items, list) or not items:
        return web.json_response({"error": "invalid_input"}, status=400)

    # Avval HAMMASINI tekshiramiz - bittasi noto'g'ri bo'lsa hech narsani
    # yarim-yorti saqlamasdan butunlay rad etamiz.
    for item in items:
        if not isinstance(item, dict) or not (item.get("name") or "").strip():
            return web.json_response({"error": "invalid_input"}, status=400)
        color = item.get("color")
        if color and not _is_valid_hex_color(color):
            return web.json_response({"error": "invalid_color", "name": item.get("name")}, status=400)
        description = item.get("description")
        if description is not None and len(str(description)) > 300:
            return web.json_response({"error": "description_too_long", "name": item.get("name")}, status=400)

    await db.update_categories_order_and_meta(items)
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
    app.router.add_post("/admin/api/balance_adjust", api_admin_balance_adjust)
    app.router.add_get("/admin/api/tasks", api_admin_tasks)
    app.router.add_post("/admin/api/tasks", api_admin_task_create)
    app.router.add_post("/admin/api/tasks/{task_id}/toggle", api_admin_task_toggle)
    app.router.add_get("/admin/api/task_submissions/pending_count", api_admin_task_submissions_pending_count)
    app.router.add_get("/admin/api/settings", api_admin_settings_list)
    app.router.add_post("/admin/api/settings", api_admin_settings_update)
    app.router.add_get("/admin/api/task_submissions/ai_approved", api_admin_ai_approved_task_submissions)
    app.router.add_get("/admin/api/task_submissions", api_admin_task_submissions)
    app.router.add_post("/admin/api/task_submissions/{submission_id}/approve", api_admin_task_submission_approve)
    app.router.add_post("/admin/api/task_submissions/{submission_id}/reject", api_admin_task_submission_reject)
    app.router.add_get("/admin/api/contact_messages", api_admin_contact_messages)
    app.router.add_post("/admin/api/contact_messages/{message_id}/resolve", api_admin_contact_message_resolve)
    app.router.add_get("/admin/api/customers", api_admin_customers_search)
    app.router.add_get("/admin/api/customers/{user_id}", api_admin_customer_detail)
    app.router.add_post("/admin/api/customers/{user_id}/profile", api_admin_customer_profile_update)
    app.router.add_post("/admin/api/customers/{user_id}/block", api_admin_customer_block)
    app.router.add_get("/admin/api/products", api_admin_products)
    app.router.add_post("/admin/api/products", api_admin_product_create)
    app.router.add_post("/admin/api/products/{product_id}/delete", api_admin_product_delete)
    app.router.add_post("/admin/api/products/{product_id}/update", api_admin_product_update)
    app.router.add_get("/admin/api/colors", api_admin_colors)
    app.router.add_post("/admin/api/colors", api_admin_color_create)
    app.router.add_post("/admin/api/colors/{color_id}/toggle", api_admin_color_toggle)
    app.router.add_post("/admin/api/colors/{color_id}/rename", api_admin_color_rename)
    app.router.add_get("/admin/api/delivery_prices", api_admin_delivery_prices_list)
    app.router.add_post("/admin/api/delivery_prices", api_admin_delivery_prices_update)
    app.router.add_get("/admin/api/categories", api_admin_categories_list)
    app.router.add_post("/admin/api/categories", api_admin_categories_update)
    app.router.add_get("/admin/api/stats", api_admin_stats)
    app.router.add_get("/admin/api/announcements", api_admin_announcements)
    app.router.add_post("/admin/api/announcements", api_admin_announcement_create)
    app.router.add_post("/admin/api/announcements/{announcement_id}/delete", api_admin_announcement_delete)
