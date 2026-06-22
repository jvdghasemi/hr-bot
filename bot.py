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

# ================== منو ==================
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

cancel_keyboard = ReplyKeyboardMarkup([["❌ انصراف"]], resize_keyboard=True)

confirm_keyboard = ReplyKeyboardMarkup(
    [["✅ ارسال", "❌ لغو"]], resize_keyboard=True)

sms_keyboard = ReplyKeyboardMarkup(
    [
        ["📩 ارسال پیام معمولی"],
        ["🧑‍💼 پیام عدم تأیید مصاحبه"],
        ["📊 پیام دعوت به مصاحبه"],
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
            [["🚀 Start / Menu"]], resize_keyboard=True)
    )


# ================== HANDLE ==================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    user_id = update.effective_user.id

    # ================== ورود ==================
    if text == "🚀 Start / Menu":
        await update.message.reply_text("🔓 وارد منو شدی", reply_markup=get_markup(user_id))
        return

    # ================== بازگشت ==================
    if text == "🔙 بازگشت":
        context.user_data.clear()
        await update.message.reply_text("🔙 منو", reply_markup=get_markup(user_id))
        return

    # ================== CANCEL GLOBAL ==================
    if text == "❌ انصراف":
        context.user_data.clear()
        await update.message.reply_text("❌ لغو شد", reply_markup=get_markup(user_id))
        return

    # ================== عدم تایید مصاحبه ==================
    if context.user_data.get("step") == "get_name":
        context.user_data["name"] = text
        context.user_data["step"] = "get_phone"

        await update.message.reply_text("📱 شماره تلفن را وارد کنید:", reply_markup=cancel_keyboard)
        return

    if context.user_data.get("step") == "get_phone":

        phone = text.strip()

        if not (phone.isdigit() and len(phone) == 11):
            await update.message.reply_text("❌ شماره نامعتبر است (11 رقم)")
            return

        name = context.user_data.get("name", "")

        message = f"""{name}

از حضور شما در مصاحبه سپاسگزاریم.
در حال حاضر امکان همکاری وجود ندارد.
رزومه شما در سیستم ذخیره شد.
"""

        # ⚠️ مهم: state قبل از پاک شدن ذخیره میشه
        context.user_data["final_message"] = message
        context.user_data["step"] = "preview"

        await update.message.reply_text(
            "📌 پیش‌نمایش:\n\n" + message,
            reply_markup=confirm_keyboard
        )
        return

    if text == "✅ ارسال" and context.user_data.get("step") == "preview":
        context.user_data.clear()
        await update.message.reply_text("✅ ارسال شد", reply_markup=get_markup(user_id))
        return

    if text == "❌ لغو" and context.user_data.get("step") == "preview":
        context.user_data.clear()
        await update.message.reply_text("❌ لغو شد", reply_markup=get_markup(user_id))
        return

    # ================== صدای کارکنان ==================
    if context.user_data.get("voice_staff"):

        info = f"🎙️ پیام کارمند\n👤 {update.effective_user.first_name}"

        await context.bot.send_message(chat_id=ADMIN_ID, text=info)

        if update.message.voice:
            await context.bot.send_voice(chat_id=ADMIN_ID, voice=update.message.voice.file_id)
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=text)

        context.user_data.clear()

        await update.message.reply_text("✅ ارسال شد", reply_markup=get_markup(user_id))
        return

    # ================== منو ==================
    if text == "🧑‍💼 پیام عدم تأیید مصاحبه":
        context.user_data["step"] = "get_name"
        await update.message.reply_text("👤 نام را وارد کنید:")
        return

    if text == "🎙️ صدای کارکنان":
        context.user_data["voice_staff"] = True
        await update.message.reply_text("✍ متن یا ویس بفرستید", reply_markup=cancel_keyboard)
        return

    if text == "🌐 شبکه های اجتماعی":
        await update.message.reply_text("یکی را انتخاب کنید:", reply_markup=social_keyboard)
        return

    if text == "📷 اینستاگرام":
        await update.message.reply_text("https://instagram.com/iranhormone")
        return

    if text == "✈️ تلگرام":
        await update.message.reply_text("https://t.me/irhormon")
        return

    if text == "🔵 لینکدین":
        await update.message.reply_text(
            "https://linkedin.com/company/iranhormonepharmaceuticalcompany/"
        )
        return

    if text == "🟢 بله":
        await update.message.reply_text("https://ble.ir/iranhormon")
        return

    if text == "📞 تماس‌ با ما":
        await update.message.reply_text(
            "📞 تماس:\n02144905517\n\n📍 تهران، جاده مخصوص کرج"
        )
        return

    if text == "❓ سوالات پر تکرار":
        await update.message.reply_text("شرکت داروسازی ایران هورمون")
        return

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
