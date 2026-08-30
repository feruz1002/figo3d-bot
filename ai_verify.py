"""AI (Claude) yordamida "🎯 Vazifalar" skrinshotini OLDINDAN baholash.

MUHIM (haqiqatni buzmaslik uchun): bu YAKUNIY, 100% ishonchli tekshiruv
EMAS. Instagram/YouTube kabi platformalar "bu odam haqiqatan like
bosdimi/obuna bo'ldimi" degan ma'lumotni tashqi dasturga ochiq bermaydi -
shuning uchun AI ham faqat skrinshotning VIZUAL jihatdan ishonchli
ko'rinish-ko'rinmasligini baholaydi (masalan: rasm to'g'ri ilovaga/sahifaga
tegishlimi, tasvirlangan holat vazifaga mos keladimi). AI fotoshop qilingan
yoki keyinchalik bekor qilingan (masalan like bosib, keyin qaytarib
olingan) holatlarni ANIQLAY OLMAYDI - shu sababli faqat YUQORI ishonch
darajasidagi natijalar avtomatik tasdiqlash uchun ishlatiladi
(webapp_api.api_task_submit'ga qarang), qolgani baribir admin ko'rib
chiqishi uchun navbatga tushadi (endi AI'ning bahosi bilan birga - bu
tekshirishni sezilarli tezlashtiradi).

Ishlatish: ANTHROPIC_API_KEY sozlanmagan yoki admin panelda "🤖 AI
tekshiruvi" o'chirilgan bo'lsa, bu modul UMUMAN chaqirilmaydi (chaqiruvchi
o'zi tekshiradi) - bu yerda alohida yoqish/o'chirish mantig'i yo'q."""
import base64
import json
import logging

import config

# MUHIM (30-avgust): to'g'ridan-to'g'ri "from config import ANTHROPIC_API_KEY"
# EMAS, getattr orqali - agar config.py'da bu nomlar hali yo'q bo'lsa
# (masalan admin eski versiyada qolgan bo'lsa), oddiy "from import" ImportError
# bilan qulab tushib, bu modulni chaqiruvchi so'rovni (mijozning vazifa
# skrinshoti yuborishini) butunlay to'xtatib qo'yardi.
ANTHROPIC_API_KEY = getattr(config, "ANTHROPIC_API_KEY", None)
ANTHROPIC_MODEL = getattr(config, "ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

logger = logging.getLogger("figo3d_bot.ai_verify")

_TASK_TYPE_HUMAN = {
    "like": "layk bosish",
    "subscribe": "obuna bo'lish",
    "comment": "komentariya yozish",
    "repost": "ulashish/repost qilish",
    "boshqa": "vazifani bajarish",
}

_VALID_VERDICTS = {"ishonchli", "shubhali", "mos_emas"}
_VALID_CONFIDENCE = {"yuqori", "o'rta", "past"}


def _extract_mime(photo_data_url: str) -> str:
    """"data:image/png;base64,...." kabi satrdan MIME turini ("image/png")
    ajratib oladi - topilmasa xavfsiz standart ("image/jpeg") qaytadi."""
    try:
        if photo_data_url.startswith("data:") and ";base64," in photo_data_url:
            return photo_data_url.split(";base64,", 1)[0][5:] or "image/jpeg"
    except Exception:
        pass
    return "image/jpeg"


async def verify_task_screenshot(image_bytes: bytes, mime_type: str, task: dict) -> dict | None:
    """Qaytaradi:
      {"verdict": "ishonchli" | "shubhali" | "mos_emas",
       "confidence": "yuqori" | "o'rta" | "past",
       "reasoning": "qisqa o'zbekcha izoh"}
    yoki None - AI kaliti sozlanmagan, kutubxona o'rnatilmagan, yoki
    so'rovda biror xatolik bo'lsa (bunda chaqiruvchi oddiy qo'lda tekshirish
    navbatiga tushirishi kerak - hech qachon bu holatda avtomatik
    tasdiqlanmaydi)."""
    if not ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
    except ImportError:
        logger.warning("`anthropic` kutubxonasi o'rnatilmagan (requirements.txt'ni tekshiring) - AI tekshiruvi o'tkazib yuborildi")
        return None

    task_type_human = _TASK_TYPE_HUMAN.get(task.get("task_type"), task.get("task_type") or "")
    prompt = (
        f"Bir mobil ilova foydalanuvchisi \"{task.get('platform')}\" tarmog'idagi quyidagi "
        f"vazifani bajarganini tasdiqlash uchun skrinshot yubordi:\n"
        f"- Vazifa turi: {task_type_human}\n"
        f"- Sarlavha: {task.get('title')}\n"
        f"- Nishon havola: {task.get('target_url')}\n\n"
        "Skrinshotga qarab, ushbu aniq vazifa HAQIQATAN bajarilganga VIZUAL jihatdan "
        "o'xshaydimi (masalan: to'g'ri ilova/sahifa ko'rinib turibdimi, tasvirlangan "
        "belgi/holat - layk/obuna/komentariya - ko'rinib turibdimi)?\n\n"
        "MUHIM CHEKLOV: siz skrinshotning fotoshop qilinganini yoki harakat keyinchalik "
        "bekor qilinganini (masalan like bosib, keyin qaytarib olingan) ANIQLAY OLMAYSIZ - "
        "faqat rasmda VIZUAL ravishda ko'ringan holatni baholang, ortiqcha ishonch bildirmang. "
        "Agar rasm ushbu vazifaga umuman bog'liq bo'lmasa (boshqa ilova, bo'sh/tasodifiy "
        "rasm, matn o'qib bo'lmaydi va h.k.) - \"mos_emas\" deb belgilang.\n\n"
        "FAQAT quyidagi JSON formatida javob bering, boshqa hech qanday matn yozmang:\n"
        '{"verdict": "ishonchli yoki shubhali yoki mos_emas", '
        '"confidence": "yuqori yoki o\'rta yoki past", '
        '"reasoning": "1-2 gapli qisqa izoh, o\'zbek tilida"}'
    )

    try:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        resp = await client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type if mime_type in ("image/jpeg", "image/png", "image/gif", "image/webp") else "image/jpeg",
                            "data": base64.b64encode(image_bytes).decode("ascii"),
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        text = "".join(getattr(block, "text", "") for block in resp.content)
        data = json.loads(text[text.index("{"): text.rindex("}") + 1])
        verdict = data.get("verdict")
        confidence = data.get("confidence")
        reasoning = (data.get("reasoning") or "")[:500]
        if verdict not in _VALID_VERDICTS:
            return None
        if confidence not in _VALID_CONFIDENCE:
            confidence = None
        return {"verdict": verdict, "confidence": confidence, "reasoning": reasoning}
    except Exception:
        logger.exception("AI (Claude) orqali vazifa skrinshotini tekshirishda xatolik")
        return None
