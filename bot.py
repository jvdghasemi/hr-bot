from datetime import datetime
import pytz
import jdatetime
import asyncio

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os


TOKEN = os.getenv("TOKEN")

keyboard = [
    ["🏢 اطلاعات شرکت", "🌐 شبکه های اجتماعی"],
    ["🚕 کلید 2", "⏰ کلید 1"],
    ["✉️ پیشنهادات و انتقادات", "📞 تماس‌ با ما"]
]

menu_keyboard = ReplyKeyboardMarkup(
    [
        ["🏠 منو / Start"]
    ],
    resize_keyboard=True,
    is_persistent=True
)

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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
    [
        ["❌ انصراف"]
    ],
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = await update.message.reply_text(
        "👋 سلام\nبه دستیار منابع انسانی ایران هورمون خوش آمدی"
    )

    # 2 ثانیه صبر
    await asyncio.sleep(2)

    # پاک کردن پیام سلام
    await msg.delete()

    # دکمه ورود به منو
    await update.message.reply_text(
        "👇 برای ورود به منو روی دکمه زیر بزن",
        reply_markup=ReplyKeyboardMarkup(
            [["🚀 ورود به منو"]],
            resize_keyboard=True
        )
    )

ADMIN_ID = 8040436465


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🚀 ورود به منو":
        msg = await update.message.reply_text(
            "🔓 وارد منو شدی",
            reply_markup=reply_markup
        )

        await asyncio.sleep(2)
        await msg.delete()
        return

    if text == "🏠 منو / Start":
        await update.message.reply_text(
            "✅ ورود به منو",
            reply_markup=reply_markup
        )
        return

    # ================== حالت پیشنهادات ==================
    if context.user_data.get("feedback"):

        if text == "❌ انصراف":
            context.user_data["feedback"] = False

            await update.message.reply_text(
                "❌ ثبت پیشنهاد لغو شد.",
                reply_markup=reply_markup
            )
            return

        user = update.effective_user

        tehran_tz = pytz.timezone("Asia/Tehran")

        now = datetime.now(tehran_tz).replace(tzinfo=None)
        now = jdatetime.datetime.fromgregorian(datetime=now)

        username = f"@{user.username}" if user.username else "ندارد"

        message = (
            f"📩 پیشنهاد/انتقاد جدید\n\n"
            f"👤 نام: {user.first_name}\n"
            f"🔹 نام کاربری: {username}\n"
            f"🆔 آیدی: {user.id}\n"
            f"📅 تاریخ: {now.strftime('%Y/%m/%d')}\n"
            f"🕒 ساعت: {now.strftime('%H:%M:%S')}\n\n"
            f"💬 متن پیام:\n{text}"
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=message
        )

        await update.message.reply_text(
            "✅ نظر شما ارسال شد. ممنون از مشارکت شما 🙏",
            reply_markup=reply_markup
        )

        context.user_data["feedback"] = False
        return

    # ================== منو ==================
    if text == "⏰ کلید 1":
        await update.message.reply_text("کلید 1")

    elif text == "🚕 کلید 2":
        await update.message.reply_text("کلید 2 🚐")

    elif text == "🌐 شبکه های اجتماعی":
        await update.message.reply_text(
            "یکی از شبکه‌ها را انتخاب کنید:",
            reply_markup=social_keyboard
        )

    elif text == "📷 اینستاگرام":
        await update.message.reply_text(
            "https://instagram.com/iranhormone?igsh=cGVycHZlN2N0dzE1"
        )

    elif text == "✈️ تلگرام":
        await update.message.reply_text("https://t.me/irhormon")

    elif text == "🔵 لینکدین":
        await update.message.reply_text(
            "https://linkedin.com/company/iranhormonepharmaceuticalcompany/"
        )

    elif text == "🟢 بله":
        await update.message.reply_text("https://ble.ir/iranhormone")

    elif text == "🔙 بازگشت":
        await update.message.reply_text(
            "از منو انتخاب کنید:",
            reply_markup=reply_markup
        )

    elif text == "📞 تماس‌ با ما":
        await update.message.reply_text("کلید 4")

    elif text == "✉️ پیشنهادات و انتقادات":
        context.user_data["feedback"] = True

        await update.message.reply_text(
            "📝 لطفاً پیشنهاد یا انتقاد خود را بنویسید.",
            reply_markup=feedback_keyboard
        )

    elif text == "🏢 اطلاعات شرکت":
        await update.message.reply_text("شرکت داروسازی ایران هورمون")

    else:
        await update.message.reply_text("از منو انتخاب کن")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("NEW VERSION LOADED")
    app.run_polling()


if __name__ == "__main__":
    main()
