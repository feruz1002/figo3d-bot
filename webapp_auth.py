"""Telegram Mini App'dan (veb-do'kon) kelgan so'rovlarni tekshirish.

Mini App browserda ochiladi va API'ga so'rov yuborganda o'zi bilan Telegram
imzolagan "initData" degan matnni yuboradi. Buni bot tokeni yordamida
tekshirib, ICHIDAGI foydalanuvchi ID'siga ishonish mumkinligini aniqlaymiz.

DIQQAT: bu tekshiruv SHART - aks holda istalgan odam so'rovda boshqa
foydalanuvchining ID raqamini yuborib, uning savati yoki hamyon balansiga
aralashishi mumkin bo'lardi. Tafsilotlar: Telegram Mini Apps hujjati,
"Validating data received via the Mini App" bo'limi."""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400):
    """initData to'g'ri va yangi bo'lsa, undagi ma'lumotlarni (jumladan
    ishonchli "user" obyektini) dict sifatida qaytaradi. Aks holda None."""
    if not init_data or not bot_token:
        return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    except Exception:
        return None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    auth_date = pairs.get("auth_date")
    if auth_date:
        try:
            if time.time() - int(auth_date) > max_age_seconds:
                return None
        except ValueError:
            return None

    result = dict(pairs)
    if "user" in result:
        try:
            result["user"] = json.loads(result["user"])
        except Exception:
            result["user"] = None
    return result
