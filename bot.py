from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

TOKEN = os.getenv("TOKEN")

keyboard = [
    ["🏢 اطلاعات شرکت", "🌐 شبکه های اجتماعی"],
    ["🚕 کلید 2", "⏰ کلید 1"],
    ["💰 کلید 3", "📞 تماس‌ها"]
]

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سلام\nبه دستیار منابع انسانی ایران هورمون خوش آمدی",
        reply_markup=reply_markup
    )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

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
        await update.message.reply_text("https://instagram.com/iranhormone?igsh=cGVycHZlN2N0dzE1")

    elif text == "✈️ تلگرام":
        await update.message.reply_text("https://t.me/irhormon")

    elif text == "🔵 لینکدین":
        await update.message.reply_text("https://linkedin.com/company/iranhormonepharmaceuticalcompany/")

    elif text == "🟢 بله":
        await update.message.reply_text("https://ble.ir/iranhormone")

    elif text == "🔙 بازگشت":
        await update.message.reply_text(
            "از منو انتخاب کنید:",
            reply_markup=reply_markup
        )
    elif text == "📞 تماس‌ با ما":
        await update.message.reply_text("کلید 4")

    elif text == "💰 کلید 3":
        await update.message.reply_text("کلید 3 💵")

    elif text == "🏢 اطلاعات شرکت":
        await update.message.reply_text("شرکت داروسازی ایران هورمون")

    else:
        await update.message.reply_text("از منو انتخاب کن")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("NEW VERSION LOADED")
    app.run_polling()


if __name__ == "__main__":
    main()
