# HRBot - ربات منابع انسانی ایران هورمون

## ساختار پروژه

```
HRBot/
├── ai/
│   ├── __init__.py
│   ├── settings.py      # تنظیمات AI (threshold، model name)
│   ├── model.py         # لود مدل (یک بار اجرا می‌شود)
│   ├── search.py        # جستجوی semantic
│   └── build_index.py   # ساخت FAISS index از faq.db
├── data/
│   ├── documents.pkl    # اسناد FAQ
│   ├── embeddings.npy   # وکتورها
│   └── faiss.index      # ایندکس جستجو
├── project/
│   └── faq_builder.py   # ساخت faq.db از صفر
├── bot.py               # ربات تلگرام
├── faq.db               # دیتابیس سوالات
├── tickets.db           # دیتابیس تیکت‌ها
└── requirements.txt
```

## نصب و راه‌اندازی

```bash
# ۱. نصب کتابخانه‌ها
pip install -r requirements.txt

# ۲. تنظیم توکن
export TOKEN="your_bot_token_here"

# ۳. اجرای ربات
python bot.py
```

## اگر فایل‌های data/ وجود ندارند (از صفر)

```bash
# ابتدا دیتابیس FAQ رو بساز
python -m project.faq_builder

# بعد ایندکس FAISS رو بساز
python -m ai.build_index

# حالا ربات رو اجرا کن
python bot.py
```

## اگر FAQ جدید اضافه کردی

بعد از ویرایش `faq.db`، ایندکس رو rebuild کن:
```bash
python -m ai.build_index
```

## تنظیمات AI

فایل `ai/settings.py`:
- `SIMILARITY_THRESHOLD = 0.50` — حد تشابه برای پاسخ دادن (بالاتر = دقیق‌تر اما کمتر پاسخ)
- `MODEL_NAME` — مدل sentence transformer
