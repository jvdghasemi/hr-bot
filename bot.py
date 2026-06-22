from datetime import datetime
import pytz
import jdatetime
import asyncio
import os

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

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 7186618503

# ================== منوها ==================
keyboard = [
    ["❓ سوالات پر تکرار", "🌐 شبکه های اجتماعی"],
    ["📝 پیام مدیر عامل", "🤝 فرصت های شغلی"],
    ["🎙️ صدای کارکنان", "📞 تماس‌ با ما"]
]

admin_keyboard = [
    ["📢 ارسال پیامک"],
    ["❓ سوالات پر تکرار", "🌐 شبکه های اجتماعی"],
    ["📝 پیام مدیر عامل", "🤝 فرصت های شغلی"],
    ["🎙️ صدای کارکنان", "📞 تماس‌ با ما"],
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

sms_keyboard = ReplyKeyboardMarkup(
    [
        ["📩 ارسال پیام معمولی"],
        ["🧑‍💼 پیام عدم تأیید مصاحبه"],
        ["📊 پیام دعوت به مصاحبه"],
        ["🔙 بازگشت"]
    ],
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
    return admin_markup if user_id == ADMIN_ID else user_markup


# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonCommands()
    )

    await update.message.reply_text(
        "👋 سلام\nبه دستیار منابع انسانی ایران هورمون خوش آمدید"
    )

    await asyncio.sleep(1)

    await update.message.reply_text(
        "👇 برای ورود به منو روی دکمه زیر بزن",
        reply_markup=ReplyKeyboardMarkup(
            [["🚀 Start / Menu"]],
            resize_keyboard=True
        )
    )


# ================== HANDLE ==================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    text = update.message.text or ""
    user_id = update.effective_user.id

    # ---------- ورود ----------
    if text == "🚀 Start / Menu":
        await update.message.reply_text(
            "🔓 وارد منو شدی",
            reply_markup=get_markup(user_id)
        )
        return

    # ---------- بازگشت ----------
    if text == "🏠 منو / Start":
        await update.message.reply_text(
            "🔙 منو فعال شد",
            reply_markup=get_markup(user_id)
        )
        return

    # ================== FEEDBACK ==================
    if context.user_data.get("feedback"):

        if text == "❌ انصراف":
            context.user_data["feedback"] = False
            await update.message.reply_text("❌ لغو شد", reply_markup=get_markup(user_id))
            return

        user = update.effective_user

        tehran = pytz.timezone("Asia/Tehran")
        now = jdatetime.datetime.fromgregorian(datetime=datetime.now(tehran))

        username = f"@{user.username}" if user.username else "ندارد"

        message = (
            f"📩 پیشنهاد/انتقاد جدید\n\n"
            f"👤 نام: {user.first_name}\n"
            f"🔹 یوزرنیم: {username}\n"
            f"🆔 آیدی: {user.id}\n"
            f"📅 تاریخ: {now.strftime('%Y/%m/%d')}\n"
            f"🕒 ساعت: {now.strftime('%H:%M:%S')}\n\n"
            f"💬 متن:\n{text}"
        )

        await context.bot.send_message(chat_id=ADMIN_ID, text=message)

        await update.message.reply_text("✅ ارسال شد 🙏", reply_markup=get_markup(user_id))
        context.user_data["feedback"] = False
        return

    # ================== VOICE STAFF ==================
    if context.user_data.get("voice_staff"):

        user = update.effective_user
        username = f"@{user.username}" if user.username else "ندارد"

        info = (
            f"🎙️ پیام جدید کارکنان\n\n"
            f"👤 نام: {user.first_name}\n"
            f"🔹 یوزرنیم: {username}\n"
            f"🆔 آیدی: {user.id}"
        )

        if text == "❌ انصراف":
            context.user_data["voice_staff"] = False
            await update.message.reply_text("❌ لغو شد", reply_markup=get_markup(user_id))
            return

        if update.message.voice:
            await context.bot.send_message(chat_id=ADMIN_ID, text=info)
            await context.bot.send_voice(chat_id=ADMIN_ID, voice=update.message.voice.file_id)

            context.user_data["voice_staff"] = False
            await update.message.reply_text("✅ ویس شما ارسال شد", reply_markup=get_markup(user_id))
            return

        if update.message.text:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=info + f"\n\n💬 متن:\n{text}"
            )

            context.user_data["voice_staff"] = False
            await update.message.reply_text("✅ نظر شما ارسال شد", reply_markup=get_markup(user_id))
            return

    # ================== SMS MENU ==================
    if context.user_data.get("sms_menu"):

        if text == "🔙 بازگشت":
            context.user_data["sms_menu"] = False
            await update.message.reply_text("برگشت به منو", reply_markup=get_markup(user_id))
            return

        return

    # ================== MAIN MENU ==================
    if text == "🤝 فرصت های شغلی":
        await update.message.reply_text("کلید 1")
        return

    elif text == "📝 پیام مدیر عامل":
        await update.message.reply_text("کلید 2 🚐")
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

    elif text == "📢 ارسال پیامک":
        context.user_data["sms_menu"] = True
        await update.message.reply_text(
            "نوع پیام را انتخاب کنید:",
            reply_markup=sms_keyboard
        )
        return

    elif text == "🎙️ صدای کارکنان":
        context.user_data["voice_staff"] = True
        await update.message.reply_text(
            "🎤 نظر خود را ارسال کنید\n\n❌ انصراف",
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
        await update.message.reply_text("بخش قرارداد و استخدام")

    elif text == "📍 حضور و غیاب و تردد":
        await update.message.reply_text("بخش حضور و غیاب و تردد")

    elif text == "➕ اضافه کاری":
        await update.message.reply_text("بخش اضافه کاری")

    elif text == "🏖 مرخصی":
        await update.message.reply_text("بخش مرخصی")

    elif text == "🛡 انتظامات":
        await update.message.reply_text("بخش انتظامات")

    elif text == "🍽 غذا و پذیرایی":
        await update.message.reply_text("بخش غذا و پذیرایی")

    elif text == "💻 فناوری اطلاعات":
        await update.message.reply_text("بخش فناوری اطلاعات")

    elif text == "💰 تسهیلات رفاهی":
        await update.message.reply_text("بخش تسهیلات رفاهی")

    elif text == "🎓 آموزش":
        await update.message.reply_text("بخش آموزش")

    elif text == "🔙 بازگشت":
        await update.message.reply_text(
            "برگشت به منو",
            reply_markup=get_markup(user_id)
        )
        return

    else:
        await update.message.reply_text("از منو انتخاب کن")


# ================== MAIN ==================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.VOICE, handle))

    print("BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()
