"""Mini App (veb-do'kon) uchun JSON API va rasm/video proksi.

Rasm/video proksi nima uchun kerak: mahsulot rasmlari bazada Telegram
"file_id" (uzun kod) sifatida saqlanadi - bu faqat bot tokeni orqali
yuklab olinadi, oddiy <img src="..."> bilan to'g'ridan-to'g'ri ko'rsatib
bo'lmaydi. Shuning uchun bu yerda serverning o'zi (tokenini oshkor
qilmasdan) rasmni Telegramdan yuklab, brauzerga uzatib beradi."""
from aiohttp import web

import db
import order_service
from config import BOT_TOKEN, PAYMENT_PROVIDER_TOKEN
from webapp_auth import validate_init_data


def _authed_user_id(request: web.Request):
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    data = validate_init_data(init_data, BOT_TOKEN)
    if not data or not data.get("user"):
        return None
    return data["user"].get("id")


async def api_catalog(request: web.Request):
    categories = await db.get_categories()
    products = []
    for cat in categories:
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
        }
        for item in cart
    ]
    total = sum(i["price"] * i["quantity"] for i in items)
    return web.json_response({"items": items, "total": total})


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
        product = await db.get_product_by_id(product_id)
        if not product:
            return web.json_response({"error": "not_found"}, status=404)

    new_qty = await db.set_cart_item_quantity(user_id, product_id, quantity)
    return web.json_response({"quantity": new_qty})


async def api_config(request: web.Request):
    """Mini App yuklanganda: qaysi to'lov usullari yoqilganini bilishi uchun."""
    return web.json_response({"card_enabled": bool(PAYMENT_PROVIDER_TOKEN)})


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
    subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart)
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

    cart = await db.get_cart(user_id)
    if not cart:
        return web.json_response({"error": "empty_cart"}, status=400)
    subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart)

    # Chegirmani hech qachon mijoz brauzeridan kelgan raqamga ishonib emas,
    # har doim serverning o'zi promo-kod asosida qayta hisoblab tasdiqlaydi.
    discount_amount = 0
    if promo_code:
        promo = await db.get_promo(promo_code)
        if promo and not (promo["max_uses"] is not None and promo["used_count"] >= promo["max_uses"]):
            discount_amount = subtotal * promo["discount_percent"] // 100
        else:
            promo_code = None  # yaroqsiz kod - jimgina e'tiborsiz qoldiramiz

    total = max(subtotal - discount_amount, 0)

    order_id, reason = await order_service.create_order_and_apply_payment(
        user_id, full_name, phone, address, promo_code, discount_amount, payment_method,
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
    return web.json_response({"order_id": order_id, "status": "confirmed", "total": total})


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


async def webapp_page(request: web.Request):
    return web.FileResponse(request.app["webapp_index_path"])


def register_webapp_routes(app: web.Application, webapp_index_path: str):
    app["webapp_index_path"] = webapp_index_path
    app.router.add_get("/webapp", webapp_page)
    app.router.add_get("/api/config", api_config)
    app.router.add_get("/api/catalog", api_catalog)
    app.router.add_get("/api/cart", api_cart)
    app.router.add_post("/api/cart/set_qty", api_cart_set_qty)
    app.router.add_get("/api/profile", api_profile)
    app.router.add_post("/api/promo/check", api_promo_check)
    app.router.add_post("/api/checkout", api_checkout)
    app.router.add_get("/api/photo/{file_id}", api_photo)
