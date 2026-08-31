"""Mini App (veb-do'kon) uchun JSON API va rasm/video proksi.

Rasm/video proksi nima uchun kerak: mahsulot rasmlari bazada Telegram
"file_id" (uzun kod) sifatida saqlanadi - bu faqat bot tokeni orqali
yuklab olinadi, oddiy <img src="..."> bilan to'g'ridan-to'g'ri ko'rsatib
bo'lmaydi. Shuning uchun bu yerda serverning o'zi (tokenini oshkor
qilmasdan) rasmni Telegramdan yuklab, brauzerga uzatib beradi."""
import base64
import hashlib

from aiogram.types import BufferedInputFile
from aiohttp import web

import db
import delivery
import order_service
from admin_notify import notify_admins
from config import BOT_TOKEN, CONTACT_INFO, PAYMENT_INFO, PAYMENT_PROVIDER_TOKEN
from webapp_auth import validate_init_data


def _authed_user_id(request: web.Request):
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    data = validate_init_data(init_data, BOT_TOKEN)
    if not data or not data.get("user"):
        return None
    return data["user"].get("id")


def _authed_username(request: web.Request):
    """`_authed_user_id` bilan bir xil so'rovdan @username'ni ham olib
    beradi (bor bo'lsa) - admin panelning "Mijoz bilan bog'lanish" havolasi
    uchun (db.remember_username'ga qarang). Alohida qayta validatsiya
    qilmaslik uchun chaqiruvchi buni faqat allaqachon _authed_user_id
    muvaffaqiyatli bo'lgandan keyin ishlatishi kerak."""
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    data = validate_init_data(init_data, BOT_TOKEN)
    if not data or not data.get("user"):
        return None
    return data["user"].get("username")


async def _check_not_blocked(user_id: int):
    """29-avgust: admin panelidagi "👥 Mijozlar" bo'limida bloklangan
    mijozlar uchun - endi savat/buyurtma berish/hamyon to'ldirish/
    operatorga murojaat yuborish kabi "faol" amallar to'xtatiladi (katalog
    ko'rish va profilni ko'rish esa hamon ishlaydi - to'liq qulflab
    qo'yish shart emas). Qaytaradi: None (bloklanmagan) yoki xato javobi
    (web.Response) - chaqiruvchi shuni to'g'ridan-to'g'ri qaytarishi
    kerak."""
    profile = await db.get_user_profile(user_id)
    if profile and profile.get("blocked"):
        return web.json_response(
            {"error": "blocked", "message": "Sizning hisobingiz bloklangan. Savol bo'lsa, operator bilan bog'laning."},
            status=403,
        )
    return None


async def api_catalog(request: web.Request):
    """MUHIM (27-avgust, "katalog ichida katalog" so'roviga javoban):
    `categories` endi oddiy matn ro'yxati emas, balki har biri o'z ichidagi
    kichik bo'limlar ro'yxati bilan birga qaytadi - Mini App shu orqali
    2 darajali (Bo'lim -> Kichik bo'lim) navigatsiya quradi. `products`
    ro'yxatidagi har bir mahsulotda ham endi `subcategory` maydoni bor
    (bo'lmasa - null)."""
    category_names = await db.get_categories()
    categories = []
    products = []
    for cat in category_names:
        subcats = await db.get_subcategories(cat)
        categories.append({"name": cat, "subcategories": subcats})
        products.extend(await db.get_products_by_category(cat))
    return web.json_response({"categories": categories, "products": products})


async def api_cart(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    cart = await db.get_cart(user_id)
    items = [
        {
            "product_id": item["product"]["id"],
            "name": item["product"]["name"],
            "price": item["product"]["price"],
            "photo": item["product"]["photos"][0] if item["product"]["photos"] else None,
            "quantity": item["quantity"],
            # 30-avgust (foydalanuvchi so'rovi): mijoz shu mahsulot uchun
            # tanlagan filament rangi - null bo'lsa "Avtomatik" (do'kon o'zi
            # tanlaydi) degani.
            "color": item.get("color"),
            # 30-avgust (foydalanuvchi so'rovi): mijoz yozdirmoqchi bo'lgan
            # matn (faqat mahsulot buni ruxsat bergan bo'lsa mumkin) va shu
            # mahsulotning matn narxi/maksimal uzunligi - Mini App bularni
            # savat ekranida ko'rsatib, qo'shimcha to'lovni hisoblaydi.
            "custom_text": item.get("custom_text"),
            "allow_text_customization": item["product"].get("allow_text_customization", False),
            "max_text_length": item["product"].get("max_text_length"),
            "text_price": item["product"].get("text_price"),
            "line_total": db.cart_item_line_total(item),
        }
        for item in cart
    ]
    total = db.cart_subtotal(cart)
    return web.json_response({"items": items, "total": total})


async def api_colors(request: web.Request):
    """Mini App'da mijozga ko'rsatiladigan filament ranglari ro'yxati -
    faqat admin panelda FAOL qilib qo'yilganlari (30-avgust, foydalanuvchi
    so'rovi: "mijoz rangini belgilashi yoki avto belgilanishga qoysin")."""
    colors = await db.get_active_filament_colors()
    return web.json_response({"colors": colors})


async def api_delivery_options(request: web.Request):
    """Mini App'ning to'lov (checkout) ekranida yetkazib berish bo'limini
    chizish uchun kerak bo'lgan HAMMA narsa: pochta xizmatlari ro'yxati
    (nomi/emoji/uyga yetkazadimi), hududlar ro'yxati (har biri qaysi masofa
    bosqichiga tegishli) va JORIY narxlar jadvali (31-avgust, foydalanuvchi
    so'rovi: "mijoz mahsulot narxi ichida yetkazib berishi deb
    o'ylamasligi kerak"). Narx frontendda faqat KO'RSATISH uchun -
    haqiqiy hisoblash har doim serverda (/api/checkout ichida) qayta
    tekshiriladi."""
    prices = await db.get_delivery_prices()
    price_map = {}
    for p in prices:
        price_map.setdefault(p["courier"], {}).setdefault(p["delivery_type"], {})[str(p["distance_tier"])] = p["price"]
    return web.json_response({
        "couriers": delivery.COURIERS,
        "regions": delivery.REGIONS,
        "distance_tiers": delivery.DISTANCE_TIERS,
        "districts": delivery.DISTRICTS_BY_REGION,
        "prices": price_map,
    })


async def _resolve_delivery_selection(body: dict):
    """Mijoz yuborgan pochta/turi/hudud/tuman tanlovini SERVER TOMONDA
    tasdiqlaydi va haqiqiy narxni admin narx jadvalidan hisoblaydi - mijoz
    brauzeridan kelgan narxga HECH QACHON ishonmaymiz (xuddi promo-kod/
    rang/matn narxi kabi). To'rttasi ham (courier/type/region/district)
    MAJBURIY - yetkazib berish tanlanmagan bo'lsa buyurtma qabul
    qilinmaydi (31-avgust, foydalanuvchi so'rovi: mijoz yetkazib berishni
    albatta tanlashi kerak). MUHIM: tuman narxga TA'SIR QILMAYDI (narx
    hamon faqat hudud bosqichiga qarab hisoblanadi) - faqat aniqroq manzil
    ma'lumoti sifatida saqlanadi (2-kunlik tuzatish, foydalanuvchi so'rovi:
    "viloyatni tanlagandan so'ng pastdan tuman ham chiqishi kerak").

    Qaytaradi: (courier_code, delivery_type, region_code, district, price, xato|None).
    Xato bo'lsa, qolgan qiymatlarga e'tibor bermang - chaqiruvchi xatoni
    to'g'ridan-to'g'ri qaytarishi kerak."""
    courier_code = body.get("delivery_courier")
    delivery_type = body.get("delivery_type")
    region_code = body.get("delivery_region")
    district = (body.get("delivery_district") or "").strip() or None

    courier = delivery.get_courier(courier_code)
    region = delivery.get_region(region_code)
    if not courier or not region or not delivery.is_valid_delivery_type(courier_code, delivery_type):
        return None, None, None, None, 0, web.json_response({"error": "invalid_delivery"}, status=400)
    if not district or not delivery.is_valid_district(region_code, district):
        return None, None, None, None, 0, web.json_response({"error": "invalid_district"}, status=400)

    price = await db.get_delivery_price(courier_code, delivery_type, region["tier"])
    if price is None:
        # Nazariy jihatdan bo'lmasligi kerak (init_db barcha to'g'ri
        # kombinatsiyalarni 0 so'm bilan oldindan to'ldiradi), lekin baza
        # eski/qo'lda o'zgartirilgan bo'lsa ham xavfsiz tomonda qolish uchun.
        price = 0
    return courier_code, delivery_type, region_code, district, price, None


async def api_cart_set_color(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        body = await request.json()
        product_id = int(body.get("product_id"))
    except (TypeError, ValueError, KeyError):
        return web.json_response({"error": "bad_request"}, status=400)

    color = body.get("color")
    color = (color or "").strip() or None
    # Bo'sh/None ("Avtomatik") har doim ruxsat etiladi. Aniq rang tanlansa -
    # hozir FAOL bo'lgan ranglar ro'yxatida borligi tekshiriladi (mijoz
    # brauzeridan kelgan qiymatga ko'r-ko'rona ishonmaslik uchun).
    if color is not None:
        active_colors = await db.get_active_filament_colors()
        if color not in [c["name"] for c in active_colors]:
            return web.json_response({"error": "invalid_color"}, status=400)

    ok = await db.set_cart_item_color(user_id, product_id, color)
    if not ok:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True, "color": color})


async def api_cart_set_text(request: web.Request):
    """30-avgust (foydalanuvchi so'rovi): "matn yozdirish" - HAMMA
    mahsulotda emas, faqat admin panelda `allow_text_customization`
    yoqilgan mahsulotlarda mumkin, va matn `max_text_length`dan uzun
    bo'lmasligi kerak - ikkalasi ham mijoz brauzeridan kelgan qiymatga
    ko'r-ko'rona ishonmasdan, serverning o'zida qayta tekshiriladi."""
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        body = await request.json()
        product_id = int(body.get("product_id"))
    except (TypeError, ValueError, KeyError):
        return web.json_response({"error": "bad_request"}, status=400)

    text = body.get("text")
    text = (text or "").strip() or None

    if text is not None:
        product = await db.get_product_by_id(product_id)
        if not product:
            return web.json_response({"error": "not_found"}, status=404)
        if not product.get("allow_text_customization"):
            return web.json_response({"error": "text_not_allowed"}, status=400)
        max_len = product.get("max_text_length")
        if max_len and len(text) > max_len:
            return web.json_response({"error": "text_too_long", "max_length": max_len}, status=400)

    ok = await db.set_cart_item_text(user_id, product_id, text)
    if not ok:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True, "text": text})


async def api_cart_set_qty(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        body = await request.json()
        product_id = int(body.get("product_id"))
        quantity = max(0, int(body.get("quantity", 0)))
    except (TypeError, ValueError, KeyError):
        return web.json_response({"error": "bad_request"}, status=400)

    if quantity > 0:
        blocked_resp = await _check_not_blocked(user_id)
        if blocked_resp is not None:
            return blocked_resp
        product = await db.get_product_by_id(product_id)
        if not product:
            return web.json_response({"error": "not_found"}, status=404)

    new_qty = await db.set_cart_item_quantity(user_id, product_id, quantity)
    return web.json_response({"quantity": new_qty})


async def api_config(request: web.Request):
    """Mini App yuklanganda: qaysi to'lov usullari yoqilganini, "Aloqa" matni
    va hisob to'ldirish rekvizitlarini bilishi uchun."""
    return web.json_response({
        "card_enabled": bool(PAYMENT_PROVIDER_TOKEN),
        "contact_info": CONTACT_INFO,
        "payment_info": PAYMENT_INFO,
    })


async def api_profile(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    profile = await db.get_user_profile(user_id)
    return web.json_response({
        "full_name": profile["full_name"] if profile else None,
        "phone": profile["phone"] if profile else None,
        "address": profile["address"] if profile else None,
        "balance": profile["balance"] if profile else 0,
    })


def _decode_photo(data_url: str) -> bytes:
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    return base64.b64decode(data_url)


async def _upload_photo_get_file_id(bot, filename: str, photo_data_url: str):
    """Brauzerdan kelgan base64 rasmni Telegram'ga yuklab, keyinchalik
    saqlash/qayta yuborish uchun ishlatiladigan "file_id"ni qaytaradi.
    Buning uchun rasm birinchi adminning shaxsiy chatiga yuboriladi (bu
    ADMIN_IDS bo'sh bo'lmasligini talab qiladi)."""
    from config import ADMIN_IDS

    if not ADMIN_IDS:
        raise RuntimeError("ADMIN_IDS sozlanmagan - rasm yuklab bo'lmadi")
    raw = _decode_photo(photo_data_url)
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("photo_too_large")
    input_file = BufferedInputFile(raw, filename=filename)
    msg = await bot.send_photo(ADMIN_IDS[0], photo=input_file)
    return msg.photo[-1].file_id


async def api_profile_update(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    full_name = _valid_str(body.get("full_name"), 2)
    phone = _valid_str(body.get("phone"), 7)
    address = _valid_str(body.get("address"), 3)
    if not full_name or not phone or not address:
        return web.json_response({"error": "invalid_input"}, status=400)

    await db.upsert_user_profile(user_id, full_name=full_name, phone=phone, address=address)
    await db.remember_username(user_id, _authed_username(request))
    return web.json_response({"ok": True})


async def api_orders(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    orders = await db.get_user_orders(user_id, limit=20)
    return web.json_response({"orders": orders})


async def api_custom_order(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    blocked_resp = await _check_not_blocked(user_id)
    if blocked_resp is not None:
        return blocked_resp

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    description = _valid_str(body.get("description"), 3)
    full_name = _valid_str(body.get("full_name"), 2)
    phone = _valid_str(body.get("phone"), 7)
    address = _valid_str(body.get("address"), 3)
    photo_data_url = body.get("photo")
    if not (description and full_name and phone and address and photo_data_url):
        return web.json_response({"error": "invalid_input"}, status=400)

    bot = request.app["bot"]
    try:
        photo_file_id = await _upload_photo_get_file_id(bot, "custom_order.jpg", photo_data_url)
    except ValueError:
        return web.json_response({"error": "photo_too_large"}, status=400)
    except Exception:
        return web.json_response({"error": "photo_upload_failed"}, status=502)

    custom_order_id = await db.create_custom_order(
        user_id=user_id, photo_file_id=photo_file_id, description=description,
        full_name=full_name, phone=phone, address=address,
    )
    await db.upsert_user_profile(user_id, full_name=full_name, phone=phone, address=address)
    await db.remember_username(user_id, _authed_username(request))

    caption = (
        f"🎨 Yangi SHAXSIY buyurtma so'rovi #{custom_order_id}\n\n"
        f"Tavsif: {description}\n\n"
        f"Ism: {full_name}\n"
        f"Tel: {phone}\n"
        f"Manzil: {address}\n\n"
        "Rasmni ko'rib, narxni kelishib, mijoz bilan bog'laning."
    )
    from keyboards import custom_admin_keyboard
    await notify_admins(
        bot, photo=photo_file_id, caption=caption,
        reply_markup=custom_admin_keyboard(custom_order_id, user_id),
    )

    return web.json_response({"ok": True, "custom_order_id": custom_order_id})


async def api_topup(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    blocked_resp = await _check_not_blocked(user_id)
    if blocked_resp is not None:
        return blocked_resp

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    try:
        amount = int(body.get("amount"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_input"}, status=400)
    if amount <= 0:
        return web.json_response({"error": "invalid_input"}, status=400)

    # MUHIM (28-avgust, foydalanuvchi so'rovi): skrinshot ENDI MAJBURIY -
    # avval ixtiyoriy edi ("skrinshotsiz yuborish" tugmasi bor edi), lekin
    # to'lovni tasdiqlashni osonlashtirish uchun endi har doim talab
    # qilinadi (chatdagi eski "skrinshotsiz" yo'li ham olib tashlandi -
    # handlers/profile.py'ga qarang).
    photo_data_url = body.get("screenshot")
    if not photo_data_url:
        return web.json_response({"error": "screenshot_required"}, status=400)

    bot = request.app["bot"]
    try:
        screenshot_file_id = await _upload_photo_get_file_id(bot, "topup_proof.jpg", photo_data_url)
    except ValueError:
        return web.json_response({"error": "photo_too_large"}, status=400)
    except Exception:
        return web.json_response({"error": "photo_upload_failed"}, status=502)

    request_id = await db.create_topup_request(user_id, amount, screenshot_file_id)

    from handlers.catalog import format_price
    from keyboards import topup_admin_keyboard
    caption = (
        f"💰 Yangi hisob to'ldirish so'rovi #{request_id}\n\n"
        f"Foydalanuvchi ID: {user_id}\n"
        f"Summasi: {format_price(amount)} so'm"
    )
    if screenshot_file_id:
        await notify_admins(bot, photo=screenshot_file_id, caption=caption, reply_markup=topup_admin_keyboard(request_id))
    else:
        await notify_admins(bot, text=caption + "\n\n(Skrinshot yuborilmagan)", reply_markup=topup_admin_keyboard(request_id))

    return web.json_response({"ok": True, "request_id": request_id})


# ---------- VAZIFALAR ("🎯 Vazifalar" - tanga/mukofot tizimi, 29-avgust) ----------
# Admin (yoki kelajakda boshqa biznes egalari admin orqali) Instagram/
# YouTube'da like/obuna/komentariya kabi vazifalar joylashtiradi, mijoz
# bajarib skrinshot yuboradi, admin tasdiqlagach mukofot to'g'ridan-to'g'ri
# hamyonga (so'm sifatida) qo'shiladi - xuddi hisob to'ldirish (topup) bilan
# bir xil oqim.

async def api_tasks(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    tasks = await db.get_active_tasks()
    submissions_map = await db.get_user_task_submissions_map(user_id)
    for t in tasks:
        # "kutilmoqda" / "tasdiqlandi" / "rad etildi" yoki None (hali
        # umuman yubormagan) - Mini App shu bo'yicha tugma/nishon ko'rsatadi.
        t["my_status"] = submissions_map.get(t["id"])
    return web.json_response({"tasks": tasks})


async def api_task_submit(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    blocked_resp = await _check_not_blocked(user_id)
    if blocked_resp is not None:
        return blocked_resp

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    try:
        task_id = int(body.get("task_id"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_input"}, status=400)

    task = await db.get_task(task_id)
    if not task or task["status"] != "faol":
        return web.json_response({"error": "task_not_found"}, status=404)

    if await db.has_open_task_submission(task_id, user_id):
        return web.json_response({"error": "already_submitted"}, status=409)

    photo_data_url = body.get("screenshot")
    if not photo_data_url:
        return web.json_response({"error": "screenshot_required"}, status=400)

    bot = request.app["bot"]
    try:
        raw = _decode_photo(photo_data_url)
        if len(raw) > 10 * 1024 * 1024:
            return web.json_response({"error": "photo_too_large"}, status=400)
        # MUHIM: rasm mazmunidan hisoblangan "barmoq izi" (sha256) saqlanadi -
        # kimdir bir marta olingan skrinshotni qayta-qayta (yoki turli
        # vazifalar/akkauntlar bilan) yuborsa, admin panelida avtomatik
        # ogohlantirish sifatida ko'rinadi (bu firibgarlikni to'liq oldini
        # olmaydi, lekin sezilarli qiyinlashtiradi).
        image_hash = hashlib.sha256(raw).hexdigest()
        screenshot_file_id = await _upload_photo_get_file_id(bot, "task_proof.jpg", photo_data_url)
    except ValueError:
        return web.json_response({"error": "photo_too_large"}, status=400)
    except Exception:
        return web.json_response({"error": "photo_upload_failed"}, status=502)

    submission_id = await db.create_task_submission(task_id, user_id, screenshot_file_id, image_hash)
    await db.remember_username(user_id, _authed_username(request))

    # MUHIM (29-avgust, foydalanuvchi so'rovi): AVVAL bu yerda topup/shaxsiy
    # buyurtma kabi HAR bir yuborilgan skrinshot uchun ALOHIDA chat xabari
    # yuborilardi - lekin vazifalar minglab bo'lishi mumkinligi sababli bu
    # ADMIN CHATINI TO'LDIRIB TASHLASHI mumkin edi. Shuning uchun endi
    # bunday xabar UMUMAN yuborilmaydi - ko'rib chiqish FAQAT admin
    # panelning "🎯 Vazifalar -> 🆕 Tekshirish" navbati orqali bo'ladi (u
    # yerda sidebar'da "🎯 Vazifalar (N)" ko'rinishida nechta so'rov
    # kutayotgani ko'rinadi - api_admin_task_submissions_pending_count'ga
    # qarang).
    #
    # DIQQAT (texnik cheklov): Telegram'dan skrinshot uchun "file_id" olish
    # (yuqoridagi _upload_photo_get_file_id) baribir uni ADMIN_IDS[0]'ning
    # shaxsiy chatiga BITTA oddiy (izohsiz) rasm sifatida yuboradi - bu
    # Telegram Bot API'ning o'zi shunday ishlashi sababli (file_id olish
    # uchun rasmni biron joyga yuborish SHART) va topup/shaxsiy buyurtma/
    # mahsulot rasmlarida ham bor - hozircha o'zgartirilmagan.

    # MUHIM (29-avgust, foydalanuvchi so'rovi): "🤖 AI tekshiruvi" - admin
    # panelda YOQILGAN bo'lsagina (va ANTHROPIC_API_KEY sozlangan bo'lsagina)
    # ishga tushadi. AI skrinshotni baholaydi; agar u "ishonchli" VA "yuqori"
    # ishonch darajasida deb topsa, HAMDA bu rasm boshqa hech qayerda
    # ishlatilmagan bo'lsa (image_hash dublikat emas) - so'rov ADMINSIZ,
    # DARHOL avtomatik tasdiqlanadi va mukofot hamyonga tushadi. Boshqa
    # barcha holatlarda (shubhali/mos_emas/dublikat/AI o'chirilgan/AI
    # xatolik bergan) - so'rov odatdagidek "🆕 Tekshirish" navbatida qoladi,
    # lekin endi AI'ning bahosi ham ko'rinadi (bor bo'lsa) - bu admin
    # qarorini sezilarli tezlashtiradi. Hech qachon AI o'zi rad ETMAYDI -
    # noaniq/salbiy baho doim odamga qoldiriladi (pul yo'qotish xavfi
    # yo'q, faqat noto'g'ri rad etish xavfi bo'lishi mumkin edi).
    ai_enabled = (await db.get_setting("ai_task_review_enabled", "0")) == "1"
    auto_approved = False
    if ai_enabled:
        from ai_verify import _extract_mime, verify_task_screenshot
        ai_result = await verify_task_screenshot(raw, _extract_mime(photo_data_url), task)
        if ai_result:
            await db.set_task_submission_ai_result(
                submission_id, ai_result["verdict"], ai_result.get("confidence"), ai_result.get("reasoning"),
            )
            if ai_result["verdict"] == "ishonchli" and ai_result.get("confidence") == "yuqori":
                duplicate = await db.find_duplicate_submission_by_hash(image_hash, submission_id)
                if not duplicate:
                    import admin_service
                    sub, task_obj, new_balance, reason = await admin_service.approve_task_submission(
                        submission_id, approved_by="ai",
                    )
                    if sub:
                        await admin_service.notify_customer_task_approved(bot, sub, task_obj, new_balance)
                        auto_approved = True

    # 29-avgust (foydalanuvchi so'rovi): AI avtomatik tasdiqlamagan
    # so'rovlar uchun chatga xabar yuborish - endi ENDI DEFAULT bo'yicha
    # O'CHIRILGAN (yuqoridagi izohga qarang: minglab vazifa chatni to'ldirib
    # yuborishi mumkin edi) - lekin admin panelning "⚙️ Sozlamalar" bo'limida
    # "🎯 Vazifa bajarilgani haqida chatga xabar kelsin" switch'ini YOQSA,
    # bu yerda odatdagidek (topup/shaxsiy buyurtma kabi) alohida chat xabari
    # keladi. Ko'rib chiqish har doim, xabar yoqilgan-yoqilmaganidan qat'i
    # nazar, "🎯 Vazifalar -> 🆕 Tekshirish" navbatida (badge bilan) mavjud.
    if not auto_approved:
        chat_notify = (await db.get_setting("task_submission_chat_notify", "0")) == "1"
        if chat_notify:
            username = _authed_username(request)
            caption = (
                f"🎯 Yangi vazifa bajarilgani haqida xabar #{submission_id}\n\n"
                f"Vazifa: {task.get('title')}\n"
                f"Platforma: {task.get('platform')}\n"
                f"Mukofot: {task.get('reward_amount')} so'm\n\n"
                "Skrinshotni ko'rib, tasdiqlang yoki rad eting."
            )
            from keyboards import task_submission_admin_keyboard
            await notify_admins(
                bot, photo=screenshot_file_id, caption=caption,
                reply_markup=task_submission_admin_keyboard(submission_id),
            )

    return web.json_response({"ok": True, "submission_id": submission_id})


async def api_promo_check(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        body = await request.json()
    except Exception:
        body = {}
    code = (body.get("code") or "").strip().upper()
    if not code:
        return web.json_response({"valid": False, "reason": "empty"})

    promo = await db.get_promo(code)
    if not promo:
        return web.json_response({"valid": False, "reason": "not_found"})
    if promo["max_uses"] is not None and promo["used_count"] >= promo["max_uses"]:
        return web.json_response({"valid": False, "reason": "limit_reached"})

    cart = await db.get_cart(user_id)
    subtotal = db.cart_subtotal(cart)
    discount_amount = subtotal * promo["discount_percent"] // 100
    return web.json_response({
        "valid": True,
        "code": code,
        "discount_percent": promo["discount_percent"],
        "discount_amount": discount_amount,
    })


def _valid_str(value, min_len: int) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value if len(value) >= min_len else None


async def api_checkout(request: web.Request):
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    blocked_resp = await _check_not_blocked(user_id)
    if blocked_resp is not None:
        return blocked_resp

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    full_name = _valid_str(body.get("full_name"), 2)
    phone = _valid_str(body.get("phone"), 7)
    address = _valid_str(body.get("address"), 3)
    payment_method = body.get("payment_method")
    promo_code = (body.get("promo_code") or "").strip().upper() or None

    if not full_name or not phone or not address:
        return web.json_response({"error": "invalid_input"}, status=400)
    if payment_method not in ("balance", "cash", "card"):
        return web.json_response({"error": "invalid_payment_method"}, status=400)
    if payment_method == "card" and not PAYMENT_PROVIDER_TOKEN:
        return web.json_response({"error": "card_unavailable"}, status=400)

    # 31-avgust (foydalanuvchi so'rovi): yetkazib berish MAJBURIY - mijoz
    # mahsulot narxi ichida yetkazib berish ham bor deb o'ylamasligi kerak,
    # shuning uchun pochta xizmati/turi/hudud aniq tanlanmasa buyurtma
    # qabul qilinmaydi. Narx HECH QACHON mijoz yuborgan raqamga ishonib
    # emas, har doim shu yerda (serverda) admin narx jadvalidan qayta
    # hisoblanadi.
    delivery_courier, delivery_type, delivery_region, delivery_district, delivery_price, delivery_err = (
        await _resolve_delivery_selection(body)
    )
    if delivery_err is not None:
        return delivery_err

    await db.remember_username(user_id, _authed_username(request))

    cart = await db.get_cart(user_id)
    if not cart:
        return web.json_response({"error": "empty_cart"}, status=400)
    subtotal = db.cart_subtotal(cart)

    # Chegirmani hech qachon mijoz brauzeridan kelgan raqamga ishonib emas,
    # har doim serverning o'zi promo-kod asosida qayta hisoblab tasdiqlaydi.
    discount_amount = 0
    if promo_code:
        promo = await db.get_promo(promo_code)
        if promo and not (promo["max_uses"] is not None and promo["used_count"] >= promo["max_uses"]):
            discount_amount = subtotal * promo["discount_percent"] // 100
        else:
            promo_code = None  # yaroqsiz kod - jimgina e'tiborsiz qoldiramiz

    # MUHIM (31-avgust): db.order_total orqali hisoblanadi (chegirma FAQAT
    # mahsulotlarga, yetkazib berish narxi ustiga ALOHIDA qo'shiladi) -
    # order_service.create_order_and_apply_payment ICHIDA HAM aynan shu
    # funksiya ishlatiladi, ikkalasi bir xil natija berishi SHART.
    total = db.order_total(subtotal, discount_amount, delivery_price)

    order_id, reason = await order_service.create_order_and_apply_payment(
        user_id, full_name, phone, address, promo_code, discount_amount, payment_method,
        delivery_courier=delivery_courier, delivery_type=delivery_type,
        delivery_region=delivery_region, delivery_price=delivery_price,
        delivery_district=delivery_district,
    )
    if order_id is None:
        status = 409 if reason == "insufficient_balance" else 400
        return web.json_response({"error": reason}, status=status)

    if payment_method == "card":
        try:
            link = await order_service.create_card_invoice_link(request.app["bot"], order_id, len(cart), total)
        except Exception:
            return web.json_response(
                {"error": "invoice_failed", "order_id": order_id}, status=502
            )
        return web.json_response({"order_id": order_id, "status": "awaiting_payment", "invoice_link": link, "total": total})

    await order_service.notify_admin_new_order(request.app["bot"], order_id, payment_method)
    await order_service.notify_customer_order_placed(request.app["bot"], order_id)
    return web.json_response({"order_id": order_id, "status": "confirmed", "total": total})


async def api_request_checkout(request: web.Request):
    """Mini App'ning savat oynasidagi "✅ Buyurtmani yakunlash" tugmasi
    uchun. MUHIM: bu yerda buyurtma BEVOSITA yaratilmaydi va to'lov
    so'ralmaydi - bu ataylab shunday, chunki buyurtma yaratish/to'lov
    mantig'i endi FAQAT ishonchli CHAT oqimida (handlers/checkout.py)
    qoladi (qarang: 27-avgust brifingi - Mini App'ning JS/webview orqali
    to'g'ridan-to'g'ri buyurtma berishi muammoli chiqqan edi). Bu funksiya
    faqat "signal beradi": mijozning CHATIGA savat xulosasini va "✅
    Buyurtma berish" tugmasini (xuddi chatda "🛒 Savat" bosilgandagidek)
    yuboradi - shundan keyin Mini App yopiladi va mijoz to'g'ridan-to'g'ri
    tayyor xabar bilan chatda qoladi, qo'lda "🛒 Savat" tugmasini qidirib
    o'tirishi shart emas."""
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    cart = await db.get_cart(user_id)
    if not cart:
        return web.json_response({"error": "empty_cart"}, status=400)

    from handlers.catalog import format_price
    from keyboards import cart_keyboard

    subtotal = db.cart_subtotal(cart)
    lines = ["🛒 <b>Savatingiz:</b>\n"]
    for item in cart:
        lines.append(f"• {item['product']['name']} x{item['quantity']}")
    lines.append(f"\n<b>Jami: {format_price(subtotal)} so'm</b>")
    lines.append("\nBuyurtmani yakunlash uchun pastdagi tugmani bosing:")

    bot = request.app["bot"]
    try:
        await bot.send_message(user_id, "\n".join(lines), reply_markup=cart_keyboard(cart))
    except Exception:
        # Mijoz botni bloklagan yoki hali /start bosmagan bo'lishi mumkin -
        # bu holatda ham Mini App'dagi savat o'zgarishsiz qoladi, frontend
        # buni ko'rib, chatdagi "🛒 Savat" tugmasidan foydalanishni so'raydi.
        return web.json_response({"error": "send_failed"}, status=502)
    return web.json_response({"ok": True})


async def api_contact_message(request: web.Request):
    """29-avgust (foydalanuvchi so'rovi): mijoz "chat" tugmasini bosganda
    adminga murojaat yubora OLMAYOTGAN edi - sababi, pastki chat tugmalari
    olib tashlangandan keyin (28-avgust) mijoz botning oddiy chatida
    yozadigan bo'lsa ham buni HECH KIM o'qib turmasdi (botda "erkin matn"ni
    ushlab, adminga yo'naltiradigan handler UMUMAN YO'Q edi - eski "☎️
    Aloqa" tugmasi ham faqat STATIK matn ko'rsatardi, mijozdan xabar
    OLMASDI). Shuning uchun Mini App ichida haqiqiy "operatorga yozish"
    formasi qo'shildi - shu endpoint orqali xabar to'g'ridan-to'g'ri
    adminlarga yetkaziladi (ular "💬 Mijoz bilan bog'lanish" tugmasi bilan
    darhol javob yoza olishadi).

    29-avgust: endi xabar BAZAGA HAM saqlanadi (avval faqat chatga
    yuborilib, hech qayerda saqlanmasdi) va admin panelning "💬
    Murojaatlar" bo'limida ishi bitmaguncha ("ochiq" holatda) ko'rinib
    turadi - foydalanuvchi so'rovi: "ariza haqidagi ma'lumot admin panelda
    ham ko'rinishi kerak, ishi bitmaguncha"."""
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    blocked_resp = await _check_not_blocked(user_id)
    if blocked_resp is not None:
        return blocked_resp

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad_request"}, status=400)

    text = _valid_str(body.get("message"), 3)
    if not text:
        return web.json_response({"error": "invalid_input"}, status=400)

    await db.remember_username(user_id, _authed_username(request))
    message_id = await db.create_contact_message(user_id, text)

    bot = request.app["bot"]
    from keyboards import contact_message_admin_keyboard

    profile = await db.get_user_profile(user_id)
    name_line = f" ({profile['full_name']})" if profile and profile["full_name"] else ""
    caption = (
        f"💬 Mijozdan yangi murojaat #{message_id}{name_line}\n\n"
        f"Foydalanuvchi ID: {user_id}\n\n"
        f"{text}"
    )
    await notify_admins(bot, text=caption, reply_markup=contact_message_admin_keyboard(message_id, user_id))

    return web.json_response({"ok": True, "message_id": message_id})


async def api_announcements(request: web.Request):
    """Mini App'ning "📰 Yangiliklar" bo'limi uchun - admin panel orqali
    qo'shilgan e'lon/aksiyalar ro'yxati, eng yangisidan boshlab."""
    user_id = _authed_user_id(request)
    if user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    announcements = await db.get_announcements(limit=50)
    return web.json_response({"announcements": announcements})


async def api_photo(request: web.Request):
    file_id = request.match_info["file_id"]
    bot = request.app["bot"]
    try:
        buf = await bot.download(file_id)
    except Exception:
        return web.Response(status=404)
    return web.Response(
        body=buf.read(),
        content_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=2592000"},
    )


# MUHIM: Mini App sahifasini (HTML+JS) Telegram'ning ichki WebView'i (va
# ba'zan mobil brauzerlar) juda "yopishqoq" kesh (cache) qiladi - kodni
# yangilab, GitHub'ga yuklab, Render qayta deploy qilgandan keyin ham
# foydalanuvchi ESKI versiyani ko'rishda davom etishi mumkin, chunki
# qurilma hali eski HTML/JS faylni o'z keshidan ko'rsatib turadi. Buni
# oldini olish uchun bu sahifani HAR DOIM "keshlanmasin" deb ANIQ
# belgilaymiz - shunda brauzer/WebView har safar serverdan yangi nusxani
# so'raydi (o'zgarish darhol ko'rinadi, foydalanuvchi ilovani qo'lda
# tozalashi shart bo'lmaydi).
_NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
}


async def webapp_page(request: web.Request):
    return web.FileResponse(request.app["webapp_index_path"], headers=_NO_CACHE_HEADERS)


def register_webapp_routes(app: web.Application, webapp_index_path: str):
    app["webapp_index_path"] = webapp_index_path
    app.router.add_get("/webapp", webapp_page)
    app.router.add_get("/api/config", api_config)
    app.router.add_get("/api/catalog", api_catalog)
    app.router.add_get("/api/cart", api_cart)
    app.router.add_post("/api/cart/set_qty", api_cart_set_qty)
    app.router.add_post("/api/cart/set_color", api_cart_set_color)
    app.router.add_post("/api/cart/set_text", api_cart_set_text)
    app.router.add_get("/api/colors", api_colors)
    app.router.add_get("/api/delivery/options", api_delivery_options)
    app.router.add_get("/api/profile", api_profile)
    app.router.add_post("/api/profile", api_profile_update)
    app.router.add_get("/api/orders", api_orders)
    app.router.add_post("/api/custom_order", api_custom_order)
    app.router.add_post("/api/topup", api_topup)
    app.router.add_get("/api/tasks", api_tasks)
    app.router.add_post("/api/task_submit", api_task_submit)
    app.router.add_post("/api/promo/check", api_promo_check)
    app.router.add_post("/api/checkout", api_checkout)
    app.router.add_post("/api/request_checkout", api_request_checkout)
    app.router.add_get("/api/announcements", api_announcements)
    app.router.add_post("/api/contact_message", api_contact_message)
    app.router.add_get("/api/photo/{file_id}", api_photo)
