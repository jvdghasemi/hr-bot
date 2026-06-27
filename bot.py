from time import time
from datetime import datetime
from rapidfuzz import fuzz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import conn, cursor
from telegram.ext import CallbackQueryHandler
import pytz
import random
import jdatetime
import asyncio
import os
import logging
import traceback
import sqlite3
import psutil

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    MenuButtonCommands
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

logging.basicConfig(

    level=logging.INFO,

    format='%(asctime)s - %(message)s'

)

TOKEN = os.getenv("TOKEN")
ADMIN_IDS = [
    7186618503, 8040436465,
]

ADMIN_GROUP_ID = -1004433309113

BOT_START_TIME = time()

BOT_VERSION = "2.0.0"

LAST_ERROR = "None"


# ================== منوها ==================
keyboard = [
    ["❓ سوالات پر تکرار", "🌐 شبکه های اجتماعی"],
    ["📝 پیام مدیر عامل", "🤝 فرصت های شغلی"],
    ["🎙️ صدای کارکنان", "📞 تماس‌ با ما"]
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
        ["🔙 بازگشت"]
    ],
    resize_keyboard=True
)

feedback_keyboard = ReplyKeyboardMarkup(
    [["❌ انصراف"]],
    resize_keyboard=True
)

faq_keyboard = ReplyKeyboardMarkup(
    [
        ["📄 قرارداد و استخدام", "📍 حضور و غیاب و تردد", "➕ اضافه کاری"],
        ["🏖 مرخصی", "🛡 انتظامات", "🍽 غذا و پذیرایی"],
        ["💻 فناوری اطلاعات", "💰 تسهیلات رفاهی", "🎓 آموزش"],
        ["🔙 بازگشت"]
    ],
    resize_keyboard=True
)


user_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
admin_markup = ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True)


def get_markup(user_id):
    return admin_markup if user_id in ADMIN_IDS else user_markup


pending_reply = {}


def ai_faq(text):
    text = text.lower()

    intents = [
        {
            "key": "سرویس",
            "keywords": [
                "سرویس",
                "ایاب ذهاب",
                "رفت و آمد",
                "اتوبوس",
                "شرکت سرویس",
                "چطور میریم شرکت"
            ],
            "answer": "🛡 انتظامات"
        },
        {
            "key": "وام",
            "keywords": [
                "وام",
                "وام میدن",
                "تسهیلات",
                "صندوق",
                "کارگشایی",
                "پول قرض"
            ],
            "answer": "💰 تسهیلات رفاهی"
        },
        {
            "key": "پارکینگ",
            "keywords": [
                "پارکینگ",
                "جای پارک",
                "ماشین کجا بذارم",
                "پارک خودرو"
            ],
            "answer": "🛡 انتظامات"
        },
        {
            "key": "مرخصی",
            "keywords": [
                "مرخصی",
                "استراحت",
                "چند روز مرخصی",
                "مرخصی ساعتی",
                "غیبت"
            ],
            "answer": "🏖 مرخصی"
        }
    ]

    best_score = 0
    best_answer = None

    for intent in intents:
        for kw in intent["keywords"]:
            score = fuzz.partial_ratio(text, kw.lower())

            if score > best_score:
                best_score = score
                best_answer = intent["answer"]

    if best_score >= 70:
        return best_answer

    return None


async def health_check():
    global LAST_ERROR

    data = {}

    # ================= RAM / CPU =================
    try:
        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent()

        data["ram"] = ram.percent
        data["cpu"] = cpu

    except Exception as e:
        LAST_ERROR = str(e)
        data["ram"] = "Unknown"
        data["cpu"] = "Unknown"

    # ================= UPTIME =================
    uptime = int(time() - BOT_START_TIME)

    days = uptime // 86400
    hours = (uptime % 86400) // 3600
    minutes = (uptime % 3600) // 60

    data["uptime"] = f"{days}d {hours}h {minutes}m"
    data["version"] = BOT_VERSION
    data["error"] = LAST_ERROR

    # ================= SQLITE =================
    try:
        cursor.execute("SELECT COUNT(*) FROM tickets")
        data["tickets"] = cursor.fetchone()[0]
    except:
        data["tickets"] = 0

    # ================= PENDING =================
    data["pending"] = len(pending_reply)

    # ================= DB SIZE =================
    try:
        size = os.path.getsize("tickets.db")
        data["dbsize"] = round(size / 1024, 2)
    except:
        data["dbsize"] = 0

    # ================= TELEGRAM =================
    data["telegram"] = "🟢 OK"

    # ================= POLLING =================
    data["polling"] = "🟢 Running"

    return data


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        return

    if query.data.startswith("reply_"):
        ticket_id = int(query.data.split("_")[1])

        cursor.execute(
            "SELECT ticket_id FROM tickets WHERE ticket_id=?",
            (ticket_id,)
        )

        ticket = cursor.fetchone()

        if ticket is None:
            await query.message.reply_text(
                "❌ این تیکت قبلاً بسته شده است."
            )
            return

        pending_reply[user_id] = ticket_id

        await query.message.reply_text(
            f"✍️ پاسخ به تیکت #{ticket_id}.",
            reply_markup=feedback_keyboard
        )


# ================== START ==================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonCommands()
    )

    msg = await update.message.reply_text(
        "👋 سلام\nبه دستیار منابع انسانی ایران هورمون خوش آمدید"
    )

    await asyncio.sleep(1)

    await msg.delete()

    await update.message.reply_text(
        "👇 برای ورود به منو روی دکمه زیر بزن",
        reply_markup=ReplyKeyboardMarkup(
            [["🚀 شروع"]],
            resize_keyboard=True
        )
    )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user_id = update.effective_user.id
    text = update.message.text

    faq_text = ai_faq(text)

    if faq_text:
        await update.message.reply_text(faq_text)
    else:
        await update.message.reply_text("❌ اطلاعاتی برای این بخش پیدا نشد.")

        return

    if text == "🔧 سلامت ربات":

        data = await health_check()

        message = f"""
    🤖 Health Monitor V2

    🟢 Telegram
    {data['telegram']}

    🎫 Tickets
    {data['tickets']}

    📨 Pending
    {data['pending']}

    🗄 DB
    {data['dbsize']} KB

    🧠 RAM
    {data['ram']}%

    ⚙ CPU
    {data['cpu']}%

    ⏳ Uptime
    {data['uptime']}

    📶 Polling
    {data['polling']}

    🚀 Version
    {data['version']}

    ❌ Last Error
    {data['error']}
    """

        await update.message.reply_text(message)
        return

    # ================== ADMIN REPLY SYSTEM ==================
    if text in ["❌", "❌ انصراف"] and user_id in pending_reply:

        del pending_reply[user_id]

        await update.message.reply_text(
            "❌ پاسخ به تیکت لغو شد.",
            reply_markup=get_markup(user_id)
        )

        return

    if user_id in ADMIN_IDS and user_id in pending_reply:

        if update.message.voice:
            await update.message.reply_text(
                "❌ پاسخ تیکت فقط باید به صورت متنی ارسال شود."
            )
            return

        ticket_id = pending_reply[user_id]

        cursor.execute("""
        SELECT *
        FROM tickets
        WHERE ticket_id=?
        """, (ticket_id,))

        ticket = cursor.fetchone()

        if ticket is None:
            await update.message.reply_text(
                "❌ تیکت پیدا نشد."
            )

            del pending_reply[user_id]
            return

        (
            _,
            _,
            user_chat_id,
            ticket_name,
            username,
            ticket_text,
            voice_id,
            ticket_date,
            ticket_time
        ) = ticket

        message = (

            f"👤 {ticket_name}\n"
            f"📅 {ticket_date}\n"
            f"🕒 {ticket_time}\n"

            f"📩 پاسخ به تیکت #{ticket_id}\n\n"

            f"📝 نظر شما:\n\n"
            f"{ticket_text}\n\n"

            f"━━━━━━━━━━━━━━\n\n"

            f"با سلام\n\n"
            f"{text}\n\n"

            f"━━━━━━━━━━━━━━\n"
            f"امور اداری و منابع انسانی\n\n"
            f"شرکت داروسازی ایران هورمون"
        )

        try:

            if voice_id:
                await context.bot.send_voice(
                    chat_id=user_chat_id,
                    voice=voice_id
                )

            await context.bot.send_message(
                chat_id=user_chat_id,
                text=message
            )

        except Exception as e:
            print(f"Send Error: {e}")

            await update.message.reply_text(
                "❌ ارسال پیام به کاربر ناموفق بود."
            )
            del pending_reply[user_id]
            return

        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=f"✅ تیکت #{ticket_id} پاسخ داده و بسته شد."
        )

        del pending_reply[user_id]
        cursor.execute(
            "DELETE FROM tickets WHERE ticket_id=?",
            (ticket_id,)
        )

        conn.commit()

        return

    # ---------- ورود ----------
    if text == "🚀 شروع":
        await update.message.reply_text(
            "✅ وارد منو شدی",
            reply_markup=get_markup(user_id)
        )
        return


# ticket
    if context.user_data.get("voice_staff"):
        if text == "❌ انصراف":
            context.user_data["voice_staff"] = False
            await update.message.reply_text("❌ لغو شد", reply_markup=get_markup(user_id))
            return

        if not update.message.text and not update.message.voice:
            await update.message.reply_text(
                "❌ فقط متن یا پیام صوتی ارسال کنید."
            )
            return

        user = update.effective_user
        username = f"@{user.username}" if user.username else "ندارد"

        while True:

            ticket_id = random.randint(100000, 999999)

            cursor.execute(
                "SELECT 1 FROM tickets WHERE ticket_id=?",
                (ticket_id,)
            )

            if cursor.fetchone() is None:
                break

        tehran = pytz.timezone("Asia/Tehran")

        now = datetime.now(tehran)

        shamsi_date = jdatetime.datetime.fromgregorian(
            datetime=now
        ).strftime("%Y/%m/%d")

        shamsi_time = now.strftime("%H:%M")

        voice_id = update.message.voice.file_id if update.message.voice else None
        ticket_text = text if text else "☝️ پیام صوتی ارسال کردید که بالای همین پیام است."

        cursor.execute("""
        INSERT INTO tickets
        (
            ticket_id,
            user_id,
            chat_id,
            name,
            username,
            text,
            voice_id,
            date,
            time
        )
                       
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            ticket_id,
            user.id,
            update.effective_chat.id,

            user.first_name,
            username,

            ticket_text,
            voice_id,

            shamsi_date,
            shamsi_time

        ))

        conn.commit()

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📩 پاسخ به این تیکت",
                        callback_data=f"reply_{ticket_id}"
                    )
                ]
            ]
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

                reply_markup=keyboard

            )

        elif update.message.voice:

            await context.bot.send_voice(

                chat_id=ADMIN_GROUP_ID,

                voice=update.message.voice.file_id,

                caption=info + "\n\n🎤 پیام صوتی",

                reply_markup=keyboard

            )

        await update.message.reply_text(
            f"تیکت شما با کد زیر ثبت شد ✅\n🎫 #{ticket_id}",
            reply_markup=get_markup(user_id)
        )

        context.user_data["voice_staff"] = False
        return

    # ================== MAIN MENU ==================
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
        await update.message.reply_text(
            "برگشتی به منو",
            reply_markup=get_markup(user_id)
        )
        return

    elif text == "📞 تماس‌ با ما":
        await update.message.reply_text(
            "📞 راه های ارتباطی شرکت داروسازی ایران هورمون\n\n"

            "🌐 وب‌سایت:\n"
            "https://www.iranhormone.ir\n\n"

            "📧 پست الکترونیک:\n"
            "info@iranhormone.com\n\n"

            "☎️ تلفن:\n"
            "02144905517\n\n"

            "📍 آدرس:\n\n"
            "تهران، کیلومتر ۱۱ جاده مخصوص کرج، شرکت داروسازی ایران هورمون\n\n"

            "👇 نمایش مکان در نشان\n"
            " https://nshn.ir/1a_bvHRNPxjnFM\n\n"

            "📮 کد پستی:\n"
            "1399813611"
        )
        return

    elif text == "🎙️ صدای کارکنان":
        context.user_data["voice_staff"] = True

        await update.message.reply_text(
            "🎤 نظر خود را ارسال کنید.\nبرای لغو روی «❌ انصراف» بزنید.",
            reply_markup=feedback_keyboard
        )

        return

    elif text == "❓ سوالات پر تکرار":
        await update.message.reply_text(
            "یکی از موارد زیر را انتخاب کنید:",
            reply_markup=faq_keyboard
        )
        return

    elif text == "📄 قرارداد و استخدام":
        await update.message.reply_text(

            "📄 قرارداد و استخدام\n\n"

            "❓ سوال:\n"
            "شرایط قرارداد استخدامی در شرکت چگونه است؟\n\n"

            "✅ پاسخ:\n"
            "استخدام در شرکت ایران هورمون با یک ماه دوره آزمایشی آغاز می‌شود. سپس بر اساس نتایج ارزیابی عملکرد، قرارداد به‌ترتیب در دوره‌های ۳ ماهه، دو دوره ۶ ماهه و در صورت تأیید مدیر واحد، یک‌ساله منعقد می‌شود.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "در صورت استعفاء، چه زمانی باید موضوع را اعلام کنم؟\n\n"

            "✅ پاسخ:\n"
            "در صورت تمایل به قطع همکاری، باید حداقل یک ماه قبل، درخواست خود را به‌صورت کتبی به مدیر واحد اعلام کنید."

        )
    elif text == "📍 حضور و غیاب و تردد":
        await update.message.reply_text(

            "📍 حضور و غیاب و تردد\n\n"

            "❓ سوال:\n"
            "میزان تأخیر و تعجیل مجاز چقدر است؟\n\n"

            "✅ پاسخ:\n"
            "روزانه تا ۱۵ دقیقه تأخیر در ورود و ۵ دقیقه تعجیل در خروج مجاز است.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "اگر اثر انگشت در دستگاه تردد ثبت نشود، چه باید کرد؟\n\n"

            "✅ پاسخ:\n"
            "موضوع را به انتظامات اطلاع دهید تا تردد شما ثبت و برای پیگیری به کارگزینی ارسال شود."

        )
    elif text == "➕ اضافه کاری":
        await update.message.reply_text(

            "➕ اضافه کاری\n\n"

            "❓ سوال:\n"
            "ساعات اضافه‌کاری شرکت چگونه است؟\n\n"

            "✅ پاسخ:\n"
            "۱۵:۳۰ تا ۱۸:۳۰\n"
            "۱۵:۳۰ تا ۲۱:۳۰\n"
            "۱۵:۳۰ تا ۰۲:۰۰\n"
            "۱۵:۳۰ تا ۰۶:۳۰\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "تا چه زمانی باید درخواست اضافه‌کاری را ثبت کنم؟\n\n"

            "✅ پاسخ:\n"
            "درخواست اضافه‌کاری روزهای عادی باید حداکثر تا ساعت ۱۵ همان روز در سامانه کسرا ثبت شود. برای پنج‌شنبه و جمعه نیز ثبت درخواست تا ساعت ۱۲ روز چهارشنبه امکان‌پذیر است.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "اگر اضافه‌کاری ثبت نشده باشد، چه باید کرد؟\n\n"

            "✅ پاسخ:\n"
            "در صورت حضور کارکنان به درخواست مدیر واحد و عدم ثبت اضافه‌کاری تا ساعت ۱۵، مدیر واحد می‌تواند مجوز اضافه‌کاری را در سامانه ثبت کند."

        )
    elif text == "🏖 مرخصی":
        await update.message.reply_text(

            "🏖 مرخصی\n\n"

            "❓ سوال:\n"
            "میزان مرخصی استحقاقی سالانه چقدر است؟\n\n"

            "✅ پاسخ:\n"
            "مرخصی استحقاقی سالانه با احتساب ۴ روز جمعه، یک ماه است. "
            "برای کارکنانی که کمتر از یک سال سابقه دارند، مرخصی متناسب با مدت حضور محاسبه می‌شود.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "مرخصی را تا چه زمانی باید ثبت کنم؟\n\n"

            "✅ پاسخ:\n"
            "در شرایط خاص، حداکثر تا یک روز پس از پایان مرخصی امکان ثبت درخواست وجود دارد. "
            "عدم ثبت مرخصی به‌عنوان غیبت محسوب می‌شود.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "سقف مرخصی ساعتی در روز چقدر است؟\n\n"

            "✅ پاسخ:\n"
            "حداکثر ۴ ساعت در روز."

        )
    elif text == "🛡 انتظامات":
        await update.message.reply_text(

            "🛡 انتظامات\n\n"

            "❓ سوال:\n"
            "آیا شرکت پارکینگ دارد؟\n\n"

            "✅ پاسخ:\n"
            "تعداد محدودی جای پارک در خیابان مجاور شرکت در نظر گرفته شده است. "
            "برای رؤسا و داروسازان تا ساعت ۷:۳۰ جای پارک حفظ می‌شود.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "سرویس‌های ایاب و ذهاب شرکت چه ساعتی حرکت می‌کنند؟\n\n"

            "✅ پاسخ:\n"
            "سرویس‌های شرکت در ساعت‌های ۱۵:۳۰ و ۱۸:۳۰ حرکت می‌کنند. "
            "کارکنان باید ۵ دقیقه پیش از حرکت سرویس در محل حاضر باشند و پس از ثبت خروج در دستگاه تردد سوار سرویس شوند.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "آیا بسته پستی و خرید اینترنتی توسط انتظامات تحویل گرفته می‌شود؟\n\n"

            "✅ پاسخ:\n"
            "بله، بسته‌های پستی و خریدهای اینترنتی توسط انتظامات تحویل گرفته شده و به دبیرخانه شرکت تحویل داده می‌شود."

        )
    elif text == "🍽 غذا و پذیرایی":
        await update.message.reply_text(

            "🍽 غذا و پذیرایی\n\n"

            "❓ سوال:\n"
            "رزرو غذا چگونه انجام می‌شود؟\n\n"

            "✅ پاسخ:\n"
            "منوی ماهانه غذا در سامانه کسرا بارگذاری می‌شود و کارکنان یک هفته فرصت دارند غذای موردنظر خود را انتخاب کنند.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "ساعات پذیرایی چای و عصرانه چگونه است؟\n\n"

            "✅ پاسخ:\n"
            "چای صبح کارکنان اداری: ساعت ۸:۰۰\n"
            "چای صبح کارکنان اداری و تولید: ساعت ۱۰:۰۰\n"
            "چای عصر کارکنان اداری: ساعت ۱۴:۰۰\n"
            "چای عصر کارکنان اداری و تولید: ساعت ۱۶:۰۰\n"
            "عصرانه کارکنان دارای اضافه‌کاری: ساعت ۱۶:۳۰"

        )
    elif text == "💻 فناوری اطلاعات":
        await update.message.reply_text(

            "💻 فناوری اطلاعات\n\n"

            "❓ سوال:\n"
            "برای نصب، حذف و به‌روزرسانی نرم‌افزار و سخت‌افزار بر روی رایانه‌ها چه باید کرد؟\n\n"

            "✅ پاسخ:\n"
            "درخواست خود را از طریق «فرم درخواست کار از واحد فناوری اطلاعات» و پس از تأیید مدیر واحد به واحد فناوری اطلاعات ارسال کنید.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "آیا ورود لپ‌تاپ یا تجهیزات ذخیره‌سازی اطلاعات به شرکت مجاز است؟\n\n"

            "✅ پاسخ:\n"
            "ورود و خروج لپ‌تاپ، تبلت، رایانه و سایر تجهیزات ذخیره‌سازی اطلاعات ممنوع است. "
            "موارد استثنا فقط با هماهنگی و تأیید واحد فناوری اطلاعات امکان‌پذیر است."

        )
    elif text == "💰 تسهیلات رفاهی":
        await update.message.reply_text(

            "💰 تسهیلات رفاهی\n\n"

            "❓ سوال:\n"
            "شرایط دریافت وام صندوق تعاون چیست؟\n\n"

            "✅ پاسخ:\n"
            "برای عضویت در صندوق تعاون، درخواست خود را از طریق نامه به مدیر مالی ارائه کنید. "
            "ماهانه ۴ درصد از حقوق و مزایای پرسنل کسر و به صندوق واریز می‌شود. "
            "پس از یک سال عضویت، می‌توانید درخواست وام خود را از طریق فرم مربوطه به دبیرخانه ارسال کنید.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "وام صندوق کارگشایی چیست و چگونه دریافت می‌شود؟\n\n"

            "✅ پاسخ:\n"
            "کارکنان پس از یک سال از تاریخ شروع به کار می‌توانند با تکمیل فرم درخواست وام، "
            "تقاضای خود را به دبیرخانه ارائه کنند.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "از چه زمانی امکان دریافت وام وجود دارد؟\n\n"

            "✅ پاسخ:\n"
            "امکان استفاده از تسهیلات وام پس از یک سال حضور در شرکت فراهم می‌شود.\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "❓ سوال:\n"
            "برای دریافت اقلام رفاهی به چند ماه سابقه کار در شرکت نیاز است؟\n\n"

            "✅ پاسخ:\n"
            "داشتن سه ماه سابقه کار در شرکت جهت دریافت اقلام رفاهی الزامی می‌باشد."

        )
    elif text == "🎓 آموزش":
        await update.message.reply_text("سوالات و پاسخ های بخش آموزش به زودی اضافه خواهد شد...")

    elif text == "🔙 بازگشت":
        await update.message.reply_text(
            "برگشت به منو",
            reply_markup=get_markup(user_id)
        )
        return

    else:

        await update.message.reply_text(

            "❌ سوال شما در پایگاه دانش یافت نشد.\n\n"

            "لطفا از منو انتخاب کنید یا سوال خود را واضح‌ تر بنویسید."

        )

        return


# ================== MAIN ==================


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            handle
        )
    )
    app.add_handler(CallbackQueryHandler(button_handler))

    print("BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()
