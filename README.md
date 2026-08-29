# Figo3D bot — @figo3D_bot

Bu bot mijozlarga 3D-print qilingan haykalcha, kalitcha va sovg'a buyumlarini
katalogdan tanlab, buyurtma berish imkonini beradi. Buyurtma qabul qilingach,
sizga (adminga) avtomatik xabar keladi.

**Hozircha ishlaydigan qism:** Bosh menyudagi pastki tugmalar
(**🗂 Katalog, 🛒 Savat, 📦 Buyurtmalarim, 👤 Profil, 🎨 Shaxsiy buyurtma,
☎️ Aloqa**) orqali mijoz **BARCHA** amalni — katalogni ko'rish, savatga
qo'shish, **butun buyurtma berish jarayonini** (ism/telefon/manzil,
promo-kod, to'lov usuli — hamyon/karta/naqd), **profilni** saqlash,
**buyurtmalar tarixini** ko'rish, **shaxsiy (o'z rasmidan) buyurtma
so'rovi** yuborish va **aloqa ma'lumotlarini** ko'rish — oddiy Telegram
xabar almashinuvi orqali qiladi (bu eng barqaror usul). Bundan tashqari,
xabar yozish maydoni yonidagi **"🛍 Do'kon"** tugmasi orqali ochiladigan
veb-do'kon (Mini App) ham bor — u endi FAQAT mahsulotlarni chiroyli
(rasm-kartochka) ko'rinishda ko'rish va savatga qo'shish uchun qulay
muqobil (pastda "Veb-do'kon (Mini App)" bo'limiga qarang). Bundan tashqari:
mijoz sharhlari va reytingi, ichki hamyon (balans), Telegram ichida karta
orqali to'lov (Click/Payme ulangach), **bir nechta admin/hamkorga ruxsat
berish**, va — eng muhimi — endi **admin veb-paneli** orqali buyurtmalarni,
hisob to'ldirish so'rovlarini va mahsulotlarni chatga yozmasdan, chiroyli
veb-sahifadan boshqarish mumkin (pastda "Admin veb-paneli" bo'limiga
qarang).

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
   - `ADMIN_IDS` = **ixtiyoriy.** Yana boshqa odamlarga (masalan 3D-print
     hamkoringizga) ham admin ruxsati bermoqchi bo'lsangiz, ularning ID
     raqamlarini vergul bilan ajratib shu yerga yozing (masalan:
     `111111111,222222222`) — pastda "Bir nechta admin qo'shish" bo'limiga
     qarang
   - `CONTACT_INFO` = **ixtiyoriy.** Mini App'ning "Aloqa" bo'limida
     mijozlarga ko'rsatiladigan matn (masalan: `@figo3d_support yoki +998 90
     123 45 67`)
   - `PAYMENT_INFO` = mijozlarga ko'rsatiladigan to'lov rekvizitlaringiz
     (masalan: `Karta: 8600 1234 5678 9012 - F. Familiya (Payme/Click ham shu
     kartaga)`) — bu hisobni to'ldirish so'rovida mijozga ko'rsatiladi
   - `PAYMENT_PROVIDER_TOKEN` = **hozircha bo'sh qoldiring.** Click'dan API
     tokenini olganingizda shu nom bilan qo'shasiz (pastda "Click/Payme
     to'lovini ulash" bo'limiga qarang) — token yo'qligida bot avvalgidek
     hamyon/naqd usullari bilan ishlayveradi, hech narsa buzilmaydi
   - `TURSO_DATABASE_URL` va `TURSO_AUTH_TOKEN` = **tavsiya etiladi**,
     lekin ixtiyoriy — ma'lumotlaringiz (buyurtmalar, hamyon balanslari,
     mahsulotlar) Render diski tozalanganda ham yo'qolib qolmasligi uchun.
     Pastda **"Ma'lumotlar bazasini doimiy saqlash (Turso)"** bo'limida
     qadam-baqadam tushuntirilgan — hozircha bo'sh qoldirsangiz ham bot
     ishlayveradi (avvalgidek, faqat mahalliy fayl bilan)
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

### 🛍 Veb-do'kon (Mini App) — endi mijozlarning YAGONA kirish nuqtasi

⚠️⚠️ **29-avgust: YANA O'ZGARDI (oxirgi va joriy holat).** Ilgari (27-28
avgustgacha) Mini App faqat katalog+savat uchun ishlatilardi, buyurtma
berish/to'lov esa "ishonchliroq" deb chatning pastki tugmalariga
qaytarilgan edi. Endi siz ANIQ so'radingiz: **butun xarid jarayoni — savat,
shaxsiy ma'lumotlar, to'lov, hamyon to'ldirish — hammasi Mini App
ICHIDA bo'lsin**, va pastdagi chat tugmalari (Katalog, Savat, Buyurtmalarim
va h.k.) mijozlar uchun BUTUNLAY OLIB TASHLANSIN. Shunday qilindi — bu
avvalgi "webview ishonchsiz" qarorini ongli ravishda bekor qiladi; agar
kelajakda Mini App yana muammo bersa, shu bo'lim va "Pastki tugmalar olib
tashlandi" bo'limiga qarang (o'zgartirish oson, tarix git log'da saqlanadi).

Endi oddiy mijoz botga `/start` bossa, pastda **hech qanday** matnli tugma
ko'rmaydi — faqat xabar yozish maydoni yonidagi doimiy **"🛍 Do'kon"**
tugmasi orqali kiradi. U yerda:

- Katalog (bo'lim/kichik bo'lim, mahsulot tafsiloti, galereya)
- Savat (miqdorni ➕/➖ bilan o'zgartirish)
- **Savat → "✅ Buyurtmani yakunlash"**: tugma tepasida endi ism-familiya/
  telefon/manzil maydonlari bor — profildan avtomatik to'ldiriladi, lekin
  **tahrirlanishi mumkin** (masalan boshqa odamga sovg'a qilib
  yuborayotganda, boshqa manzilga)
- **To'lov (checkout)** — Mini App ichida yangi ekran: buyurtma xulosasi,
  promo-kod kiritish, joriy hamyon balansi va:
  - agar hamyonda yetarli mablag' bo'lsa — **"✅ Hamyondan to'lash"**
    tugmasi (bosilganda buyurtma DARHOL yaratiladi, hamyondan yechiladi)
  - agar yetmasa — **"💰 Hamyonni to'ldirish"** tugmasi (pastga qarang)
- **Profil** (ko'rish/tahrirlash + "💰 Hamyonni to'ldirish" tugmasi —
  xaridsiz ham, oldindan to'ldirish uchun)
- Buyurtmalar tarixi, Shaxsiy buyurtma so'rovi, Yangiliklar — avvalgidek

Bularning barchasi chap tomonlama menyu orqali ham ochiladi (pastdagi
"Mini App'da chap tomonlama menyu" bo'limiga qarang).

**Muhim (xavfsizlik zaxirasi):** bu faqat Render'da (haqiqiy https manzil
bilan, `WEBAPP_URL` sozlangan bo'lsa) ishlaydi. Agar biror sababga ko'ra
`WEBAPP_URL` bo'sh bo'lsa (masalan mahalliy sinov muhiti) — mijozga
"Do'kon" tugmasi umuman ko'rinmaydi VA pastda ham hech qanday tugma yo'q,
shuning uchun `/start` xabarida shunday holatda alohida ogohlantirish
matni chiqadi. **Production'da (Render'da) `WEBAPP_URL` doim sozlangan
bo'lishi shart** — aks holda mijozlar botdan umuman foydalana olmaydi.

### Admin veb-paneli — buyurtma/mahsulotlarni chatsiz, veb-sahifadan boshqarish

Endi `/admin` buyrug'ini yozganda chiqadigan xabarda **"🖥 Boshqaruv panelini
ochish"** tugmasi bor — bu ham xuddi mijozlar do'koni kabi veb-sahifa
(Mini App) ko'rinishida ochiladi, lekin FAQAT sizga (va ruxsat bergan
hamkorlaringizga) mo'ljallangan. Tab'lari:

- **Buyurtmalar** — endi 5 ta bosqich (bo'lim) bilan, pastda "Buyurtma
  bosqichlari" bo'limiga qarang
- **Shaxsiy** — hali javob berilmagan shaxsiy buyurtma so'rovlari (rasm bilan)
- **To'ldirish** — kutilayotgan hisob to'ldirish so'rovlari, "✅ Tasdiqlash"/
  "❌ Rad etish" tugmalari bilan
- **Mahsulotlar** — mavjud mahsulotlar ro'yxati + pastki o'ng burchakdagi
  "➕" tugmasi orqali yangi mahsulot qo'shish (bir nechta rasm bilan birga)
- **📊 Statistika** — mijozlar soni, eng ko'p sotilayotgan mahsulotlar,
  viloyat taqsimoti (pastdagi "Statistika bo'limi" ga qarang)

**Xavfsizlik:** panelga FAQAT `ADMIN_CHAT_ID`/`ADMIN_IDS` ro'yxatidagi
Telegram ID'lar kira oladi — Telegram'ning o'zi imzolab yuboradigan
maxfiy ma'lumot (`initData`) har bir so'rovda serverning o'zida tekshiriladi,
shuning uchun havolani bilib olgan boshqa odam ham kira olmaydi. Chatdagi
eski usul (`/admin` orqali mahsulot qo'shish, buyurtma tugmalari va h.k.)
ham avvalgidek ishlayveradi — ikkalasidan xohlaganingizni ishlatishingiz
mumkin, ikkalasi bir xil ma'lumot bilan ishlaydi.

**Bu — yangi imkoniyat, ishlatishdan oldin diqqat bilan sinab ko'ring**
(masalan bitta sinov mahsulot qo'shib-o'chirib ko'ring), ayniqsa real
buyurtmalar/to'lovlarni tasdiqlashdan oldin. Va mijozlar do'koni kabi, bu
ham faqat Render'da (haqiqiy https manzil bilan) ishlaydi — mahalliy
kompyuteringizda sinaganingizda "🖥 Boshqaruv panelini ochish" tugmasi
umuman ko'rinmaydi, chatdagi eski `/admin` usuli esa ishlayveradi.

### ✅ Yangi: Buyurtma bosqichlari (27-avgust, keyinchalik kengaytirildi)

Avval buyurtmani "✅ Qabul qildim" deb belgilagach, u ro'yxatdan BUTUNLAY
g'oyib bo'lardi — uni yanada oldinga surish (masalan "chiqarib
yubordim" deb belgilash) imkoni yo'q edi. Endi buyurtma to'liq bosqichdan
o'tadi, admin panelning **"📦 Buyurtmalar"** bo'limida 5 ta kichik bo'lim
(tab) bor:

1. **🆕 Qabul qilish** — hali javob berilmagan yangi buyurtmalar. "✅
   Qabul qilish" bosilsa — buyurtma keyingi bo'limga o'tadi.
2. **🛠 Yig'ish** — qabul qilingan, hozir tayyorlanayotgan buyurtmalar.
   "🚚 Chiqarib yubordim" bosilsa — keyingi bo'limga o'tadi.
3. **🚚 Chiqarib yuborilgan** — yo'lda bo'lgan buyurtmalar. "✅ Yetkazildi"
   bosilsa — arxivga o'tadi.
4. **📁 Arxiv** — yakunlangan (yetkazib berilgan) buyurtmalar.
5. **⚠️ Muammo** — davom ettirib bo'lmagan buyurtmalar (ALOHIDA bo'lim —
   avval "Arxiv" bilan bitta joyda aralashib turardi, endi diqqat talab
   qiladigan buyurtmalar tugallanganlardan aniq ajratilgan).

Har bir bosqichda (1, 2, 3-bo'limlarda) qo'shimcha **"⚠️ Muammo"** tugmasi
ham bor — agar biror sababga ko'ra (mijoz bilan bog'lanib bo'lmayapti,
mahsulot yo'q va h.k.) buyurtmani davom ettirib bo'lmasa, shu tugma bilan
istalgan bosqichdan to'g'ridan-to'g'ri "⚠️ Muammo" bo'limiga o'tkazish
mumkin. **Yangi:** bu tugma endi bosilganda avval sababni (izohni)
so'raydi — admin panelda kichik forma, chatda esa oddiy matn xabari
sifatida ("-" deb yozsa, sababsiz belgilanadi). Yozilgan sabab admin
panelda "⚠️ Muammo" bo'limidagi buyurtma kartochkasida, chatdagi buyurtma
xabarida va mijozga yuboriladigan xabarda ham ko'rinadi.

Har bir bosqich o'zgarganda mijozga ham avtomatik xabar boradi (masalan
"🚚 Buyurtmangiz chiqarib yuborildi"), va mijoz "📦 Buyurtmalarim"
bo'limida buyurtmasining joriy holatini har doim ko'rib turadi ("✅ Qabul
qilindi, yig'ilmoqda" → "🚚 Chiqarib yuborildi" → "📦 Yetkazildi").

Bu bosqichlar chatning o'zidan ham (har bir yangi buyurtma xabari ostidagi
tugmalar orqali) boshqariladi — admin panel va chat bir xil ma'lumot bilan
ishlaydi, xohlagan birini ishlatishingiz mumkin.

### ✅ Yangi: Katalog ichida kichik bo'lim (subkategoriya)

Endi mahsulot qo'shishda bo'limdan tashqari ixtiyoriy **"Kichik bo'lim"**
ham ko'rsatish mumkin (masalan "Sovg'alar" bo'limi ichida "Hayvonlar",
"Multfilm qahramonlari" kabi kichik bo'limlar). Bu maydonni bo'sh
qoldirsangiz, mahsulot avvalgidek to'g'ridan-to'g'ri bo'lim ichida
ko'rinadi — hech narsa buzilmaydi.

- **Chatdagi katalog**: bo'lim tanlanganda, agar ichida kichik bo'limlar
  bo'lsa, avval ularning ro'yxati chiqadi (+ "📦 Hammasini ko'rish" tugmasi
  — kichik bo'limga ega bo'lmagan mahsulotlarni ham birga ko'rish uchun).
- **Mini App ("🛍 Do'kon")**: bo'lim tablari ostida, agar kerak bo'lsa,
  kichik bo'limlar uchun qo'shimcha kichikroq tugmalar qatori chiqadi
  ("Hammasi" + har bir kichik bo'lim nomi).
- **Admin panel**: mahsulot qo'shish formasida "Bo'lim" yonida "Kichik
  bo'lim (ixtiyoriy)" maydoni bor.

### ✅ Yangi: Statistika bo'limi (admin panel)

Admin panelga **"📊 Statistika"** degan yangi tab qo'shildi:

- **Xarid qilgan mijoz** — kamida bitta buyurtma bergan noyob odamlar soni
- **Botni ko'rgan odam** — /start bosgan HAMMA odamlar soni (buyurtma
  bermagan bo'lsa ham)
- **Jami buyurtma** — barcha vaqtdagi umumiy buyurtmalar soni
- **🏆 Eng ko'p buyurtma qilinayotgan** — mahsulotlar nomi bo'yicha,
  qancha marta buyurtma qilinganiga qarab ko'pdan kamga
- **📍 Viloyatlar bo'yicha** — buyurtmalardagi manzil matnidan TAXMINAN
  aniqlangan viloyat/shahar taqsimoti

**Muhim cheklov:** "jinsi" va "yoshi" statistikasi YO'Q — Telegram bu
ma'lumotni botga umuman bermaydi, buni bilish uchun mijozdan alohida
so'ralishi kerak bo'lardi. Buni suhbatda muhokama qildik va hozircha
qo'shilmadi (agar kelajakda kerak bo'lsa, profilga ixtiyoriy savol
sifatida qo'shish mumkin). Shuningdek, viloyat statistikasi 100% aniq
emas — u mijoz yozgan ERKIN manzil matnidan taxminan topiladi (masalan
mijoz "Chilonzor" deb yozib, "Toshkent" so'zini yozmasa, "Aniqlanmadi"
toifasiga tushadi).

### ✅ Yangi: Pul bo'yicha to'liq hisobot (Statistika bo'limida)

**"📊 Statistika"** bo'limiga endi **"💰 Pul bo'yicha hisobot"** va
**"💳 To'lov usuli bo'yicha"** kartalari ham qo'shildi:

- Jami tushum (barcha buyurtmalar bo'yicha, "⚠️ Muammo" deb belgilanganlar
  hisobga KIRMAYDI)
- 📁 Yakunlangan (arxivga o'tgan, ya'ni yetkazib berilgan) buyurtmalar
  summasi
- ⏳ Hali jarayonda bo'lgan (yangi/yig'ilayotgan/yo'lda) buyurtmalar summasi
- 📅 Bugungi, 🗓 shu haftadagi, 📆 shu oydagi tushum
- 📊 O'rtacha buyurtma summasi
- 💳 To'lov usuli (hamyondan / naqd-karta operator bilan / Click-Payme
  karta) bo'yicha buyurtmalar soni va summasi

**Muhim:** bu hisobotning to'g'ri ishlashi uchun har bir yangi
buyurtmaning to'lov usuli endi alohida saqlanadi (avval faqat holatdan
[status] taxmin qilinardi, lekin holat buyurtma bosqichdan o'tganda
o'zgarib ketgani uchun asl to'lov usuli haqidagi ma'lumot yo'qolib
qolardi). **Eski buyurtmalarda** (bu yangilanishdan oldin yaratilgan)
to'lov usuli noma'lum bo'lgani uchun ular hisobotda "❔ Noma'lum (eski
buyurtma)" toifasida ko'rinadi — bu xato emas, shunchaki eski
ma'lumotlarda bu maydon yo'qligidan.

### ✅ Yangi: Shaxsiy buyurtmalar endi yo'qolib qolmaydi (arxiv)

Avval "🎨 Shaxsiy" bo'limida "✅ Bog'landim" tugmasi bosilgach, buyurtma
ro'yxatdan BUTUNLAY g'oyib bo'lardi — uni keyinchalik topib bo'lmasdi.
Endi bu bo'lim ikki tabga bo'lingan:

1. **🎨 Faol** — hali bog'lanilmagan, javob kutayotgan so'rovlar.
2. **✅ Bog'lanilgan** — "✅ Bog'landim" deb belgilangan so'rovlar (arxiv) —
   endi bu yerdan istalgan vaqtda qaytadan ko'rish mumkin, hech narsa
   yo'qolmaydi.

### ✅ Yangi: Mijoz bilan to'g'ridan-to'g'ri bog'lanish

Endi buyurtma va shaxsiy buyurtma kartochkalarida (ham chatda, ham admin
panelda) **"💬 Mijoz bilan bog'lanish"** tugmasi bor — bosilsa, to'g'ridan
mijozning shaxsiy Telegram profiliga/chatiga o'tkazadi (Telegram'ning
`tg://user?id=...` havolasi orqali). Bu tugma buyurtmaning HAR bir
bosqichida (shu jumladan Arxiv/Muammo kabi yakunlangan holatlarda ham)
ko'rinadi, shunda mijozga istalgan vaqt yozish imkoni bor.

**Muhim cheklov:** bu — botsiz mumkin bo'lgan ENG YAQIN "mijozga o'tish"
usuli, lekin Telegram'ning o'zi bu havolani har doim ham 100% kafolatlab
ochavermaydi (ba'zi Telegram versiyalarida yoki mijoz hech qachon siz
bilan umumiy chatda bo'lmagan bo'lsa ishlamasligi mumkin). Agar tugma
ishlamasa, muqobil yo'l — mijozning telefon raqamiga (kartochkada
ko'rsatilgan) qo'ng'iroq qilish yoki yozish.

### ✅ Yangi: `/admin` — endi tugma orqali ham (faqat adminlarga)

Avval boshqaruv panelini ochish uchun `/admin` buyrug'ini qo'lda yozish
kerak edi. Endi bu — pastdagi doimiy tugmalar qatorida **"🛠 Admin
panel"** degan alohida tugma sifatida ham chiqadi, lekin FAQAT sizga
(yoki `ADMIN_IDS`da ko'rsatilgan boshqa adminlarga) — oddiy mijozlar bu
tugmani umuman ko'rmaydi. `/admin` buyrug'ini yozish ham avvalgidek
ishlayveradi, tugma shunchaki qo'shimcha qulaylik.

### ✅ Tuzatildi: "Mijoz bilan bog'lanish" tugmasi (admin panel)

Avvalgi versiyada bu tugma bosilganda **"This content is blocked. Contact
the site owner to fix the issue."** degan xato chiqardi. Sababi: tugma
`tg://user?id=...` degan maxsus havoladan foydalangan, bu esa Mini App
(veb-sahifa) ICHIDA Telegram tomonidan xavfsizlik sababli bloklanar ekan
(oddiy chat xabarlarida esa bunday havola muammosiz ishlaydi — u yerga
tegilmadi).

Endi bu tugma mijozning Telegram **@username**'idan (agar mavjud bo'lsa)
foydalanadi — haqiqiy `https://t.me/username` havolasi orqali, bu
bloklanmaydi. Mijozning username'i bot bilan muloqot qilgan sari (/start
bosganda, buyurtma berganda, profilni saqlaganda va h.k.) avtomatik
"eslab qolinadi". **Agar mijoz Telegram'da username o'rnatmagan bo'lsa**,
tugma o'rniga "📵 Telegram username'i noma'lum — faqat telefon orqali
bog'laning" degan izoh chiqadi (kartochkada mijozning telefon raqami
allaqachon ko'rsatilgan).

### ✅ Yangi: Mini App'da chap tomonlama menyu

Mijozlar uchun "🛍 Do'kon" Mini App'iga endi yuqori chap burchakda **☰**
tugmasi bilan ochiladigan menyu qo'shildi, 7 ta bo'lim bilan:

1. **👤 Profil** — ism/telefon/manzilni ko'rish va tahrirlash, hamyon
   balansini ko'rish
2. **🗂 Mahsulotlar** — katalogga qaytaradi (bosh sahifa)
3. **🎨 Shaxsiy buyurtmalar** — o'z rasmingizdan buyurtma so'rovi yuborish
   formasi (rasm + tavsif + ism/telefon/manzil)
4. **🛒 Savat** — mavjud savat oynasi
5. **📦 Buyurtmalar** — avvalgi buyurtmalaringiz va ularning holati
   (faqat ko'rish uchun)
6. **📰 Yangiliklar** — admin joylashtirgan e'lon/aksiyalar
7. **💬 Chat** — Mini App'ni yopib, botning asosiy chatiga qaytaradi

**Muhim:** buyurtma berish (to'lov, promo-kod) jarayoni bu menyuga
KIRITILMAGAN — u ataylab hamon FAQAT chatning o'zida ishlaydi, chunki
aynan shu qism avval Mini App'ning veb-ko'rinishida ishonchsiz chiqib
qolgan edi (yuqoridagi "🛍 Veb-do'kon" bo'limiga qarang). Yangi qo'shilgan
Profil/Buyurtmalar/Shaxsiy buyurtma/Yangiliklar bo'limlari bundan ancha
sodda (faqat ko'rish yoki oddiy forma yuborish) bo'lgani uchun xavfsiz
qo'shildi.

### ✅ Yangi: "📰 Yangiliklar" bo'limi

Admin panelga yangi **"📰 Yangiliklar"** tab qo'shildi — bu yerdan matn
(va ixtiyoriy rasm) bilan e'lon yoki aksiya joylashtirishingiz mumkin
(masalan "Bu hafta barcha sovg'alarga -15% chegirma!"). Joylashtirilgan
e'lon darhol mijozlarning Mini App'idagi "📰 Yangiliklar" bo'limida
ko'rina boshlaydi, eng yangisidan boshlab. E'lonni o'chirish uchun
kartochkadagi "🗑 O'chirish" tugmasi bor.

### Bir nechta admin qo'shish

Agar buyurtmalarni siz bilan birga boshqa odam ham (masalan 3D-print
hamkoringiz) ko'rib, qabul qilishini xohlasangiz — Render'ning Environment
Variables bo'limida **YANGI** o'zgaruvchi sifatida `ADMIN_IDS` nomi bilan
(bu `ADMIN_CHAT_ID`dan BOSHQA, alohida nom) ularning Telegram ID
raqamlarini vergul bilan ajratib qo'shing (masalan: `111111111,222222222`).

⚠️ **Muhim:** `ADMIN_CHAT_ID`ni qayta yozmang/o'zgartirmang — u sizda
allaqachon bor, Render esa bir xil nomli o'zgaruvchini ikki marta
qo'shishga ruxsat bermaydi ("Duplicate key... is not allowed" degan xato
shundan). Ikkinchi (va undan ko'p) odamlar UCHUN har doim `ADMIN_IDS`
degan **BOSHQA** nom ishlatiladi — `ADMIN_CHAT_ID` esa o'zgarishsiz qoladi,
u avtomatik ravishda `ADMIN_IDS` ro'yxatiga qo'shib olinadi.

Shundan so'ng: yangi buyurtma, shaxsiy buyurtma so'rovi va hisob to'ldirish
so'rovi haqidagi xabarlar **HAMMA** adminlarga yuboriladi, va hammasi
`/admin` buyrug'i hamda admin veb-paneliga kira oladi.

### Savat: miqdorni ➕/➖ qilish

Endi "Savatga qo'shish" tugmasi bosilganda mahsulot sahifasidagi tugma
darhol o'zgarib, savatda nechta borligini ko'rsatadi (masalan "➕ Yana
qo'shish (savatda: 2 ta)"), va yuqorida qisqa xabar ham chiqadi — shu bilan
qo'shilgani sezilarli bo'ladi. Savat sahifasida ("🛒 Savat" tugmasi) har bir
mahsulot qatorida ➖ va ➕ tugmalari bor — ular orqali miqdorni birma-bir
kamaytirish yoki oshirish mumkin (0 ga tushsa, mahsulot savatdan butunlay
o'chadi). Butunlay o'chirish uchun bir necha marta ➖ bosish kifoya, yoki
"🗑 Savatni tozalash" bilan hammasini bir yo'la tozalash mumkin.

### Pastki tugmalar OLIB TASHLANDI (29-avgust — joriy holat)

Ilgari (28-avgustgacha) bosh menyudagi doimiy matnli tugmalar (🗂 Katalog,
🛒 Savat, 📦 Buyurtmalarim, 👤 Profil, 🎨 Shaxsiy buyurtma, ☎️ Aloqa)
har doim ko'rsatilar va BARCHA amal shular orqali ishlardi. Endi bu
**butunlay olib tashlandi** — oddiy mijozlarga pastda hech qanday tugma
ko'rsatilmaydi (`keyboards.main_menu_keyboard` endi ularga
`ReplyKeyboardRemove()` qaytaradi), faqat yuqorida tasvirlangan **"🛍
Do'kon"** Mini App orqali ishlaydi.

**FAQAT adminlarga** (`config.ADMIN_IDS` ro'yxatida bo'lganlarga) bitta
**"🛠 Admin panel"** tugmasi qoladi — boshqa hech narsa yo'q.

Diqqat: chatdagi eski matn-buyruq handler'lari (masalan "🗂 Katalog" so'zi
kelganda katalogni ko'rsatuvchi kod) DASTURDAN o'chirilmagan, faqat
ularni chaqiruvchi TUGMA olib tashlangan — shuning uchun mijoz qo'lda shu
so'zlarni yozib yuborsa, baribir ishlab turadi (bu ataylab shunday
qoldirilgan, xavfsizroq — kelajakda kerak bo'lsa, tugmalarni qaytarish
oson).

### Shaxsiy profil va manzilni tasdiqlash

"👤 Profil" tugmasi orqali mijoz o'z ism-familiyasi, telefon raqami va
manzilini bir marta kiritib saqlab qo'yishi mumkin. Keyingi safar buyurtma
berayotganda ("🛒 Savat" → "✅ Buyurtma berish"), bot ism/telefon/manzilni
BARIBIR HAR DOIM birma-bir so'raydi — lekin agar saqlangan qiymat bo'lsa,
u pastdagi tugmada ko'rinadi (masalan avvalgi manzil tugma sifatida
chiqadi) — mijoz shuni bosib bir zumda tasdiqlashi, yoki o'rniga
yangisini yozib yuborishi mumkin (masalan do'stiga sovg'a
yuborayotganda, boshqa manzil bilan). Bu ataylab shunday: manzil
HECH QACHON ko'rsatmasdan, sinovsiz avtomatik ishlatilmaydi — mijoz doim
uni ko'rib, tasdiqlab o'tadi. Har bir muvaffaqiyatli buyurtmadan so'ng eng
oxirgi kiritilgan ma'lumot profilga saqlanib qoladi.

### Ichki hamyon (balans) tizimi va Mini App'dagi to'lov (29-avgust yangilandi)

Endi to'lov **faqat hamyondan** amalga oshiriladi va butunlay Mini App
ichida (yuqoridagi "🛍 Veb-do'kon" bo'limiga qarang): savat → shaxsiy
ma'lumotlar → to'lov ekrani → "✅ Hamyondan to'lash". Hamyonda mablag'
yetmasa — o'sha yerdanoq "💰 Hamyonni to'ldirish" tugmasi bilan davom
etiladi (yoki Profil sahifasidan, oldindan). Eski naqd/operator va
Telegram-karta (Click/Payme invoice) to'lov usullari DASTURDAN
o'chirilmagan (kodda ishlab turibdi), lekin Mini App'ning yangi to'lov
ekranida ENDI KO'RSATILMAYDI — faqat hamyon.

**Hamyonni to'ldirish — 2 usul (Mini App'da ham, chatda ham bir xil):**

1. **⚡ Click orqali (avtomatik)** — hozircha **"Tez kunda"** deb
   ko'rsatiladi, bosilmaydi (Click kompaniyasidan API hali olinmagan).
   Tayyor bo'lgach, shu joyni ishlaydigan tugmaga almashtirish kifoya.
2. **💳 Bank kartasiga o'tkazib, skrinshot yuborish** — `PAYMENT_INFO`
   rekvizitlariga o'tkazib, chekning skrinshotini yuboradi. **⚠️ Skrinshot
   ENDI MAJBURIY** — avval "skrinshotsiz yuborish" degan tugma bor edi, u
   OLIB TASHLANDI (ham Mini App'da, ham chatdagi "💰 Hisobni to'ldirish"
   oqimida). Skrinshotsiz so'rov serverda rad etiladi.

Har ikkala usulda ham so'rov sizga (admin) darhol skrinshot va "✅
Tasdiqlash" / "❌ Rad etish" tugmalari bilan keladi. **Tasdiqlaganingizda**
— va faqat shundagina — mablag' mijozning hamyoniga qo'shiladi (bu darhol
emas, operator tasdig'i kerak — xuddi avvalgidek).

### 📰 Yangiliklar — endi HAMMAGA xabarnoma (29-avgust)

Admin panelda "📰 Yangiliklar" bo'limiga yangi e'lon qo'shilganda, botni
kamida bir marta ko'rgan **BARCHA** foydalanuvchilarga (faqat xarid
qilganlarga emas) avtomatik Telegram xabari yuboriladi — e'lon matni va
**qachon joylashtirilgani** (masalan "28-avgust, 15:40") bilan birga.
Agar kimdir botni bloklagan yoki hali `/start` bosmagan bo'lsa, xabar
shunchaki o'sha birovga yetmaydi — qolganlarga to'sqinlik qilmaydi.

### ✅ Hisob to'ldirishni tasdiqlashda summani qo'lda tuzatish (29-avgust)

**Muammo:** mijoz "necha so'm to'ldirmoqchisiz" deb so'ralganda bir summa
yozadi, lekin keyin bank kartasiga BOSHQA summa o'tkazishi mumkin (kam,
ko'p, yoki tranzaksiyada xatolik bo'lib umuman noaniq bo'lishi mumkin) —
avval "✅ Tasdiqlash" tugmasi HAR DOIM mijoz SO'RAGAN summani hamyonga
qo'shardi, skrinshotda haqiqatda nima ko'rinishidan qat'i nazar.

**Endi tuzatildi — 2 joyda:**

- **Admin panel → "💰 To'ldirish" bo'limi:** har bir so'rov kartasida endi
  summa maydoni bor — dastlab mijoz so'ragan summa bilan to'ldirilgan,
  lekin siz uni skrinshotga qarab kerakli songa **o'zgartirib**, keyin
  "✅ Tasdiqlash" bosishingiz mumkin. Aynan shu (tahrirlangan) summa
  hamyonga qo'shiladi.
- **Chatdagi tasdiqlash tugmalari:** "✅ Tasdiqlash" (bu hamon so'ralgan
  summani to'liq tasdiqlaydi — mos kelgan holatlar uchun tezkor) yonida
  endi **"✏️ Boshqa summa"** tugmasi ham bor — bosilganda bot "Necha so'm
  tasdiqlaysiz?" deb so'raydi, siz raqam yozasiz, shu summa qo'shiladi.

Ikkala usulda ham, agar tasdiqlangan summa mijoz so'raganidan farq qilsa,
mijozga yuboriladigan xabarda bu **aniq tushuntiriladi** ("Siz X so'm
so'ragan edingiz, lekin to'lov tafsilotlariga ko'ra Y so'm tasdiqlandi") —
mijoz hayron qolib qolmasligi uchun.

**Qo'shimcha: "🧾 Balansni qo'lda tuzatish"** — admin panelning "💰
To'ldirish" bo'limi tepasida endi alohida mini-forma bor: istalgan
mijozning Telegram ID'sini kiritib, istalgan summani (musbat = qo'shish,
manfiy = ayirish) va ixtiyoriy izoh bilan hamyoniga TO'G'RIDAN-TO'G'RI
ta'sir qilish mumkin — bu hech qanday hisob to'ldirish so'roviga bog'liq
emas. Foydali holat: mijoz pul o'tkazgan, lekin biror sababga ko'ra bot
orqali so'rov yaratilmagan yoki tranzaksiyada xatolik bo'lgan — shu orqali
kompensatsiya qilib qo'yish mumkin. Mijozga bu haqda ham avtomatik xabar
boradi.

### ✅ "Operatorga yozish" — mijoz endi Mini App ichidan murojaat yubora oladi (29-avgust)

**Muammo topildi:** pastki chat tugmalari olib tashlangandan keyin (yuqoriga
qarang), Mini App sidebar'idagi "💬 Chat" tugmasi shunchaki ilovani yopib,
mijozni botning oddiy chatiga qaytarardi — lekin u yerda mijoz yozgan erkin
matnni "ushlab", sizga yo'naltiradigan HECH QANDAY mexanizm yo'q edi
(eski "☎️ Aloqa" tugmasi ham faqat STATIK aloqa ma'lumotini ko'rsatardi,
mijozdan xabar OLMASDI). Shuning uchun mijozlar "murojaat yubora
olmayapman" deb shikoyat qilishgan — bu to'g'ri edi, funksiya haqiqatan
ham yo'q edi.

**Tuzatildi:** sidebar'dagi bu bo'lim endi **"💬 Operatorga yozish"** deb
nomlangan va to'liq ishlaydigan forma — mijoz aloqa ma'lumotlarini ko'radi,
xabarini yozadi, "✅ Yuborish"ni bosadi — xabar SHU ZAHOTI sizga (barcha
adminlarga) Telegram orqali yetib boradi, ostida "💬 Mijoz bilan
bog'lanish" tugmasi bilan (to'g'ridan-to'g'ri mijozning shaxsiy chatiga
o'tish uchun, agar @username saqlangan bo'lsa).

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

## Ma'lumotlar bazasini doimiy saqlash (Turso)

Render'ning **bepul** tarifida disk "doimiy" emas — bot qayta ishga
tushganda (masalan, uzoq vaqt ishlatilmay qolgach, yoki texnik sabablarga
ko'ra) `figo3d.db` fayli (demak barcha buyurtmalar, sharhlar, promo-kodlar,
mijozlarning hamyon balanslari, saqlangan profillari va mahsulotlar/
rasmlar) tozalanib ketishi mumkin edi.

✅ **Bu endi hal qilindi** — bot endi ixtiyoriy ravishda **Turso** (bepul,
doimiy, SQLite-mos bulut baza) bilan ishlay oladi: har bir yozuvdan
(buyurtma, profil, mahsulot va h.k.) so'ng ma'lumot darhol bulutga ham
nusxalanadi, shuning uchun Render diski tozalansa ham hech narsa
yo'qolmaydi. Sozlash ixtiyoriy va tez:

1. [turso.tech](https://turso.tech) saytida bepul akkaunt oching (kredit
   karta talab qilinmaydi)
2. Yangi baza (database) yarating
3. Baza sahifasidan **"Database URL"** (`libsql://...` bilan boshlanadi) va
   **"Auth Token"**ni nusxalab oling
4. Render'ning **Environment Variables** bo'limiga qo'shing:
   - `TURSO_DATABASE_URL` = nusxalagan Database URL
   - `TURSO_AUTH_TOKEN` = nusxalagan Auth Token
5. **Save Changes** — Render botni avtomatik qayta ishga tushiradi

Ikkalasini ham bo'sh qoldirsangiz — muammo emas, bot avvalgidek faqat
mahalliy fayl bilan ishlayveradi (lekin yuqoridagi yo'qolish xavfi
qoladi). Bepul reja: 500 million o'qish/oy, 10 million yozish/oy, 5GB joy —
kichik-o'rta do'kon uchun yetarlicha.

✅ **Xavfsizlik to'ri qo'shildi:** endi agar `TURSO_DATABASE_URL`/
`TURSO_AUTH_TOKEN` noto'g'ri bo'lsa (masalan token eskirgan/bekor qilingan
bo'lsa), bot BUTUNLAY ishdan to'xtab qolmaydi — xatoni "Logs"ga aniq yozib,
avtomatik ravishda oddiy mahalliy fayl rejimiga tushib, ishlashda davom
etadi (Turso to'g'rilanguncha). Shunday bo'lsa, "Logs" bo'limida
`Turso bilan ULANIB BO'LMADI` degan qatorni ko'rasiz — bu holatda pastdagi
"Turso xatosi chiqsa" bo'limiga qarang.

Ulanish muvaffaqiyatli bo'lsa, "Logs" bo'limida
`Turso bilan dastlabki sinxronizatsiya muvaffaqiyatli` degan qatorni
ko'rasiz — shundan so'ng bir marta sinov buyurtma berib/mahsulot qo'shib
ko'ring, muammo chiqsa menga ayting.

#### Turso xatosi chiqsa (masalan "invalid JWT token")

Agar Logs'da token/ulanish bilan bog'liq xato ko'rinsa (masalan
`invalid JWT token: role was invalidated after token was issued` yoki
`401 Unauthorized`) — bu odatda token Turso tomonida bekor qilingan yoki
noto'g'ri nusxalangan degani. Turso'ning o'zi tokenlarni faqat siz
(yoki Turso paneli) aniq buyruq bergandagina bekor qiladi — masalan bitta
tokenni ikki marta ustma-ust "yaratish/rotate qilish" natijasida avvalgisi
avtomatik bekor bo'lishi mumkin. Tuzatish:

1. [turso.tech](https://turso.tech) saytida bazangizga kiring
2. Yangi (butunlay FRESH) **Auth Token** yarating — eskisiga tegmang, yangi
   nusxalab oling
3. Render'da `TURSO_AUTH_TOKEN` qiymatini shu yangi token bilan
   ALMASHTIRING (eskisini butunlay o'chirib, yangisini joylashtiring —
   boshida/oxirida bo'sh joy qolmasligiga e'tibor bering)
4. **Save Changes** — qayta deploy bo'lgach, Logs'ni qayta tekshiring

Bu davrda ham (token tuzatilmagunicha) bot mijozlar uchun to'liq ishlayveradi
— faqat ma'lumotlar Turso'ga emas, mahalliy faylga saqlanadi.

#### ✅ Tuzatildi: "savat/buyurtma berish yo'qolib qolishi" (`ValueError: file is not a database`)

Agar avval Logs'da `ValueError: file is not a database` degan xato bilan
birga savatga mahsulot qo'shish yoki "✅ Buyurtma berish" ishlamay qolgan
bo'lsa — sababi topildi va tuzatildi: fondagi davriy Turso sinxronlash
vazifasi (`start_periodic_sync`, har 25 soniyada ishlaydi) mijozning
so'rovi (masalan `/api/cart`) bilan **bir vaqtning o'zida**, bir-biridan
himoyalanmagan holda, bitta bazaga ulanishga tegishi mumkin edi — bu esa
vaqti-vaqti bilan mahalliy baza faylini buzib qo'yardi. Endi bu ikkalasi
hech qachon bir vaqtda ishlamaydi (bir xil qulf — "lock" orqali
navbat bilan ishlaydi). Bu narsa avtomatik tuzatilgan, sizdan hech qanday
qo'shimcha sozlash talab qilinmaydi — shu zip'ni GitHub'ga yuklab, Render
qayta deploy bo'lishini kutsangiz bas.
