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
ADMIN_ID = 8040436465

# ================== منو اصلی ==================
keyboard = [
    ["❓ سوالات پر تکرار", "🌐 شبکه های اجتماعی"],
    ["📝 پیام مدیر عامل", "🤝 فرصت های شغلی"],
    ["✉️ پیشنهادات و انتقادات", "📞 تماس‌ با ما"]
]

admin_keyboard = [
    ["❓ سوالات پر تکرار", "🌐 شبکه های اجتماعی"],
    ["📝 پیام مدیر عامل", "🤝 فرصت های شغلی"],
    ["✉️ پیشنهادات و انتقادات", "📞 تماس‌ با ما"],
    ["🎉 ارسال پیام خوشامدگویی"]
]

# ================== کیبوردها ==================
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

cancel_keyboard = ReplyKeyboardMarkup(
    [["❌ انصراف"]],
    resize_keyboard=True
)

user_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
admin_markup = ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True)

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
    try:
        await msg.delete()
    except:
        pass

    await update.message.reply_text(
        "👇 برای ورود به منو روی دکمه زیر بزن",
        reply_markup=ReplyKeyboardMarkup(
            [["🚀 Start / Menu"]],
            resize_keyboard=True
        )
    )

# ================== HANDLE ==================


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # ---------- ورود ----------
    if text == "🚀 Start / Menu":
        markup = admin_markup if user_id == ADMIN_ID else user_markup

        await update.message.reply_text(
            "🔓 وارد منو شدی",
            reply_markup=markup
        )
        return

    # ---------- بازگشت ----------
    if text == "🏠 منو / Start":
        markup = admin_markup if user_id == ADMIN_ID else user_markup

        await update.message.reply_text(
            "🔙 منو فعال شد",
            reply_markup=markup
        )
        return

    # ================== پیشنهادات ==================
    if context.user_data.get("feedback"):

        if text == "❌ انصراف":
            context.user_data["feedback"] = False
            await update.message.reply_text("❌ لغو شد", reply_markup=user_markup)
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

        await update.message.reply_text("✅ ارسال شد 🙏", reply_markup=user_markup)

        context.user_data["feedback"] = False
        return

    # ================== خوشامدگویی ==================
    if context.user_data.get("get_name"):

        if text == "❌ انصراف":
            context.user_data.clear()
            await update.message.reply_text("❌ لغو شد", reply_markup=admin_markup)
            return

        context.user_data["employee_name"] = text
        context.user_data["get_name"] = False
        context.user_data["get_phone"] = True

        await update.message.reply_text(
            "📱 شماره موبایل کارمند جدید را وارد کنید:",
            reply_markup=cancel_keyboard
        )
        return

    if context.user_data.get("get_phone"):

        if text == "❌ انصراف":
            context.user_data.clear()
            await update.message.reply_text("❌ لغو شد", reply_markup=user_markup)
            return

        name = context.user_data["employee_name"]
        phone = text

        context.user_data.clear()

        await update.message.reply_text(
            f"✅ پیام خوشامدگویی ثبت شد.\n\n👤 {name}\n📱 {phone}",
            reply_markup=user_markup
        )
        return

    # ================== منو ==================
    if text == "🤝 فرصت های شغلی":
        await update.message.reply_text("کلید 1")

    elif text == "📝 پیام مدیر عامل":
        await update.message.reply_text("کلید 2 🚐")

    elif text == "🌐 شبکه های اجتماعی":
        await update.message.reply_text("یکی رو انتخاب کن:", reply_markup=social_keyboard)

    elif text == "📷 اینستاگرام":
        await update.message.reply_text("https://instagram.com/iranhormone")

    elif text == "✈️ تلگرام":
        await update.message.reply_text("https://t.me/irhormon")

    elif text == "🔵 لینکدین":
        await update.message.reply_text(
            "https://linkedin.com/company/iranhormonepharmaceuticalcompany/"
        )

    elif text == "🟢 بله":
        await update.message.reply_text("https://ble.ir/iranhormon")

    elif text == "🔙 بازگشت":
        await update.message.reply_text("برگشتی به منو", reply_markup=user_markup)

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

    elif text == "✉️ پیشنهادات و انتقادات":
        context.user_data["feedback"] = True
        await update.message.reply_text("📝 لطفا پیشنهاد و یا انتقاد خود را بنویسید", reply_markup=feedback_keyboard)

    elif text == "🎉 ارسال پیام خوشامدگویی":
        context.user_data["get_name"] = True
        await update.message.reply_text("👤 نام کارمند جدید را وارد کنید:", reply_markup=cancel_keyboard)

    elif text == "❓ سوالات پر تکرار":
        await update.message.reply_text("شرکت داروسازی ایران هورمون")

    else:
        await update.message.reply_text("از منو انتخاب کن")


# ================== MAIN ==================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()
