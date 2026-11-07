# 🎓 O'quv Markaz Target CRM (Lead Management System)

Facebook va Instagram target reklamalaridan keladigan lidlarni qabul qilish, Telegram guruhga bir zumda bildirishnoma yuborish va Web CRM (Kanban doska) orqali boshqarish tizimi.

---

## 🚀 Imkoniyatlari

1. **Meta / Instagram / Facebook Lead Ads Webhook:**
   - Reklama formasini to'ldirgan o'quvchilar avtomatik tarzda bazaga yoziladi.
   - Meta Developers Webhook integratsiyasi tayyor (`/webhook/meta`).

2. **Telegram Guruhga Bir Zumda Bildirishnoma:**
   - Har bir yangi lid kelishi bilan o'quv markaz adminlari/operatorlari guruhiga batafsil xabar boradi.
   - Xabar ostidagi tugmalar orqali Telegramning o'zida statusni o'zgartirish mumkin:
     - 📞 *Bog'lanildi*
     - 📅 *Sinov darsiga yozildi*
     - ✅ *To'lov qildi*
     - ❌ *Rad etdi*
   - Xabar real vaqtda tahrirlanib, qaysi admin qachon o'zgartirgani ko'rinadi.

3. **Web CRM Dashboard (Kanban doska):**
   - Brauzer orqali ochiladigan qulay interfeys (`http://localhost:8000`).
   - 5 ta bosqichli Kanban voronkasi (Yangi ➡️ Bog'lanildi ➡️ Sinov darsi ➡️ To'lov ➡️ Rad etdi).
   - Ism, telefon va kurs bo'yicha tezkor qidiruv.
   - Bitta bosishda qo'ng'iroq qilish (`tel:`) va Telegram profilini ochish.
   - Barcha lidlarni **Excel (.xlsx)** formatida yuklab olish.

4. **Statistika va Konversiya:**
   - Bugungi va jami lidlar soni.
   - Sotuv konversiyasi foizi (ROI).
   - Telegramda `/stats` buyrug'i orqali hisobot olish.

---

## 🛠 O'rnatish va Ishga Tushirish

### 1. `.env` faylini sozlash
`.env` faylini oching va quyidagi ma'lumotlarni kiriting:

```env
# Telegram BotFather orqali olingan token
BOT_TOKEN=1234567890:AAH...

# Bildirishnoma borishi kerak bo'lgan Telegram guruh ID si (masalan: -1001234567890)
TELEGRAM_GROUP_ID=-1001234567890

# Meta / Facebook Lead Ads Webhook maxfiy kodi
META_VERIFY_TOKEN=lead_verify_secret_token_2026
```

> **Guruh ID sini qanday bilish mumkin?**
> Guruhga botni qo'shing va `/id` buyrug'ini yuboring. Bot guruh ID sini chiqarib beradi.

### 2. Tizimni ishga tushirish
Windowsda `run.bat` fayliga 2 marta bosing yoki terminalda:

```powershell
.\.venv\Scripts\activate
python run.py
```

- **Web CRM:** [http://localhost:8000](http://localhost:8000)
- **Target Formasi (Landing):** [http://localhost:8000/form](http://localhost:8000/form)
- **API Hujjatlari:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Instagram Target reklamasiga qo'yish (Ochiq Internet Havolasi)
Instagram target reklamangizga qo'yish uchun kompyuteringizdagi `public_link.bat` fayliga bosing:
U sizga bir lahzada bepul **`https://...`** havola beradi. O'sha havolaning orqasiga `/form` qo'shib, Instagramga qo'yasiz!

---

## 🌐 Facebook / Instagram Target Ads ga ulash

1. [developers.facebook.com](https://developers.facebook.com) ga kiring.
2. O'z ilovangizda **Webhooks** bo'limiga o'ting va `Page` obyektini tanlang.
3. Callback URL: `https://sizning-domeningiz.uz/webhook/meta`
4. Verify Token: `.env` dagi `META_VERIFY_TOKEN` (default: `lead_verify_secret_token_2026`).
5. `leadgen` hodisasiga obuna bo'ling.

