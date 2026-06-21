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

# ================== منو اصلی ==================
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

sms_keyboard = ReplyKeyboardMarkup(
    [
        ["📩 ارسال پیام معمولی"],
        ["🧑‍💼 پیام عدم تأیید مصاحبه"],
        ["📊 پیام دعوت به مصاحبه"],
        ["🔙 بازگشت"]
    ],
    resize_keyboard=True
)

cancel_keyboard = ReplyKeyboardMarkup(
    [["❌ انصراف"]],
    resize_keyboard=True
)

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

    # مرحله گرفتن اسم
    if context.user_data.get("step") == "get_name":

        context.user_data["name"] = text
        context.user_data["step"] = "get_phone"

        await update.message.reply_text(
            "📱 شماره تلفن مصاحبه‌شونده را وارد کنید:"
        )

        return

    # مرحله گرفتن شماره + ساخت پیش نمایش
    if context.user_data.get("step") == "get_phone":

        name = context.user_data["name"]

        context.user_data["phone"] = text

        message = f"""{name}

با سلام

از حضور شما در جلسه مصاحبه شرکت داروسازی ایران هورمون سپاسگزاریم.

در حال حاضر اولویت های مجموعه ما با شرایط شما متفاوت است.

رزومه شما در بانک اطلاعاتی ما حفظ خواهد شد و در صورت ایجاد فرصت های شغلی متناسب با مهارت های شما با شما تماس خواهیم گرفت.
"""

        context.user_data["final_message"] = message
        context.user_data["step"] = "preview"

        await update.message.reply_text(

            "📌 پیش‌نمایش پیام\n\n"
            + message,

            reply_markup=confirm_keyboard

        )

        return

    # تایید ارسال
    if text == "✅ ارسال":

        if context.user_data.get("step") == "preview":

            context.user_data.clear()

            await update.message.reply_text(
                "✅ پیام ارسال شد",
                reply_markup=get_markup(user_id)
            )

            return

    # لغو ارسال
    if text == "❌ لغو":

        if context.user_data.get("step") == "preview":

            context.user_data.clear()

            await update.message.reply_text(
                "❌ ارسال لغو شد",
                reply_markup=get_markup(user_id)
            )

            return
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

        await update.message.reply_text(
            "✅ ارسال شد 🙏",
            reply_markup=get_markup(user_id)
        )

        context.user_data["feedback"] = False
        return

    # ================== خوشامدگویی ==================
    if context.user_data.get("get_name"):

        if text == "❌ انصراف":
            context.user_data.clear()
            await update.message.reply_text("❌ لغو شد", reply_markup=get_markup(user_id))
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
            await update.message.reply_text("❌ لغو شد", reply_markup=get_markup(user_id))
            return

        name = context.user_data["employee_name"]
        phone = text

        context.user_data.clear()

        await update.message.reply_text(
            f"✅ پیام خوشامدگویی ثبت شد.\n\n👤 {name}\n📱 {phone}",
            reply_markup=get_markup(user_id)
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
        await update.message.reply_text(
            "برگشتی به منو",
            reply_markup=get_markup(user_id)
        )

    elif text == "📞 تماس‌ با ما":
        await update.message.reply_text(
            "📞 راه های ارتباطی شرکت داروسازی ایران هورمون\n\n"
            "🌐 وب‌سایت:\nhttps://www.iranhormone.ir\n\n"
            "📧 info@iranhormone.com\n\n"
            "☎️ 02144905517\n\n"
            "📍 تهران\n\n"
            "📮 1399813611"
        )

    elif text == "🧑‍💼 پیام عدم تأیید مصاحبه":

        context.user_data["step"] = "get_name"

        await update.message.reply_text(
            "👤 نام مصاحبه‌شونده را وارد کنید:"
        )

        return

    elif text == "📢 ارسال پیامک":
        context.user_data["sms_menu"] = True
        await update.message.reply_text(
            "نوع پیام را انتخاب کنید:",
            reply_markup=sms_keyboard
        )

    elif text == "🔙 بازگشت":
        context.user_data["sms_menu"] = False
        markup = admin_markup if user_id == ADMIN_ID else user_markup

        await update.message.reply_text(
            "برگشت به منو",
            reply_markup=markup
        )

    elif text == "✉️ پیشنهادات و انتقادات":
        context.user_data["feedback"] = True
        await update.message.reply_text(
            "📝 متن را بنویسید",
            reply_markup=feedback_keyboard
        )

    elif text == "🎉 ارسال پیام خوشامدگویی":
        context.user_data["get_name"] = True
        await update.message.reply_text(
            "👤 نام کارمند:",
            reply_markup=cancel_keyboard
        )

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
