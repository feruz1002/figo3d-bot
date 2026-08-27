"""Mini App (veb-do'kon) uchun JSON API va rasm/video proksi.

Rasm/video proksi nima uchun kerak: mahsulot rasmlari bazada Telegram
"file_id" (uzun kod) sifatida saqlanadi - bu faqat bot tokeni orqali
yuklab olinadi, oddiy <img src="..."> bilan to'g'ridan-to'g'ri ko'rsatib
bo'lmaydi. Shuning uchun bu yerda serverning o'zi (tokenini oshkor
qilmasdan) rasmni Telegramdan yuklab, brauzerga uzatib beradi."""
from aiohttp import web

import db
from config import BOT_TOKEN
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
    app.router.add_get("/api/catalog", api_catalog)
    app.router.add_get("/api/cart", api_cart)
    app.router.add_post("/api/cart/set_qty", api_cart_set_qty)
    app.router.add_get("/api/photo/{file_id}", api_photo)
