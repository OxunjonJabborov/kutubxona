# Kutubxonaga murojaat (4-amaliyot ishi, 8-variant)

FastAPI + SQLAlchemy + Jinja2. Login sahifasi, himoyalangan shaxsiy kabinet,
"Kitob nomi" va "Murojaat matni" formasi ("Yuborish" tugmasi), sessiya va "Chiqish".

## Talablar qanday bajarilgan
- Login — ism (`oxunjon`), parol — 12 belgi, familiya bilan (`Jabborov2026`).
- Login serverda tekshiriladi (`POST /login`), parol bazada **bcrypt xesh** ko‘rinishida saqlanadi.
- Sessiya — imzolangan cookie (2 soat), `Chiqish` tugmasi sessiyani tozalaydi.
- Kirishsiz `/cabinet` ochilmaydi (`/login` ga yo‘naltiradi).
- Mobil qurilmaga moslashgan (viewport + responsive CSS).

## Lokal ishga tushirish
```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
So‘ng http://127.0.0.1:8000 ni oching.

## Ma’lumotlaringizni o‘zgartirish
`app/config.py` ichida `SEED_GROUP`, `SEED_FACULTY`, `SEED_AGE` (va kerak bo‘lsa `SEED_FULL_NAME`) ni o‘zingiznikiga almashtiring.

## Render.com ga joylashtirish (bepul)
1. Loyihani GitHub'ga yuklang.
2. render.com → New → Web Service → repozitoriyani ulang.
3. Sozlamalar:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Instance Type: Free
4. Environment Variables: `SECRET_KEY` (uzun tasodifiy matn), `HTTPS_ONLY=true`, `PYTHON_VERSION=3.12.8`.
5. Deploy tugagach `https://<nom>.onrender.com` havolasini topshiriqqa ilova qiling.

Eslatma: bepul tarifda sayt 15 daqiqa ishlatilmasa uxlaydi (birinchi ochilish ~1 daqiqa),
SQLite fayli esa qayta ishga tushganda tozalanadi — foydalanuvchi har ishga tushishda qayta yaratiladi.
Doimiy saqlash kerak bo‘lsa, `DATABASE_URL` ga bepul PostgreSQL (masalan, Neon) manzilini kiriting.
