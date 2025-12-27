import os
import datetime
import pickle
import logging
import io

from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler

# ================= CONFIG =================

TOKEN = os.getenv("8246711932:AAHg0tVX7Z8MWEsAVTSaiM93m_XjrVqJ0Mo")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

    ADMIN_ID = 6999604701
    CHANNEL_ID = -1003075312230
    INVITE_LINK = "https://t.me/+9e5QtDXXc9U4NDM1"
    DATA_FILE = "subscribers.pkl"

    bot = Bot(token=TOKEN)
    app = Flask(__name__)

    logging.basicConfig(level=logging.INFO)

    # ============== DATA =====================

    def load_data():
        try:
                with open(DATA_FILE, "rb") as f:
                            return pickle.load(f)
                                except:
                                        return {}

                                        def save_data(data):
                                            with open(DATA_FILE, "wb") as f:
                                                    pickle.dump(data, f)

                                                    subscribers = load_data()

                                                    # ============== COMMANDS =================

                                                    def start(update, context):
                                                        update.message.reply_text(
                                                                    "Welcome!\nPlease contact admin to activate subscription."
                                                        )

                                                        def add_user(update, context):
                                                            if update.effective_user.id != ADMIN_ID:
                                                                    update.message.reply_text("Unauthorized")
                                                                            return

                                                                                if len(context.args) < 2:
                                                                                        update.message.reply_text("Usage: /add_user <user_id> <days>")
                                                                                                return

                                                                                                    user_id = int(context.args[0])
                                                                                                        days = int(context.args[1])
                                                                                                            expiry = datetime.datetime.now() + datetime.timedelta(days=days)

                                                                                                                subscribers[user_id] = expiry
                                                                                                                    save_data(subscribers)

                                                                                                                        bot.send_message(
                                                                                                                                    user_id,
                                                                                                                                            f"Access granted for {days} days\n"
                                                                                                                                                    f"Expires: {expiry.date()}\n\n"
                                                                                                                                                            f"Join channel:\n{INVITE_LINK}"
                                                                                                                        )

                                                                                                                            update.message.reply_text("User added successfully")

                                                                                                                            def export_data(update, context):
                                                                                                                                if update.effective_user.id != ADMIN_ID:
                                                                                                                                        return

                                                                                                                                            lines = [
                                                                                                                                                        f"{uid}|{exp.strftime('%Y-%m-%d %H:%M:%S')}"
                                                                                                                                                                for uid, exp in subscribers.items()
                                                                                                                                            ]

                                                                                                                                                content = "\n".join(lines)
                                                                                                                                                    bio = io.BytesIO(content.encode())
                                                                                                                                                        bio.name = "subscribers.txt"

                                                                                                                                                            update.message.reply_document(bio)

                                                                                                                                                            # ============== DISPATCHER ===============

                                                                                                                                                            dispatcher = Dispatcher(bot, None, workers=0)

                                                                                                                                                            dispatcher.add_handler(CommandHandler("start", start))
                                                                                                                                                            dispatcher.add_handler(CommandHandler("add_user", add_user))
                                                                                                                                                            dispatcher.add_handler(CommandHandler("export", export_data))

                                                                                                                                                            # ============== WEBHOOK ==================

                                                                                                                                                            @app.route("/", methods=["POST"])
                                                                                                                                                            def webhook():
                                                                                                                                                                update = Update.de_json(request.get_json(force=True), bot)
                                                                                                                                                                    dispatcher.process_update(update)
                                                                                                                                                                        return "OK"

                                                                                                                                                                        @app.route("/", methods=["GET"])
                                                                                                                                                                        def index():
                                                                                                                                                                            return "Bot is running"

                                                                                                                                                                            # ============== START ====================

                                                                                                                                                                            if __name__ == "__main__":
                                                                                                                                                                                PORT = int(os.environ.get("PORT", 10000))
                                                                                                                                                                                    bot.set_webhook(
                                                                                                                                                                                                url=os.environ.get("RENDER_EXTERNAL_URL")
                                                                                                                                                                                    )
                                                                                                                                                                                        app.run(host="0.0.0.0", port=PORT)
                                                                                                                                                                                    )
                                                                                                                                            ]
                                                                                                                        )
                                                        )