import datetime
import time
import logging
import pickle
import os
import io
import threading

from telegram import Bot
from telegram.ext import CommandHandler, Updater

# ================== CONFIG ==================

TOKEN = os.getenv("8246711932:AAGN1raJxfSH8Qf2_Rx4ECyJmrgMIfXYifA")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")

ADMIN_ID = 6999604701
CHANNEL_ID = -1003075312230
INVITE_LINK = "https://t.me/+9e5QtDXXc9U4NDM1"
DATA_FILE = "subscribers.pkl"

# ============================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

bot = Bot(token=TOKEN)

# ---------- Persistence ----------

def load_data():
    try:
        with open(DATA_FILE, "rb") as f:
            data = pickle.load(f)
            logging.info("Subscribers loaded")
            return data
    except FileNotFoundError:
        return {}
    except Exception as e:
        logging.error(f"Load error: {e}")
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, "wb") as f:
            pickle.dump(data, f)
            logging.info("Subscribers saved")
    except Exception as e:
        logging.error(f"Save error: {e}")

subscribers = load_data()

# ---------- Commands ----------

def start(update, context):
    update.message.reply_text(
        "Welcome.\nPlease contact admin to activate your subscription."
    )

def add_user(update, context):
    global subscribers

    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("Unauthorized")
        return

    if len(context.args) < 2:
        update.message.reply_text("Usage: /add_user <user_id> <days>")
        return

    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)

        subscribers[user_id] = expiry
        save_data(subscribers)

        bot.send_message(
            chat_id=user_id,
            text=(
                f"Access granted for {days} days\n"
                f"Expires on: {expiry.date()}\n\n"
                f"Join channel:\n{INVITE_LINK}"
            )
        )

        update.message.reply_text(
            f"User {user_id} added until {expiry.date()}"
        )

    except Exception as e:
        update.message.reply_text(f"Error: {e}")

# ---------- Manual Export ----------

def download_data(update, context):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("Unauthorized")
        return

    if not subscribers:
        update.message.reply_text("No data to export")
        return

    lines = [
        f"{uid}|{exp.strftime('%Y-%m-%d %H:%M:%S')}"
        for uid, exp in subscribers.items()
    ]

    content = "\n".join(lines)
    filename = "subscribers_export.txt"

    with open(filename, "w") as f:
        f.write(content)

    with open(filename, "rb") as f:
        update.message.reply_document(
            document=f,
            caption="Reply with /export to restore"
        )

    os.remove(filename)

# ---------- Manual Import ----------

def upload_data(update, context):
    global subscribers

    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("Unauthorized")
        return

    if not update.message.reply_to_message:
        update.message.reply_text("Reply to export file with /export")
        return

    doc = update.message.reply_to_message.document
    if not doc or not doc.file_name.endswith(".txt"):
        update.message.reply_text("Invalid file")
        return

    try:
        file = bot.get_file(doc.file_id)
        buffer = io.BytesIO()
        file.download(out=buffer)
        buffer.seek(0)

        content = buffer.read().decode("utf-8")
        imported = 0

        for line in content.splitlines():
            if "|" not in line:
                continue

            uid, exp = line.split("|")
            subscribers[int(uid)] = datetime.datetime.strptime(
                exp.strip(), "%Y-%m-%d %H:%M:%S"
            )
            imported += 1

        save_data(subscribers)
        update.message.reply_text(
            f"Imported {imported} users\nTotal: {len(subscribers)}"
        )

    except Exception as e:
        update.message.reply_text(f"Import error: {e}")

# ---------- Subscription Checker ----------

def check_subscriptions():
    now = datetime.datetime.now()
    changed = False

    for user_id, expiry in list(subscribers.items()):
        if now > expiry:
            try:
                bot.ban_chat_member(CHANNEL_ID, user_id)
                del subscribers[user_id]
                changed = True
                logging.info(f"Removed expired user {user_id}")
            except Exception as e:
                logging.error(f"Ban error {user_id}: {e}")

    if changed:
        save_data(subscribers)

def subscription_worker():
    while True:
        check_subscriptions()
        time.sleep(3600)

# ---------- Main ----------

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add_user", add_user))
    dp.add_handler(CommandHandler("import", download_data))
    dp.add_handler(CommandHandler("export", upload_data))

    threading.Thread(
        target=subscription_worker,
        daemon=True
    ).start()

    logging.info("Bot started")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()