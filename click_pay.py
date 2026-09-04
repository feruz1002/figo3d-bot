"""Click.uz "Merchant API" (Prepare/Complete) bilan ishlash - hamyonni
AVTOMATIK to'ldirish uchun (4-sentabr, foydalanuvchi so'rovi bilan qo'shildi).

Bu modul FAQAT imzo (sign) hisoblash va to'lov havolasini yasash bilan
shug'ullanadi - ma'lumotlar bazasi bilan ishlamaydi (bu webapp_api.py'da,
shu yerdagi funksiyalarni chaqirib bajariladi). Shunday qilingani sababi:
imzo formulasi juda nozik (bitta harf xato bo'lsa ham Click "SIGN CHECK
FAILED" deb rad etadi) - shuning uchun uni alohida, sodda va sinash oson
joyda saqlash xavfsizroq.

MUHIM: bu yerdagi barcha hisob-kitob Click'ning RASMIY namunaviy kutubxonasi
(https://github.com/click-llc/click-integration-php) asosida, aniq
tekshirilgan formula bo'yicha yozilgan - o'zboshimchalik bilan
o'zgartirilmasin, aks holda haqiqiy to'lovlar ishlamay qolishi mumkin.
"""
import hashlib

import config

# Click javobida ishlatiladigan xato kodlari (Click'ning rasmiy
# hujjatlariga mos, o'zgartirib bo'lmaydi):
ERR_SUCCESS = 0
ERR_SIGN_FAILED = -1
ERR_AMOUNT = -2
ERR_ACTION_NOT_FOUND = -3
ERR_ALREADY_PAID = -4
ERR_USER_NOT_FOUND = -5
ERR_TRANSACTION_NOT_FOUND = -6
ERR_BAD_REQUEST = -8
ERR_CANCELLED = -9

ERROR_NOTES = {
    ERR_SUCCESS: "Success",
    ERR_SIGN_FAILED: "SIGN CHECK FAILED!",
    ERR_AMOUNT: "Incorrect parameter amount",
    ERR_ACTION_NOT_FOUND: "Action not found",
    ERR_ALREADY_PAID: "Already paid",
    ERR_USER_NOT_FOUND: "User does not exist",
    ERR_TRANSACTION_NOT_FOUND: "Transaction does not exist",
    ERR_BAD_REQUEST: "Error in request from click",
    ERR_CANCELLED: "Transaction cancelled",
}

# Amount solishtirishda ruxsat etilgan xatolik (Click namunaviy
# kutubxonasidagi bilan bir xil chegaraga moslashtirilgan).
AMOUNT_TOLERANCE = 0.01


def is_configured() -> bool:
    """4 ta Click qiymati (Render Environment Variables'da) to'liq
    kiritilganmi? Yo'q bo'lsa, Click orqali to'lov mijozlarga umuman
    ko'rsatilmaydi (webapp_api.py'dagi api_config shu yerdan bilib oladi)."""
    return bool(
        config.CLICK_SERVICE_ID
        and config.CLICK_MERCHANT_ID
        and config.CLICK_SECRET_KEY
        and config.CLICK_MERCHANT_USER_ID
    )


def build_pay_url(merchant_trans_id, amount, return_url: str | None = None) -> str:
    """Mijoz Click orqali to'lashi uchun havola (my.click.uz saytiga yoki
    Click Up ilovasiga olib boradi). `merchant_trans_id` - bizning
    tarafdagi tranzaksiya ID (click_transactions.id, matn sifatida)."""
    url = (
        "https://my.click.uz/services/pay"
        f"?service_id={config.CLICK_SERVICE_ID}"
        f"&merchant_id={config.CLICK_MERCHANT_ID}"
        f"&amount={amount}"
        f"&transaction_param={merchant_trans_id}"
    )
    if return_url:
        url += f"&return_url={return_url}"
    return url


def _compute_sign(
    click_trans_id,
    merchant_trans_id,
    amount,
    action,
    sign_time,
    merchant_prepare_id=None,
) -> str:
    """Click'ning rasmiy formulasi (Prepare/Complete uchun bir xil, faqat
    Complete'da merchant_prepare_id qo'shiladi):

    md5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id +
        [merchant_prepare_id agar action==1 bo'lsa] + amount + action + sign_time)
    """
    parts = [
        str(click_trans_id),
        str(config.CLICK_SERVICE_ID),
        str(config.CLICK_SECRET_KEY),
        str(merchant_trans_id),
    ]
    if merchant_prepare_id is not None:
        parts.append(str(merchant_prepare_id))
    parts.append(str(amount))
    parts.append(str(action))
    parts.append(str(sign_time))
    raw = "".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def verify_sign(data: dict, action: int) -> bool:
    """Click'dan kelgan so'rovdagi `sign_string`ni o'zimiz hisoblab
    solishtiramiz - mos kelmasa, bu so'rov Click'dan emas (yoki
    buzilgan/qalbaki) degani, hech qanday amal bajarilmaydi."""
    merchant_prepare_id = data.get("merchant_prepare_id") if action == 1 else None
    expected = _compute_sign(
        click_trans_id=data.get("click_trans_id"),
        merchant_trans_id=data.get("merchant_trans_id"),
        amount=data.get("amount"),
        action=action,
        sign_time=data.get("sign_time"),
        merchant_prepare_id=merchant_prepare_id,
    )
    got = str(data.get("sign_string") or "")
    return bool(got) and expected == got


def amounts_match(expected_amount, received_amount) -> bool:
    try:
        return abs(float(expected_amount) - float(received_amount)) <= AMOUNT_TOLERANCE
    except (TypeError, ValueError):
        return False
