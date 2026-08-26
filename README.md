# Figo3D bot — @figo3D_bot

Bu bot mijozlarga 3D-print qilingan haykalcha, kalitcha va sovg'a buyumlarini
katalogdan tanlab, buyurtma berish imkonini beradi. Buyurtma qabul qilingach,
sizga (adminga) avtomatik xabar keladi.

**Hozircha ishlaydigan qism:** katalog (ko'p rasm/video bilan, endi to'liq
**bot orqali** boshqariladi — /admin), savat (miqdorni ➕/➖ qilish bilan),
buyurtma rasmiylashtirish, promo-kod/chegirma, mijoz sharhlari va reytingi,
shaxsiy (o'z rasmidan) buyurtma so'rovi, shaxsiy profil (ism/telefon/manzilni
saqlash va qayta ishlatish), ichki hamyon (balans), Telegram ichida karta
orqali to'lov (Click/Payme ulangach), admin xabarnomasi.

**Keyingi bosqichda qo'shiladi:** hozircha hisobni to'ldirish (hamyon)
qo'lda admin tasdig'i bilan ishlaydi (mijoz to'lov qilib, chekining
skrinshotini yuboradi, siz "✅ Tasdiqlash" bosasiz). Click provider tokeningiz
kelgach, buyurtmani Telegram ichida to'g'ridan-to'g'ri karta bilan to'lash
ham yoqiladi (4-qadamdagi `PAYMENT_PROVIDER_TOKEN` bo'limiga qarang).

---

## 1-qadam: Bot tokenini toping

Siz allaqachon @BotFather orqali @figo3D_bot botini yaratgansiz. Token esa
BotFather bilan yozishmangizda saqlanган — agar yo'qotgan bo'lsangiz:

1. Telegram'da **@BotFather** ga yozing
2. `/mybots` → **Figo 3D** → **API Token** tugmasini bosing
3. Chiqqan uzun kodni (masalan `7123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
   nusxalab, xavfsiz joyga saqlab qo'ying — bu keyingi qadamlarda kerak bo'ladi.

## 2-qadam: O'zingizning Telegram ID raqamingizni toping

Buyurtmalar sizga shu ID orqali yuboriladi.

1. Telegram'da **@userinfobot** ga yozing (yoki `/start` bosing)
2. U sizga sizning ID raqamingizni yuboradi (masalan `123456789`)
3. Shu raqamni saqlab qo'ying

## 3-qadam: Kodni GitHub'ga joylashtirish

Render.com kodni GitHub orqali oladi, shuning uchun avval GitHub'da bepul
akkaunt va repository (loyiha "papkasi") kerak.

1. [github.com](https://github.com) saytida ro'yxatdan o'ting (agar hali yo'q bo'lsa)
2. Yuqori o'ng burchakdagi **+** tugmasi → **New repository**
3. Repository nomi: `figo3d-bot` deb yozing → **Create repository**
4. Ochilgan sahifada **"uploading an existing file"** havolasini bosing
5. Shu arxivdagi barcha fayllarni (bot.py, config.py, db.py, products.py,
   keyboards.py, requirements.txt, handlers papkasi va boshqalar) shu yerga
   sudrab tashlang (drag & drop) — **faqat `.env` faylini yuklamang**, u shaxsiy
   tokeningizni saqlaydi
6. Pastda **Commit changes** tugmasini bosing

## 4-qadam: Render.com'da joylashtirish

1. [render.com](https://render.com) saytida ro'yxatdan o'ting — "Sign up with
   GitHub" orqali kirsangiz qulayroq bo'ladi (kredit karta talab qilinmaydi)
2. Dashboard'da **New +** → **Web Service**
3. GitHub'dagi `figo3d-bot` repositoryingizni tanlang va **Connect** bosing
4. Sozlamalarni to'ldiring:
   - **Name:** `figo3d-bot` (yoki xohlagan nom)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** Free
5. Pastroqda **Environment Variables** bo'limini toping va qo'shing:
   - `BOT_TOKEN` = 1-qadamda olgan tokeningiz
   - `ADMIN_CHAT_ID` = 2-qadamda olgan ID raqamingiz
   - `PAYMENT_INFO` = mijozlarga ko'rsatiladigan to'lov rekvizitlaringiz
     (masalan: `Karta: 8600 1234 5678 9012 - F. Familiya (Payme/Click ham shu
     kartaga)`) — bu hisobni to'ldirish so'rovida mijozga ko'rsatiladi
   - `PAYMENT_PROVIDER_TOKEN` = **hozircha bo'sh qoldiring.** Click'dan API
     tokenini olganingizda shu nom bilan qo'shasiz (pastda "Click/Payme
     to'lovini ulash" bo'limiga qarang) — token yo'qligida bot avvalgidek
     hamyon/naqd usullari bilan ishlayveradi, hech narsa buzilmaydi
6. **Create Web Service** tugmasini bosing

Render avtomatik ravishda kodni yuklab oladi, kerakli kutubxonalarni
o'rnatadi va botni ishga tushiradi (bu 2-5 daqiqa vaqt oladi). Jarayonni
"Logs" bo'limidan kuzatib borishingiz mumkin — oxirida
`Webhook rejimi yoqildi: https://...` degan qatorni ko'rsangiz, hammasi
tayyor.

## 5-qadam: Tekshirish

Telegram'da @figo3D_bot'ga o'ting va `/start` bosing — bosh menyu chiqishi
kerak. Katalogdan mahsulot tanlab, savatga qo'shib, buyurtma berib ko'ring —
buyurtma tugagach, sizning shaxsiy Telegram'ingizga (2-qadamda ko'rsatgan ID
orqali) yangi buyurtma haqida xabar kelishi kerak.

**Eslatma:** bepul Render rejasi 15 daqiqa hech kim yozmasa botni "uxlatib
qo'yadi" — keyingi xabarga javob ~30-60 soniya kechikishi mumkin (bu MVP
bosqichida muammo emas).

Shundan so'ng, botga **`/admin`** deb yozib, o'zingizning haqiqiy
mahsulotlaringizni (rasmlari bilan) qo'shishni boshlashingiz mumkin — pastda
"Mahsulot qo'shish/o'chirish" bo'limiga qarang.

---

## Yangi imkoniyatlar qanday ishlatiladi

### Savat: miqdorni ➕/➖ qilish

Endi "Savatga qo'shish" tugmasi bosilganda mahsulot sahifasidagi tugma
darhol o'zgarib, savatda nechta borligini ko'rsatadi (masalan "➕ Yana
qo'shish (savatda: 2 ta)"), va yuqorida qisqa xabar ham chiqadi — shu bilan
qo'shilgani sezilarli bo'ladi. Savat sahifasida ("🛒 Savat" tugmasi) har bir
mahsulot qatorida ➖ va ➕ tugmalari bor — ular orqali miqdorni birma-bir
kamaytirish yoki oshirish mumkin (0 ga tushsa, mahsulot savatdan butunlay
o'chadi). Butunlay o'chirish uchun bir necha marta ➖ bosish kifoya, yoki
"🗑 Savatni tozalash" bilan hammasini bir yo'la tozalash mumkin.

### Tugmalar

Bosh menyudagi 6 ta tugma endi 2 tadan qilib, 3 qatorga tekis joylashtirilgan
(Katalog/Savat, Buyurtmalarim/Profil, Shaxsiy buyurtma/Aloqa) — bir ustunga
tizilgan avvalgi ko'rinishdan ko'ra ancha ixcham va ko'zga yoqimli
(eslatma: tugma shrifti/piksel o'lchamini bot dasturi orqali o'zgartirib
bo'lmaydi — bu faqat Telegram ilovasining o'zi belgilaydi, bot faqat
tugmalarning necha ustunga joylashishini belgilay oladi).

### Shaxsiy profil va o'zim/sovg'a tanlovi

"👤 Profil" tugmasi orqali mijoz o'z ism-familiyasi, telefon raqami va
manzilini bir marta kiritib saqlab qo'yishi mumkin ("✏️ Ma'lumotlarni
yangilash" orqali). Keyingi safar buyurtma berayotganda, agar saqlangan
ma'lumot bo'lsa, bot avtomatik so'raydi: "🙋 O'zim uchun (saqlangan
ma'lumot)" — shu tugma bilan qayta yozmasdan davom etadi, yoki "🎁 Sovg'a /
boshqa manzil" — shu holda ism/telefon/manzilni har safargidek qo'lda
kiritadi (masalan do'stiga sovg'a yuborayotganda). Har bir muvaffaqiyatli
buyurtmadan so'ng eng oxirgi kiritilgan ma'lumot profilga saqlanib qoladi.

### Ichki hamyon (balans) tizimi

Profil sahifasida mijoz joriy balansini ko'radi. "💰 Hisobni to'ldirish"
tugmasi orqali: qancha to'ldirmoqchiligini yozadi → botning `PAYMENT_INFO`
rekvizitlarini ko'radi → to'lov qilgach, chekning skrinshotini yuboradi
(yoki skrinshotsiz ham davom etishi mumkin). So'rov sizga (admin) darhol
skrinshot va "✅ Tasdiqlash" / "❌ Rad etish" tugmalari bilan keladi.
**Tasdiqlaganingizda** — va faqat shundagina — mablag' mijozning hamyoniga
qo'shiladi. Keyingi buyurtmalarda, agar hamyonda yetarli mablag' bo'lsa,
mijoz "💰 Hamyondan to'lash" tugmasi bilan darhol to'lashi mumkin (operator
bilan alohida kelishmasdan) — bo'lmasa, avvalgidek "💵 Naqd/karta (operator
bilan)" orqali davom etadi. Bu — Payme/Click API ulanmaguncha ishlatiladigan
ichki to'lov tizimi; API ulangach, "Hisobni to'ldirish" qismini avtomatik
to'lovga almashtirish mumkin bo'ladi.

### Mahsulot qo'shish/o'chirish — endi kod bilan ishlash SHART EMAS

**Bu eng muhim o'zgarish.** Avval mahsulot va rasmlarni qo'shish uchun
`products.py` faylini qo'lda tahrirlab, GitHub'ga yuklab, qayta deploy
qilish kerak edi — va aynan shu jarayon sizning "rasmlar har safar
yangilaganimda o'chib ketyapti" degan muammoingizning sababi edi: men har
safar yangi tuzatish yuborganimda, arxivdagi `products.py` doim bo'sh
(namunaviy) rasmlar bilan qaytadan yaratilar edi — va siz butun arxivni
qayta yuklaganingizda, bu sizning avval qo'shgan real rasmlaringizni
tasodifan ustidan bosib, o'chirib qo'yardi. Kodning o'zi yoki Render'ning
aybi emas edi — muammo shu "har safar hammasini qayta yuklash" jarayonida
edi.

Endi mahsulotlar (nomi, narxi, rasmlari, videosi) kodda emas, botning
bazasida saqlanadi — bundan buyon men yuboradigan yangilanishlar
mahsulotlaringizga umuman tegmaydi. Qo'shish uchun:

1. Botga **`/admin`** buyrug'ini yozing (faqat siz — `ADMIN_CHAT_ID` — buni
   ko'rasiz va ishlata olasiz)
2. **"➕ Yangi mahsulot qo'shish"** tugmasini bosing
3. Bo'lim (mavjudidan tanlang yoki yangisini yozing) → nomi → tavsifi →
   narxi → rasmlarni birma-bir yuboring (tugagach "✅ Rasmlar tayyor") →
   xohlasangiz aylanish videosi → "✅ Saqlash"
4. Tayyor — mahsulot **darhol** katalogda ko'rinadi, hech qanday GitHub yoki
   Render bilan ishlash shart emas

Mahsulotni o'chirish uchun `/admin` → **"📋 Mahsulotlar ro'yxati"** →
kerakli mahsulot ostidagi **"🗑 O'chirish"** tugmasi (bosgach, "✅ Ha,
o'chirish" bilan tasdiqlaysiz).

Rasm sifatida yuborilgan har qanday fotosurat, video uchun esa video fayl
(GIF emas) qabul qilinadi. 2 tadan ortiq rasm/video bo'lsa, bot mijozga
ularni avtomatik "albom" ko'rinishida ko'rsatadi.

### Mijoz sharhlari

Mijozlar mahsulot sahifasida "⭐ Baho berish" tugmasi orqali 1-5 yulduz va
ixtiyoriy izoh qoldirishlari mumkin. O'rtacha baho va sharhlar soni mahsulot
sahifasida avtomatik ko'rinadi, qo'shimcha sozlash shart emas.

### Promo-kod (chegirma) yaratish

Faqat siz (admin) botga quyidagi buyruqni yozib, yangi chegirma kodi
yaratishingiz mumkin:

```
/promo YANGI10 10 50
```

Bu yerda `YANGI10` — kod nomi (mijozlar shu so'zni yozadi), `10` — chegirma
foizi, `50` — kod necha marta ishlatilishi mumkinligi (bu qismni
o'chirib qoldirsangiz, kod cheklovsiz ishlatiladi: `/promo YANGI10 10`).
Mijozlar buyurtma berayotganda manzildan keyin promo-kodni kiritish
imkoniyatiga ega bo'ladi.

### Shaxsiy buyurtma (o'z rasmidan)

Mijoz bosh menyudagi "🎨 Shaxsiy buyurtma" tugmasini bosib, o'z rasmini
yuboradi va nima xohlashini yozadi. Bu maxsus buyurtma bo'lgani uchun narx
oldindan belgilanmaydi — so'rov to'g'ridan-to'g'ri sizga (fotosurat bilan
birga) keladi, narxni mijoz bilan siz shaxsan kelishasiz.

### Click/Payme to'lovini ulash (Telegram ichida karta bilan to'lash)

Click'dan API (provider) tokenini olganingizda, buyurtmani Telegram ichida
to'g'ridan-to'g'ri karta bilan to'lash imkoniyatini yoqish uchun:

1. **@BotFather** ga yozing → `/mybots` → **Figo 3D** → **Payments**
2. Ro'yxatdan **Click** (yoki Payme, ikkalasi ham qo'llab-quvvatlanadi)ni
   tanlab, ular bergan sozlash bo'yicha ulaning — oxirida BotFather sizga
   uzun bir **provider token** beradi
3. Shu tokenni nusxalab, Render'ning Environment Variables bo'limiga
   `PAYMENT_PROVIDER_TOKEN` nomi bilan qo'shing → **Save Changes**
   (Render avtomatik qayta ishga tushiradi)

Shundan so'ng, buyurtma tasdiqlash bosqichida mijozlarga avtomatik ravishda
yangi **"💳 Karta orqali (Click/Payme)"** tugmasi ham chiqadi — bosilganda
Telegram'ning o'z to'lov oynasi ochiladi, mijoz karta orqali to'laydi, va
to'lov muvaffaqiyatli bo'lishi bilan buyurtma avtomatik yaratilib, sizga
xabar keladi (hech qanday qo'lda tasdiqlash shart emas — bu hamyonni
to'ldirish jarayonidan farqli o'laroq, to'liq avtomatik).

Token hali yo'q bo'lsa — hech narsa qilish shart emas, bu tugma shunchaki
ko'rinmay turadi, mijozlar hamyon yoki naqd/karta (operator bilan)
usullaridan foydalanaveradi.

---

## Muhim eslatma: ma'lumotlar bazasi haqida

Render'ning **bepul** tarifida disk "doimiy" emas — bot qayta ishga
tushganda (masalan, GitHub'ga yangi kod yuklaganingizda) `figo3d.db` fayli
(demak barcha buyurtmalar, sharhlar, promo-kodlar, **mijozlarning hamyon
balanslari, saqlangan profillari va ENDI mahsulotlar/rasmlar ham**)
tozalanib ketishi mumkin.

⚠️ Mahsulotlar endi (avvalgi products.py fayli o'rniga) shu bazada
saqlanayotgani va bot ichida "pul" (hamyon balansi) ham borligi uchun bu
masala avvalgidan ham muhimroq. Amalda: oddiy kodni yangilash/qayta deploy
qilish (masalan men yuborgan tuzatishlarni joylashtirish) odatda bazaga
tegmaydi — sizning "rasmlar yo'qolib turishi" muammoingiz aslida shundan
emas, balki `products.py` faylini har safar to'liq qayta yuklashdan kelib
chiqqan edi (yuqorida tushuntirilgan), va bu endi butunlay bartaraf etildi.
Lekin Render ba'zan (masalan uzoq vaqt servis to'xtab qolgach, yoki texnik
sabablarga ko'ra) diskni to'liq tozalashi ham mumkin — shuning uchun real
mijozlar pul kiritishni boshlashidan OLDIN, buni albatta hal qilish kerak —
masalan Render'ning pullik "Persistent Disk" xizmatiga yoki tashqi bazaga
(masalan bepul Postgres taklif qiluvchi xizmatlarga) o'tish orqali. Tayyor
bo'lganingizda shu masalani birga hal qilamiz.
