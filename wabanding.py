import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import nest_asyncio
nest_asyncio.apply()

# ======== KONFIGURASI DARI ENV (Railway Variables) =========
EMAIL_KAMU = os.getenv("EMAIL_KAMU")
PASSWORD_APLIKASI = os.getenv("PASSWORD_APLIKASI")
PENERIMA = os.getenv("PENERIMA")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_IDS = [int(os.getenv("ADMIN_IDS"))]  # ambil dari Railway Variable
ALLOWED_USERS = set(ADMIN_IDS)
# ============================================================

# ======== FUNGSI TAMBAHAN ========
def buat_pesan_banding(nomor):
    return f"""
مرحباً فريق دعم واتساب،
أود الإبلاغ عن مشكلة في رقم واتساب الخاص بي {nomor}. عند محاولة التسجيل، تظهر لي رسالة "تسجيل الدخول غير متاح حالياً".

أتمنى أن يساعدني واتساب لأتمكن من استخدام رقمي {nomor} مجدداً دون هذه المشكلة. شكراً لاهتمامكم ومساعدتكم.
"""

def hanya_admin(func):
    """Dekorator: hanya admin yang bisa akses perintah"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Kamu bukan admin, akses ditolak.")
            return
        return await func(update, context)
    return wrapper

def cek_izin(func):
    """Dekorator: hanya user terdaftar yang bisa pakai bot"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USERS:
            await update.message.reply_text("🚫 Kamu tidak memiliki izin menggunakan bot ini.")
            return
        return await func(update, context)
    return wrapper

# ======== COMMAND HANDLER ========
@cek_izin
async def banding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Gunakan format:\n/banding +6281234567890")
        return

    nomor = context.args[0]
    teks_email = buat_pesan_banding(nomor)

    msg = MIMEText(teks_email)
    msg["Subject"] = f"My Number Can't Get Through {nomor}"
    msg["From"] = EMAIL_KAMU
    msg["To"] = PENERIMA

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_KAMU, PASSWORD_APLIKASI)
        server.send_message(msg)
        server.quit()
        await update.message.reply_text(f"✅ Email banding untuk {nomor} berhasil dikirim ke WhatsApp!")
        print(f"[LOG] Email banding untuk {nomor} berhasil dikirim oleh {update.effective_user.id}.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal mengirim email:\n{e}")
        print(f"[ERROR] {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ALLOWED_USERS:
        await update.message.reply_text("👋 Hai! Kirim banding WhatsApp dengan format:\n\n/banding +628xxxxxxxxxx")
    else:
        await update.message.reply_text("🚫 Kamu belum memiliki izin menggunakan bot ini.")

@hanya_admin
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan format: /adduser <id_telegram>")
        return

    try:
        user_id = int(context.args[0])
        ALLOWED_USERS.add(user_id)
        await update.message.reply_text(f"✅ User dengan ID {user_id} ditambahkan ke whitelist.")
        print(f"[ADMIN] Menambahkan user {user_id}")
    except ValueError:
        await update.message.reply_text("⚠️ ID harus berupa angka.")

@hanya_admin
async def del_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan format: /deluser <id_telegram>")
        return

    try:
        user_id = int(context.args[0])
        if user_id in ADMIN_IDS:
            await update.message.reply_text("⚠️ Tidak bisa menghapus admin.")
            return
        if user_id in ALLOWED_USERS:
            ALLOWED_USERS.remove(user_id)
            await update.message.reply_text(f"🗑️ User dengan ID {user_id} dihapus dari whitelist.")
            print(f"[ADMIN] Menghapus user {user_id}")
        else:
            await update.message.reply_text("❗ User tidak ditemukan di whitelist.")
    except ValueError:
        await update.message.reply_text("⚠️ ID harus berupa angka.")

@hanya_admin
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    daftar = "\n".join(str(uid) for uid in ALLOWED_USERS)
    await update.message.reply_text(f"👥 Daftar pengguna yang diizinkan:\n\n{daftar}")

# ======== MAIN ========
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("banding", banding))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("deluser", del_user))
    app.add_handler(CommandHandler("listusers", list_users))

    print("🤖 Bot sedang berjalan dengan sistem akses privat...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
