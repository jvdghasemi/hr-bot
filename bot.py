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

# ================== منوها ==================
keyboard = [
    ["❓ سوالات پر تکرار", "🌐 شبکه های اجتماعی"],
    ["📝 پیام مدیر عامل", "🤝 فرصت های شغلی"],
    ["✉️ پیشنهادات و انتقادات", "📞 تماس‌ با ما"]
]

admin_keyboard = [
    ["📢 ارسال پیامک"],
    ["❓ سوالات پر تکرار", "🌐 شبکه های اجتماعی"],
    ["📝 پیام مدیر عامل", "🤝 فرصت های شغلی"],
    ["✉️ پیشنهادات و انتقادات", "📞 تماس‌ با ما"],
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

feedback_keyboard = ReplyKeyboardMarkup([["❌ انصراف"]], resize_keyboard=True)
cancel_keyboard = ReplyKeyboardMarkup([["❌ انصراف"]], resize_keyboard=True)

confirm_keyboard = ReplyKeyboardMarkup(
    [["✅ ارسال", "❌ لغو"]],
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

    msg = await update.message.reply_text(
        "👋 سلام\nبه دستیار منابع انسانی ایران هورمون خوش آمدید"
    )

    await asyncio.sleep(1)
    await msg.delete()

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
    user = update.effective_user
    user_id = user.id

    # ========== START MENU ==========
    if text == "🚀 Start / Menu":
        await update.message.reply_text(
            "🔓 وارد منو شدی",
            reply_markup=get_markup(user_id)
        )
        return

    # ========== BACK ==========
    if text == "🏠 منو / Start":
        await update.message.reply_text(
            "🔙 منو فعال شد",
            reply_markup=get_markup(user_id)
        )
        return

    # ========== SMS FLOW ==========
    if context.user_data.get("step") == "get_name":
        context.user_data["name"] = text
        context.user_data["step"] = "get_phone"

        await update.message.reply_text("📱 شماره تلفن را وارد کنید:")
        return

    if context.user_data.get("step") == "get_phone":

        name = context.user_data["name"]
        phone = text

        tehran = pytz.timezone("Asia/Tehran")
        now = datetime.now(tehran)
        now = jdatetime.datetime.fromgregorian(datetime=now)

        message = f"""جناب آقای/ سرکار خانم {name}

با سلام

از حضور شما در جلسه مصاحبه شرکت داروسازی ایران هورمون سپاسگزاریم.

در حال حاضر اولویت های مجموعه ما با شرایط شما متفاوت است.
رزومه شما در بانک اطلاعاتی ما حفظ خواهد شد.

📱 تماس: {phone}
📅 {now.strftime('%Y/%m/%d')}
🕒 {now.strftime('%H:%M:%S')}
"""

        context.user_data["final_message"] = message
        context.user_data["step"] = "preview"

        await update.message.reply_text(
            "📌 پیش‌نمایش پیام:\n\n" + message,
            reply_markup=confirm_keyboard
        )
        return

    # ========== CONFIRM ==========
    if text == "✅ ارسال":
        if "final_message" in context.user_data:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text="📤 ارسال شد:\n\n" + context.user_data["final_message"]
            )

        context.user_data.clear()

        await update.message.reply_text("✅ انجام شد ✔️", reply_markup=get_markup(user_id))
        return

    # ========== CANCEL ==========
    if text == "❌ لغو":
        context.user_data.clear()
        await update.message.reply_text("❌ لغو شد", reply_markup=get_markup(user_id))
        return

    # ========== FEEDBACK ==========
    if context.user_data.get("feedback"):
        if text == "❌ انصراف":
            context.user_data["feedback"] = False
            await update.message.reply_text("❌ لغو شد", reply_markup=get_markup(user_id))
            return

        tehran = pytz.timezone("Asia/Tehran")
        now = datetime.now(tehran)
        now = jdatetime.datetime.fromgregorian(datetime=now)

        username = f"@{user.username}" if user.username else "ندارد"

        message = (
            "📩 پیام جدید\n\n"
            f"👤 نام: {user.first_name}\n"
            f"🔹 یوزرنیم: {username}\n"
            f"🆔 آیدی: {user.id}\n"
            f"📅 {now.strftime('%Y/%m/%d')}\n"
            f"🕒 {now.strftime('%H:%M:%S')}\n\n"
            f"💬 متن:\n{text}"
        )

        await context.bot.send_message(chat_id=ADMIN_ID, text=message)

        await update.message.reply_text("✅ ارسال شد", reply_markup=get_markup(user_id))
        context.user_data["feedback"] = False
        return

    # ========== MENU ==========
    if text == "📢 ارسال پیامک":
        context.user_data["step"] = "get_name"
        await update.message.reply_text("👤 نام را وارد کنید:")
        return

    if text == "✉️ پیشنهادات و انتقادات":
        context.user_data["feedback"] = True
        await update.message.reply_text("📝 متن را بنویسید:", reply_markup=feedback_keyboard)
        return

    if text == "🌐 شبکه های اجتماعی":
        await update.message.reply_text("انتخاب کنید:", reply_markup=social_keyboard)
        return

    if text == "📷 اینستاگرام":
        await update.message.reply_text("https://instagram.com/iranhormone")
        return

    if text == "✈️ تلگرام":
        await update.message.reply_text("https://t.me/irhormon")
        return

    if text == "🔵 لینکدین":
        await update.message.reply_text("https://linkedin.com/company/iranhormonepharmaceuticalcompany/")
        return

    if text == "🟢 بله":
        await update.message.reply_text("https://ble.ir/iranhormon")
        return

    if text == "📞 تماس‌ با ما":
        await update.message.reply_text(
            "📞 شرکت داروسازی ایران هورمون\n\n"
            "🌐 https://www.iranhormone.ir\n"
            "📧 info@iranhormone.com\n"
            "☎️ 02144905517\n"
            "📍 تهران، جاده مخصوص کرج\n"
            "📮 1399813611"
        )
        return

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
