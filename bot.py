from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

TOKEN = os.getenv("TOKEN")

keyboard = [
    ["🏢 اطلاعات شرکت", "⏰ ساعت کاری"],
    ["🚕 ایاب و ذهاب", "📝 مرخصی"],
    ["💰 حقوق", "📞 تماس‌ها"]
]

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سلام\nبه دستیار منابع انسانی ایران هورمون خوش آمدی",
        reply_markup=reply_markup
    )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "⏰ ساعت کاری":
        await update.message.reply_text("از 7 صبح تا 18 عصر")
    elif text == "🚕 ایاب و ذهاب":
        await update.message.reply_text("سرویس داریم 🚐")
    elif text == "📝 مرخصی":
        await update.message.reply_text("۲۶ روز در سال")
    elif text == "💰 حقوق":
        await update.message.reply_text("آخر ماه واریز میشه 💵")
    elif text == "📞 تماس‌ها":
        await update.message.reply_text("داخلی 101")
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
