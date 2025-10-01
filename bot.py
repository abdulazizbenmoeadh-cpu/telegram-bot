import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# 🔹 التوكن سيؤخذ من بيئة التشغيل في Render (لا تكتبه هنا يدوياً)
TOKEN = os.getenv("TOKEN")

# 🔹 ID الخاص بك كإدمن (سيصلك كل الصور)
ADMIN_CHAT_ID = 8439544955

# 🔹 عدد المحاولات المسموح بها لتغيير الصورة
MAX_RETRIES = 3

# حفظ بيانات المستخدمين (عدد المحاولات + معرف الرسائل المرسلة)
user_data = {}

# ⬇️ دالة البدء
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📷 طلب تعديل الصورة", callback_data="edit_photo")],
        [InlineKeyboardButton("💰 عرض الأسعار", callback_data="pricing")],
        [InlineKeyboardButton("ℹ️ المساعدة", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 مرحباً بك في بوت خدمة تعديل الصور!\n\n"
        "يمكنك عبر هذا البوت الحصول على تجربة مجانية لتعديل صورة واحدة، "
        "وأيضاً يمكنك الاطلاع على باقات الاشتراك الخاصة بنا.\n\n"
        "فضلاً، اختر أحد الخيارات من الأسفل:",
        reply_markup=reply_markup
    )

# ⬇️ التعامل مع الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "edit_photo":
        user_data[query.from_user.id] = {"retries": 0, "last_message": None}
        await query.message.reply_text(
            "✅ لديك تجربة مجانية واحدة.\n\n"
            "📸 يرجى إرسال صورة واضحة الآن حتى نتمكن من العمل عليها.\n\n"
            "⚠️ ملاحظة: بعد إرسال الصورة سيتم إعلامك أن العملية قد تستغرق ساعة، "
            "وسيكون لديك إمكانية تغيير الصورة بحد أقصى 3 مرات."
        )

    elif query.data == "pricing":
        await query.message.reply_text(
            "💰 قائمة الأسعار لدينا:\n\n"
            "🔹 10 صور = 7 دولار\n"
            "🔹 50 صورة = 33 دولار\n"
            "🔹 100 صورة = 49 دولار\n\n"
            "✨ جميع الصور بجودة عالية مع تعديل احترافي."
        )

    elif query.data == "help":
        await query.message.reply_text(
            "ℹ️ *تعليمات الاستخدام:*\n\n"
            "1️⃣ اضغط على زر (طلب تعديل الصورة).\n"
            "2️⃣ أرسل صورة واضحة.\n"
            "3️⃣ بعد الإرسال سيتم إعلامك بالمدة (حوالي ساعة).\n"
            "4️⃣ لديك خيار تبديل الصورة بحد أقصى 3 مرات.\n\n"
            "📌 الأسعار متاحة من خلال زر (عرض الأسعار).",
            parse_mode="Markdown"
        )

# ⬇️ استقبال الصور من المستخدم
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]  # أفضل دقة
    file_id = photo.file_id

    if user_id not in user_data:
        await update.message.reply_text(
            "⚠️ من فضلك ابدأ أولاً بالضغط على زر (طلب تعديل الصورة) من القائمة."
        )
        return

    retries = user_data[user_id]["retries"]

    # إذا كان لديه محاولات سابقة
    if retries >= MAX_RETRIES:
        await update.message.reply_text(
            "🚫 لقد استهلكت جميع محاولات تغيير الصورة (3 مرات).\n"
            "لن يتم قبول المزيد من الصور للتجربة المجانية."
        )
        return

    # حذف الصورة السابقة من دردشة المستخدم (إن وجدت)
    if user_data[user_id]["last_message"]:
        try:
            await context.bot.delete_message(
                chat_id=user_id,
                message_id=user_data[user_id]["last_message"]
            )
        except:
            pass  # إذا لم يستطع الحذف نتجاهل

    # إرسال رد للمستخدم
    sent_msg = await update.message.reply_text(
        "✅ تم استلام الصورة.\n\n"
        "⏳ العملية قد تستغرق حوالي ساعة لإرسال النتيجة.\n\n"
        "📌 يمكنك تغيير الصورة (بحد أقصى 3 مرات)."
    )

    # حفظ بيانات الرسالة
    user_data[user_id]["retries"] += 1
    user_data[user_id]["last_message"] = sent_msg.message_id

    # إرسال الصورة إلى الإدمن (أنت)
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=file_id,
        caption=f"📩 صورة جديدة من المستخدم ID: {user_id}\n"
                f"🔄 المحاولة رقم: {user_data[user_id]['retries']}"
    )

# ⬇️ معرفة Chat ID لأي مستخدم (للاختبار فقط)
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔑 Chat ID الخاص بك هو: {update.message.chat_id}")

# ⬇️ تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("✅ البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
