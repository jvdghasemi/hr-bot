import threading
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    MenuButtonCommands,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from datetime import datetime
import pytz
import random
import jdatetime
import asyncio
import os
import logging
import psutil
import sqlite3
import time

# ================== INIT ==================

BOT_START_TIME = time.time()
BOT_VERSION = "2.0.0"
LAST_ERROR = "None"

TOKEN = os.getenv("TOKEN")

ADMIN_IDS = [7186618503, 8040436465, 866732263, 34406542, ]
ADMIN_GROUP_ID = -1004433309113

db_lock = threading.Lock()
conn = sqlite3.connect("tickets.db", check_same_thread=False)
cursor = conn.cursor()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

pending_reply = {}

# ================== منوها ==================

keyboard = [
    ["❓ سوالات پر تکرار", "🌐 شبکه های اجتماعی"],
    ["📝 پیام مدیر عامل", "🤝 فرصت های شغلی"],
    ["🎙️ صدای کارکنان", "📞 تماس‌ با ما"],
]

admin_keyboard = [
    ["❓ سوالات پر تکرار", "🌐 شبکه های اجتماعی"],
    ["📝 پیام مدیر عامل", "🤝 فرصت های شغلی"],
    ["🎙️ صدای کارکنان", "📞 تماس‌ با ما"],
    ["🔧 سلامت ربات"],
]

social_keyboard = ReplyKeyboardMarkup(
    [
        ["📷 اینستاگرام"],
        ["✈️ تلگرام"],
        ["🔵 لینکدین"],
        ["🟢 بله"],
        ["🔙 بازگشت"],
    ],
    resize_keyboard=True,
)

feedback_keyboard = ReplyKeyboardMarkup([["❌ انصراف"]], resize_keyboard=True)

faq_keyboard = ReplyKeyboardMarkup(
    [
        ["📄 قرارداد و استخدام", "📍 حضور و غیاب و تردد", "➕ اضافه کاری"],
        ["🏖 مرخصی", "🛡 انتظامات", "🍽 غذا و پذیرایی"],
        ["💻 فناوری اطلاعات", "💰 تسهیلات رفاهی", "🎓 آموزش"],
        ["🔙 بازگشت"],
    ],
    resize_keyboard=True,
)

user_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
admin_markup = ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True)


def get_markup(user_id):
    return admin_markup if user_id in ADMIN_IDS else user_markup


# ================== HEALTH CHECK ==================


async def health_check():
    global LAST_ERROR
    data = {}

    try:
        ram = psutil.virtual_memory()
        data["ram"] = ram.percent
        data["cpu"] = psutil.cpu_percent()
    except Exception as e:
        LAST_ERROR = str(e)
        data["ram"] = "Unknown"
        data["cpu"] = "Unknown"

    uptime = int(time.time() - BOT_START_TIME)
    days = uptime // 86400
    hours = (uptime % 86400) // 3600
    minutes = (uptime % 3600) // 60

    data["uptime"] = f"{days}d {hours}h {minutes}m"
    data["version"] = BOT_VERSION
    data["error"] = LAST_ERROR

    try:
        cursor.execute("SELECT COUNT(*) FROM tickets")
        data["tickets"] = cursor.fetchone()[0]
    except Exception:
        data["tickets"] = 0

    data["pending"] = len(pending_reply)

    try:
        data["dbsize"] = round(os.path.getsize("tickets.db") / 1024, 2)
    except Exception:
        data["dbsize"] = 0

    data["telegram"] = "🟢 OK"
    data["polling"] = "🟢 Running"

    return data


# ================== BUTTON HANDLER ==================


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        return

    if query.data.startswith("reply_"):
        ticket_id = int(query.data.split("_")[1])

        cursor.execute(
            "SELECT ticket_id FROM tickets WHERE ticket_id=?", (ticket_id,))
        ticket = cursor.fetchone()

        if ticket is None:
            await query.message.reply_text("❌ این تیکت قبلاً بسته شده است.")
            return

        pending_reply[user_id] = ticket_id
        await query.message.reply_text(
            f"✍️ پاسخ به تیکت #{ticket_id}.",
            reply_markup=feedback_keyboard,
        )


# ================== START ==================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonCommands(),
    )

    msg = await update.message.reply_text(
        "👋 سلام\nبه دستیار منابع انسانی ایران هورمون خوش آمدید"
    )
    await asyncio.sleep(1)
    await msg.delete()

    await update.message.reply_text(
        "👇 برای ورود به منو روی دکمه زیر بزن",
        reply_markup=ReplyKeyboardMarkup([["🚀 شروع"]], resize_keyboard=True),
    )


# ================== MAIN HANDLER ==================


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.effective_user.id
    text = update.message.text or ""

    # ── سلامت ربات ──
    if text == "🔧 سلامت ربات":
        data = await health_check()
        message = (
            f"🤖 Health Monitor V2\n\n"
            f"🟢 Telegram\n{data['telegram']}\n\n"
            f"🎫 Tickets\n{data['tickets']}\n\n"
            f"📨 Pending\n{data['pending']}\n\n"
            f"🗄 DB\n{data['dbsize']} KB\n\n"
            f"🧠 RAM\n{data['ram']}%\n\n"
            f"⚙ CPU\n{data['cpu']}%\n\n"
            f"⏳ Uptime\n{data['uptime']}\n\n"
            f"📶 Polling\n{data['polling']}\n\n"
            f"🚀 Version\n{data['version']}\n\n"
            f"❌ Last Error\n{data['error']}"
        )
        await update.message.reply_text(message)
        return

    # ── لغو پاسخ ادمین ──
    if text in ["❌", "❌ انصراف"] and user_id in pending_reply:
        del pending_reply[user_id]
        await update.message.reply_text(
            "❌ پاسخ به تیکت لغو شد.",
            reply_markup=get_markup(user_id),
        )
        return

    # ── پاسخ ادمین به تیکت ──
    if user_id in ADMIN_IDS and user_id in pending_reply:
        if update.message.voice:
            await update.message.reply_text(
                "❌ پاسخ تیکت فقط باید به صورت متنی ارسال شود."
            )
            return

        ticket_id = pending_reply[user_id]
        cursor.execute("SELECT * FROM tickets WHERE ticket_id=?", (ticket_id,))
        ticket = cursor.fetchone()

        if ticket is None:
            await update.message.reply_text("❌ تیکت پیدا نشد.")
            del pending_reply[user_id]
            return

        (_, _, user_chat_id, ticket_name, username, ticket_text,
         voice_id, ticket_date, ticket_time) = ticket

        message = (
            f"👤 {ticket_name}\n"
            f"📅 {ticket_date}\n"
            f"🕒 {ticket_time}\n"
            f"📩 پاسخ به تیکت #{ticket_id}\n\n"
            f"📝 نظر شما:\n\n{ticket_text}\n\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"با سلام\n\n{text}\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"امور اداری و منابع انسانی\n\n"
            f"شرکت داروسازی ایران هورمون"
        )

        try:
            if voice_id:
                await context.bot.send_voice(chat_id=user_chat_id, voice=voice_id)
            await context.bot.send_message(chat_id=user_chat_id, text=message)
        except Exception as e:
            print(f"Send Error: {e}")
            await update.message.reply_text("❌ ارسال پیام به کاربر ناموفق بود.")
            del pending_reply[user_id]
            return

        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=f"✅ تیکت #{ticket_id} پاسخ داده و بسته شد.",
        )

        with db_lock:
            del pending_reply[user_id]
            cursor.execute(
                "DELETE FROM tickets WHERE ticket_id=?", (ticket_id,))
        conn.commit()
        return

    # ── شروع ──
    if text == "🚀 شروع":
        await update.message.reply_text(
            "✅ وارد منو شدی",
            reply_markup=get_markup(user_id),
        )
        return

    # ── صدای کارکنان (ثبت تیکت) ──
    if context.user_data.get("voice_staff"):
        if text == "❌ انصراف":
            context.user_data["voice_staff"] = False
            await update.message.reply_text("❌ لغو شد", reply_markup=get_markup(user_id))
            return

        if not update.message.text and not update.message.voice:
            await update.message.reply_text("❌ فقط متن یا پیام صوتی ارسال کنید.")
            return

        user = update.effective_user
        username = f"@{user.username}" if user.username else "ندارد"

        while True:
            ticket_id = random.randint(100000, 999999)
            cursor.execute(
                "SELECT 1 FROM tickets WHERE ticket_id=?", (ticket_id,))
            if cursor.fetchone() is None:
                break

        tehran = pytz.timezone("Asia/Tehran")
        now = datetime.now(tehran)
        shamsi_date = jdatetime.datetime.fromgregorian(
            datetime=now).strftime("%Y/%m/%d")
        shamsi_time = now.strftime("%H:%M")

        voice_id = update.message.voice.file_id if update.message.voice else None
        ticket_text = text if text else "☝️ پیام صوتی ارسال کردید که بالای همین پیام است."

        with db_lock:
            cursor.execute(
                """
                INSERT INTO tickets
                (ticket_id, user_id, chat_id, name, username, text, voice_id, date, time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ticket_id, user.id, update.effective_chat.id, user.first_name,
                 username, ticket_text, voice_id, shamsi_date, shamsi_time),
            )
            conn.commit()

        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📩 پاسخ به این تیکت",
                                   callback_data=f"reply_{ticket_id}")]]
        )

        info = (
            f"🎙️ تیکت صدای کارکنان #{ticket_id}\n\n"
            f"👤 نام: {user.first_name}\n"
            f"🔹 یوزرنیم: {username}\n"
            f"🆔 آیدی: {user.id}\n\n"
            f"📅 تاریخ: {shamsi_date}\n"
            f"🕒 ساعت: {shamsi_time}"
        )

        if update.message.text:
            await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=info + f"\n💬 پیام:\n{ticket_text}",
                reply_markup=reply_markup,
            )
        elif update.message.voice:
            await context.bot.send_voice(
                chat_id=ADMIN_GROUP_ID,
                voice=update.message.voice.file_id,
                caption=info + "\n\n🎤 پیام صوتی",
                reply_markup=reply_markup,
            )

        await update.message.reply_text(
            f"تیکت شما با کد زیر ثبت شد ✅\n🎫 #{ticket_id}",
            reply_markup=get_markup(user_id),
        )
        context.user_data["voice_staff"] = False
        return

    # ================== منوی اصلی ==================

    if text == "🤝 فرصت های شغلی":
        await update.message.reply_text("کلید 1")
        return

    elif text == "📝 پیام مدیر عامل":
        await update.message.reply_text(
            "📝 پیام مدیرعامل\n\n"
            "سپاس خداوند متعال را که فرصت خدمت در کنار مدیران، متخصصان و کارکنان پرتلاش شرکت داروسازی ایران هورمون را برای اینجانب فراهم ساخت. حضور در مجموعه‌ای باسابقه، معتبر و اثرگذار در صنعت داروسازی کشور را افتخاری بزرگ و در عین حال مسئولیتی سنگین می‌دانم.\n\n"
            "شرکت داروسازی ایران هورمون طی سال‌ها فعالیت، با اتکا به دانش تخصصی، تعهد حرفه‌ای و تلاش سرمایه انسانی ارزشمند خود، جایگاهی ممتاز در صنعت دارویی کشور به دست آورده است. حفظ و ارتقای این جایگاه، مستلزم نگاه آینده‌نگر، برنامه‌ریزی علمی و بهره‌گیری از ظرفیت‌های ارزشمند موجود در سازمان است.\n\n"
            "افزون بر این، ایران هورمون به‌عنوان یکی از شرکت‌های پیشرو در حوزه تولید داروهای تخصصی، همواره نقش مهمی در تأمین نیازهای درمانی کشور ایفا کرده است. در این مسیر، توسعه سبد محصولات تخصصی و توجه ویژه به تولید داروهای هازارد، به‌عنوان یکی از حوزه‌های مهم فعالیت شرکت، در زمره اولویت‌های اصلی مدیریت قرار خواهد داشت.\n\n"
            "در کنار توسعه محصولات، ارتقای مستمر کیفیت و تولید بر اساس بالاترین استانداردهای بین‌المللی و الزامات GMP، از اصول بنیادین فعالیت شرکت خواهد بود. باور داریم کیفیت، ایمنی و اثربخشی محصولات، مهم‌ترین تعهد ما در قبال بیماران، جامعه پزشکی و نظام سلامت کشور است و حفظ این استانداردها، ضامن تداوم اعتماد ذی‌نفعان به برند ایران هورمون خواهد بود.\n\n"
            "همچنین معتقدیم توسعه بازار و ارتقای جایگاه برند ایران هورمون، تنها از مسیر بازاریابی علمی و معرفی دقیق محصولات بر پایه مستندات، رفرنس‌ها و شواهد معتبر پزشکی امکان‌پذیر است. از این رو، تعامل سازنده با جامعه پزشکی، داروسازان، مراکز درمانی و سایر ذی‌نفعان صنعت سلامت، با رویکردی علمی و مبتنی بر دانش روز، بیش از پیش مورد توجه قرار خواهد گرفت.\n\n"
            "شنیدن صدای مشتریان، پزشکان و شرکای تجاری و بهره‌گیری از دیدگاه‌ها و بازخوردهای آنان را یکی از ارکان مهم بهبود مستمر می‌دانیم. اعتقاد داریم موفقیت پایدار زمانی حاصل می‌شود که سازمان بتواند نیازها و انتظارات ذی‌نفعان خود را به‌درستی درک کرده و در مسیر پاسخگویی مؤثر به آن‌ها گام بردارد.\n\n"
            "امیدوارم با همراهی اعضای هیئت‌مدیره، تلاش همکاران گرانقدر و همکاری ارزشمند شرکای تجاری، بتوانیم در مسیر رشد، نوآوری و توسعه پایدار شرکت گام‌های مؤثری برداریم و آینده‌ای درخور نام و اعتبار ایران هورمون رقم بزنیم.\n\n"
            "دکتر عبدالرضا ظاهر طبری\n\n"
            "مدیرعامل شرکت داروسازی ایران هورمون"
        )
        return

    elif text == "🌐 شبکه های اجتماعی":
        await update.message.reply_text("یکی رو انتخاب کن:", reply_markup=social_keyboard)
        return

    elif text == "📷 اینستاگرام":
        await update.message.reply_text("https://instagram.com/iranhormone")
        return

    elif text == "✈️ تلگرام":
        await update.message.reply_text("https://t.me/irhormon")
        return

    elif text == "🔵 لینکدین":
        await update.message.reply_text(
            "https://linkedin.com/company/iranhormonepharmaceuticalcompany/"
        )
        return

    elif text == "🟢 بله":
        await update.message.reply_text("https://ble.ir/iranhormon")
        return

    elif text == "🔙 بازگشت":
        await update.message.reply_text("برگشت به منو", reply_markup=get_markup(user_id))
        return

    elif text == "📞 تماس‌ با ما":
        await update.message.reply_text(
            "📞 راه های ارتباطی شرکت داروسازی ایران هورمون\n\n"
            "🌐 وب‌سایت:\nhttps://www.iranhormone.ir\n\n"
            "📧 پست الکترونیک:\ninfo@iranhormone.com\n\n"
            "☎️ تلفن:\n02144905517\n\n"
            "📍 آدرس:\n\nتهران، کیلومتر ۱۱ جاده مخصوص کرج، شرکت داروسازی ایران هورمون\n\n"
            "👇 نمایش مکان در نشان\n https://nshn.ir/1a_bvHRNPxjnFM\n\n"
            "📮 کد پستی:\n1399813611"
        )
        return

    elif text == "🎙️ صدای کارکنان":
        context.user_data["voice_staff"] = True
        await update.message.reply_text(
            "🎤 نظر خود را ارسال کنید.\nبرای لغو روی «❌ انصراف» بزنید.",
            reply_markup=feedback_keyboard,
        )
        return

    elif text == "❓ سوالات پر تکرار":
        await update.message.reply_text(
            "یکی از موارد زیر را انتخاب کنید:",
            reply_markup=faq_keyboard,
        )
        return

    # ================== سوالات پر تکرار ==================

    elif text == "📄 قرارداد و استخدام":
        await update.message.reply_text(
            "📄 قرارداد و استخدام\n\n"
            "❓ سوال:\nشرایط قرارداد استخدامی در شرکت چگونه است؟\n\n"
            "✅ پاسخ:\n"
            "استخدام در شرکت ایران هورمون با یک ماه دوره آزمایشی آغاز می‌شود. سپس بر اساس نتایج ارزیابی عملکرد، قرارداد به‌ترتیب در دوره‌های ۳ ماهه، دو دوره ۶ ماهه و در صورت تأیید مدیر واحد، یک‌ساله منعقد می‌شود.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nدر صورت استعفاء، چه زمانی باید موضوع را اعلام کنم؟\n\n"
            "✅ پاسخ:\n"
            "در صورت تمایل به قطع همکاری، باید حداقل یک ماه قبل، درخواست خود را به‌صورت کتبی به مدیر واحد اعلام کنید."
        )
        return

    elif text == "📍 حضور و غیاب و تردد":
        await update.message.reply_text(
            "📍 حضور و غیاب و تردد\n\n"
            "❓ سوال:\nمیزان تأخیر و تعجیل مجاز چقدر است؟\n\n"
            "✅ پاسخ:\nروزانه تا ۱۵ دقیقه تأخیر در ورود و ۵ دقیقه تعجیل در خروج مجاز است.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nاگر اثر انگشت در دستگاه تردد ثبت نشود، چه باید کرد؟\n\n"
            "✅ پاسخ:\nموضوع را به انتظامات اطلاع دهید تا تردد شما ثبت و برای پیگیری به کارگزینی ارسال شود."
        )
        return

    elif text == "➕ اضافه کاری":
        await update.message.reply_text(
            "➕ اضافه کاری\n\n"
            "❓ سوال:\nساعات اضافه‌کاری شرکت چگونه است؟\n\n"
            "✅ پاسخ:\n"
            "۱۵:۳۰ تا ۱۸:۳۰\n"
            "۱۵:۳۰ تا ۲۱:۳۰\n"
            "۱۵:۳۰ تا ۰۲:۰۰\n"
            "۱۵:۳۰ تا ۰۶:۳۰\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nتا چه زمانی باید درخواست اضافه‌کاری را ثبت کنم؟\n\n"
            "✅ پاسخ:\n"
            "درخواست اضافه‌کاری روزهای عادی باید حداکثر تا ساعت ۱۵ همان روز در سامانه کسرا ثبت شود. برای پنج‌شنبه و جمعه نیز ثبت درخواست تا ساعت ۱۲ روز چهارشنبه امکان‌پذیر است.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nاگر اضافه‌کاری ثبت نشده باشد، چه باید کرد؟\n\n"
            "✅ پاسخ:\n"
            "در صورت حضور کارکنان به درخواست مدیر واحد و عدم ثبت اضافه‌کاری تا ساعت ۱۵، مدیر واحد می‌تواند مجوز اضافه‌کاری را در سامانه ثبت کند."
        )
        return

    elif text == "🏖 مرخصی":
        await update.message.reply_text(
            "🏖 مرخصی\n\n"
            "❓ سوال:\nمیزان مرخصی استحقاقی سالانه چقدر است؟\n\n"
            "✅ پاسخ:\n"
            "مرخصی استحقاقی سالانه با احتساب ۴ روز جمعه، یک ماه است. "
            "برای کارکنانی که کمتر از یک سال سابقه دارند، مرخصی متناسب با مدت حضور محاسبه می‌شود.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nمرخصی را تا چه زمانی باید ثبت کنم؟\n\n"
            "✅ پاسخ:\n"
            "در شرایط خاص، حداکثر تا یک روز پس از پایان مرخصی امکان ثبت درخواست وجود دارد. "
            "عدم ثبت مرخصی به‌عنوان غیبت محسوب می‌شود.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nسقف مرخصی ساعتی در روز چقدر است؟\n\n"
            "✅ پاسخ:\nحداکثر ۴ ساعت در روز."
        )
        return

    elif text == "🛡 انتظامات":
        await update.message.reply_text(
            "🛡 انتظامات\n\n"
            "❓ سوال:\nآیا شرکت پارکینگ دارد؟\n\n"
            "✅ پاسخ:\n"
            "تعداد محدودی جای پارک در خیابان مجاور شرکت در نظر گرفته شده است. "
            "برای رؤسا و داروسازان تا ساعت ۷:۳۰ جای پارک حفظ می‌شود.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nسرویس‌های ایاب و ذهاب شرکت چه ساعتی حرکت می‌کنند؟\n\n"
            "✅ پاسخ:\n"
            "سرویس‌های شرکت در ساعت‌های ۱۵:۳۰ و ۱۸:۳۰ حرکت می‌کنند. "
            "کارکنان باید ۵ دقیقه پیش از حرکت سرویس در محل حاضر باشند و پس از ثبت خروج در دستگاه تردد سوار سرویس شوند.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nآیا بسته پستی و خرید اینترنتی توسط انتظامات تحویل گرفته می‌شود؟\n\n"
            "✅ پاسخ:\n"
            "بله، بسته‌های پستی و خریدهای اینترنتی توسط انتظامات تحویل گرفته شده و به دبیرخانه شرکت تحویل داده می‌شود."
        )
        return

    elif text == "🍽 غذا و پذیرایی":
        await update.message.reply_text(
            "🍽 غذا و پذیرایی\n\n"
            "❓ سوال:\nرزرو غذا چگونه انجام می‌شود؟\n\n"
            "✅ پاسخ:\n"
            "منوی ماهانه غذا در سامانه کسرا بارگذاری می‌شود و کارکنان یک هفته فرصت دارند غذای موردنظر خود را انتخاب کنند.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nساعات پذیرایی چای و عصرانه چگونه است؟\n\n"
            "✅ پاسخ:\n"
            "چای صبح کارکنان اداری: ساعت ۸:۰۰\n"
            "چای صبح کارکنان اداری و تولید: ساعت ۱۰:۰۰\n"
            "چای عصر کارکنان اداری: ساعت ۱۴:۰۰\n"
            "چای عصر کارکنان اداری و تولید: ساعت ۱۶:۰۰\n"
            "عصرانه کارکنان دارای اضافه‌کاری: ساعت ۱۶:۳۰"
        )
        return

    elif text == "💻 فناوری اطلاعات" in text:
        await update.message.reply_text(
            "💻 فناوری اطلاعات\n\n"
            "❓ سوال:\nآیا در استفاده شخصی، از امکانات نرم افزاری و سخت افزاری شرکت، محدودیتی وجود دارد؟\n\n"
            "✅ پاسخ:\n"
            "امکانات نرم افزاری و سخت افزاری ارائه شده به کارکنان، صرفا جهت انجام امور مربوط به سازمان بوده و هرگونه استفاده شخصی ممنوع می باشد.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nقصد نصب نرم افزاری را بر روی کامپیوتر خود دارم اما نصب نمی شود، علت آن چیست؟\n\n"
            "✅ پاسخ:\n"
            "نصب / حذف / بروزرسانی نرم افزار ها و سخت افزار ها بر روی کلیه رایانه ها بر عهده واحد ICT بوده و کلیه پرسنل جهت انجام این موارد با هماهنگی واحد ICT و از طریق فرم درخواست کار از واحد ICT با کد مدرک FRM/IT-01/02 و همچنین تایید مدیران مربوطه واحد مجاز به انجام آن خواهند بود. کاربران مجوز تغییر در تنظیمات شبکه ای ، کاربری و نرم افزاری را بر روی سیستم رایانه خود و همکاران خود را ندارند.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nچگونه عکس های شخصی ام را از طریق گوشی موبایل به کامپیوتر انتقال دهم ؟\n\n"
            "✅ پاسخ:\n"
            "ثبت، ذخیره و نگهداری اطلاعات شخصی (عکس، فیلم، موزیک و .....) غیر سازمانی بر روی کلیه رایانه های داخل سازمان ممنوع می باشد.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nتمامی اطلاعات موجود بر روی دسک تاپم پاک شده اند، چگونه آنها را برگردانم؟\n\n"
            "✅ پاسخ:\n"
            "مسئولیت نگهداری از اطلاعات سازمانی موجود در رایانه کاربران بر عهده شخص کاربر می باشد. همچنین به جهت بالارفتن امنیت اطلاعات در زمان خرابی رایانه ها از قرار دادن اطلاعات در درایو C، MyDocument و Desktop خودداری فرمایید و اطلاعات مهم را در سایر درایو ها کپی و در پایان هر ماه از آنها پشتیبان با تاریخ مشخص تهیه فرمایید. جهت تهیه پشتیبان، می بایست یک نسخه از اطلاعات بک آپ گرفته شده را در فولدر Share واحد خود کپی نمایید.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nآیا در روزهایی که همکارم در شرکت حضور ندارد و یا در حال استفاده از سیستم نمی باشد، می توانم از کامپیوتر او استفاده کنم؟\n\n"
            "✅ پاسخ:\n"
            "کاربران اجازه استفاده از رایانه دیگر همکاران را ندارند مگر با اجازه مدیر واحد مربوطه.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nچگونه فایل شخصی ام را به کامپیوتر ارسال و پرینت بگیرم؟\n\n"
            "✅ پاسخ:\n"
            "کاربران، ضمن صرفه جویی در مصرف کاغذ، تنها مجاز به چاپ اطلاعات در حیطه اطلاعات سازمانی می باشند و به هیچ عنوان اجازه چاپ اطلاعات شخصی را ندارند.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nآیا می توانم اطلاعات نام کاربری و پسورد سیستم های اتوماسیون، رایورز و کسری را در اختیار همکارم قرار دهم تا در غیاب من پیگیری های لازم را انجام دهد؟\n\n"
            "✅ پاسخ:\n"
            "کاربران مسئول حفاظت از شناسه کاربری و رمز عبورشان هستند و از این شناسه می بایست در حدود اختیار داده شده استفاده نمایند و در صورت تغییر رمز به مقام بالاتر واحد اطلاع و آن را در اختیار ایشان قرار دهند. همچنین کاربر در برابر شناسه کاربری و رمز ایمیل سازمانی قرار داده شده در اختیارش مسئول است و باید در فواصل زمانی مشخص نسبت به تغییر رمز ایمیل به صورت ترکیبی از کاراکترهای بزرگ و کوچک و اعداد اقدام نماید.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nایمیل سازمانی که در اختیارم قرار داده بودید، اطلاعاتش را نمی توانم پیدا کنم، چگونه آنها را بازیابی کنم؟\n\n"
            "✅ پاسخ:\n"
            "مسئولیت حفظ اطلاعات ایمیل بر عهده کاربر بوده و کاربر باید از اطلاعات مهم (نامه ها و پیوست ها) ایمیل سازمانی قرار داده شده در اختیارش پشتیبان تهیه نمایند.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nچرا فلش و گوشی موبایلم در کامپیوتر های سازمان باز نمی شوند؟\n\n"
            "✅ پاسخ:\n"
            "کاربران مجاز به استفاده از فلش، هارد اکسترنال و ... شخصی بر روی هیچ کدام از کامپیوتر های سازمان نبوده و جهت انتقال اطلاعات سازمانی می بایست با استفاده از فلش های سازمانی که در اختیار مدیران می باشد و با اخذ مجوز از مدیر واحد اقدام نمایند.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nآیا جهت ورود و خروج لپ تاپ و غیره به داخل سازمان، تایید مدیر واحد ICT نیاز می باشد؟\n\n"
            "✅ پاسخ:\n"
            "ورود و خروج هر گونه کامپیوتر، لپ تاپ، تبلت و یا هرگونه وسایل ذخیره سازی اطلاعات در شرکت ممنوع می باشد و در موارد خاص تنها از طریق هماهنگی لازم با واحد ICT و تایید مدیر واحد ICT امکان پذیر می باشد.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nآیا جهت استفاده از شبکه های اجتماعی، پیام رسان ها و مودم های شخصی در شرکت محدودیت خاصی وجود دارد؟\n\n"
            "✅ پاسخ:\n"
            "استفاده از نرم افزارهای تلگرام، واتس آپ، بله، روبیکا و ... و همچنین VPN در شرکت اکیدا ممنوع می باشد و در موارد خاص با درخواست مدیر واحد و تایید مدیریت محترم عامل امکان پذیر می باشد. همچنین استفاده از هرگونه تجهیزاتی مانند مودم، هر نوع تجهیز share کننده و پخش اینترنت شخصی و .... در سازمان ممنوع می باشد.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nآیا در استفاده از ایمیل محدودیتی وجود دارد؟\n\n"
            "✅ پاسخ:\n"
            "بله، در صورت دریافت ایمیل های مشکوک از باز نمودن آن خودداری نموده و واحد ICT را مطلع نمایید. همچنین کاربران مجاز به استفاده از ایمیل شرکت برای ثبت نام در سایت های اینترنتی یا امور شخصی نمی باشند.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\nآیا در ارسال و دریافت فایل ها محدودیتی وجود دارد؟\n\n"
            "✅ پاسخ:\n"
            "بله، ارسال و دریافت فایل های اجرایی با فرمت MS، BAT و EXE و فرمت های مرسوم اجرایی دیگر ممنوع می باشد و جهت ارسال آن می بایست با اطلاع و نظارت واحد ICT انجام پذیرد."
        )
        return

    elif text == "💰 تسهیلات رفاهی":
        await update.message.reply_text(
            "💰 تسهیلات رفاهی\n\n"
            "❓ سوال:\nشرایط دریافت وام صندوق تعاون چیست؟\n\n"
            "✅ پاسخ:\n"
            "برای عضویت در صندوق تعاون، درخواست خود را از طریق نامه به مدیر مالی ارائه کنید. "
            "ماهانه ۴ درصد از حقوق و مزایای پرسنل کسر و به صندوق واریز می‌شود. "
            "پس از یک سال عضویت، می‌توانید درخواست وام خود را از طریق فرم مربوطه به دبیرخانه ارسال کنید.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nوام صندوق کارگشایی چیست و چگونه دریافت می‌شود؟\n\n"
            "✅ پاسخ:\n"
            "کارکنان پس از یک سال از تاریخ شروع به کار می‌توانند با تکمیل فرم درخواست وام، "
            "تقاضای خود را به دبیرخانه ارائه کنند.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nاز چه زمانی امکان دریافت وام وجود دارد؟\n\n"
            "✅ پاسخ:\nامکان استفاده از تسهیلات وام پس از یک سال حضور در شرکت فراهم می‌شود.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "❓ سوال:\nبرای دریافت اقلام رفاهی به چند ماه سابقه کار در شرکت نیاز است؟\n\n"
            "✅ پاسخ:\nداشتن سه ماه سابقه کار در شرکت جهت دریافت اقلام رفاهی الزامی می‌باشد."
        )
        return

    elif text == "🎓 آموزش":
        await update.message.reply_text("سوالات و پاسخ های بخش آموزش به زودی اضافه خواهد شد...")
        return

    else:
        await update.message.reply_text(
            "❌ سوال شما در پایگاه داده یافت نشد.\n\n"
            "لطفا از منو انتخاب کنید یا سوال خود را واضح‌ تر بنویسید."
        )


# ================== MAIN ==================


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()
