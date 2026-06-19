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
    ["🏢 اطلاعات شرکت", "🌐 شبکه های اجتماعی"],
    ["🚕 کلید 2", "⏰ کلید 1"],
    ["✉️ پیشنهادات و انتقادات", "📞 تماس‌ با ما"]
]

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================== شبکه اجتماعی ==================
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

# ================== پیشنهادات ==================
feedback_keyboard = ReplyKeyboardMarkup(
    [["❌ انصراف"]],
    resize_keyboard=True
)


# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # فعال کردن منوی تلگرام (سنجاق)
    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonCommands()
    )

    msg = await update.message.reply_text(
        "👋 سلام\nبه دستیار منابع انسانی ایران هورمون خوش آمدی"
    )

    await asyncio.sleep(2)
    await msg.delete()

    await update.message.reply_text(
        "👇 برای ورود به منو روی دکمه زیر بزن",
        reply_markup=ReplyKeyboardMarkup(
            [["🚀 ورود به منو"]],
            resize_keyboard=True
        )
    )


# ================== HANDLE ==================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # ===== ورود =====
    if text == "🚀 ورود به منو":
        msg = await update.message.reply_text(
            "🔓 وارد منو شدی",
            reply_markup=reply_markup
        )

        await asyncio.sleep(2)
        await msg.delete()
        return

    # ===== بازگشت =====
    if text == "🏠 منو / Start":
        await update.message.reply_text(
            "🔙 برگشت به منو",
            reply_markup=reply_markup
        )
        return

    # ================== حالت پیشنهادات ==================
    if context.user_data.get("feedback"):

        if text == "❌ انصراف":
            context.user_data["feedback"] = False

            await update.message.reply_text(
                "❌ لغو شد",
                reply_markup=reply_markup
            )
            return

        user = update.effective_user

        tehran_tz = pytz.timezone("Asia/Tehran")
        now = datetime.now(tehran_tz)
        now = jdatetime.datetime.fromgregorian(datetime=now)

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

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=message
        )

        await update.message.reply_text(
            "✅ ارسال شد 🙏",
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
            "یکی رو انتخاب کن:",
            reply_markup=social_keyboard
        )

    elif text == "📷 اینستاگرام":
        await update.message.reply_text("https://instagram.com/iranhormone")

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
            "برگشتی به منو",
            reply_markup=reply_markup
        )

    elif text == "📞 تماس‌ با ما":
        await update.message.reply_text("کلید 4")

    elif text == "✉️ پیشنهادات و انتقادات":
        context.user_data["feedback"] = True

        await update.message.reply_text(
            "📝 پیامتو بنویس یا انصراف بزن",
            reply_markup=feedback_keyboard
        )

    elif text == "🏢 اطلاعات شرکت":
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
