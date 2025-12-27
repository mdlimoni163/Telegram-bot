import datetime
import time
import logging
import pickle  # For automatic data saving and loading (persistence)
import os      # For handling temporary files
import io      # ✅ FIX: Needed for in-memory file handling (BytesIO)

from telegram import Bot
from telegram.ext import CommandHandler, Updater

# ========= CONFIG =========
# NOTE: Replace 'YOUR_BOT_TOKEN' with your actual bot token.
TOKEN = "8246711932:AAGN1raJxfSH8Qf2_Rx4ECyJmrgMIfXYifA"
ADMIN_ID = 6999604701
CHANNEL_ID = -1003075312230
INVITE_LINK = "https://t.me/+9e5QtDXXc9U4NDM1"
DATA_FILE = "subscribers.pkl"  # The file for automatic persistence
# ==========================

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

bot = Bot(token=TOKEN)

# ---------- Data Persistence Functions (Automatic Import/Export) ----------

def load_data():
    """IMPORTS/Loads the subscribers dictionary from the persistent pickle file."""
    try:
        # 'rb' means read binary
        with open(DATA_FILE, 'rb') as f:
            data = pickle.load(f)
            logging.info("✅ Subscribers data loaded successfully (Automatic Import).")
            return data
    except FileNotFoundError:
        logging.warning("⚠️ Data file not found. Starting with an empty list.")
        return {}
    except Exception as e:
        logging.error(f"❌ Error loading data: {e}. Starting with an empty list.")
        return {}

def save_data(data):
    """EXPORTS/Saves the subscribers dictionary to the persistent pickle file."""
    try:
        # 'wb' means write binary
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(data, f)
        logging.info("✅ Subscribers data saved successfully (Automatic Export).")
    except Exception as e:
        logging.error(f"❌ Error saving data: {e}")

# Load data when the bot starts (The actual "Import" action)
subscribers = load_data() 

# ---------- Command Handlers ----------

def start(update, context):
    update.message.reply_text("👋 Welcome! Please contact admin to start your subscription.")

def add_user(update, context):
    global subscribers 
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    if len(context.args) < 2:
        update.message.reply_text("⚠️ Usage: /add_user <user_id> <days>")
        return

    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
        subscribers[user_id] = expiry_date
        
        save_data(subscribers)  # ✅ Automatic Export after modification
        
        bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ Access granted for {days} days.\n"
                f"Expires on: {expiry_date.date()}\n\n"
                f"Join the channel:\n{INVITE_LINK}"
            )
        )

        update.message.reply_text(
            f"✅ User {user_id} added for {days} days (till {expiry_date.date()})."
        )
    except Exception as e:
        update.message.reply_text(f"⚠️ Error: {e}")

# ---------- Manual Backup/Restore Commands ----------

def download_data(update, context):
    """/import command: Generates a text file of all subscribers for download (Manual Export)."""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    if not subscribers:
        update.message.reply_text("ℹ️ No active VIP users to export.")
        return

    # 1. Prepare the text content (Format: user_id|YYYY-MM-DD HH:MM:SS)
    data_lines = [
        f"{user_id}|{expiry.strftime('%Y-%m-%d %H:%M:%S')}" 
        for user_id, expiry in subscribers.items()
    ]

    content = "\n".join(data_lines)
    filename = "subscribers_export.txt"

    # 2. Save content to a temporary file
    try:
        with open(filename, 'w') as f:
            f.write(content)
        
        # 3. Send the file to the admin
        with open(filename, 'rb') as f:
            update.message.reply_document(
                document=f,
                caption="✅ Your subscription data is ready for download. Reply to this file with /export to restore it later."
            )
        
        # 4. Clean up the temporary file
        os.remove(filename)

    except Exception as e:
        update.message.reply_text(f"❌ Error creating or sending export file: {e}")

def upload_data(update, context):
    """/export command: Loads a text file uploaded by admin (Manual Import/Restore)."""
    global subscribers

    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    # Check if the command is a reply to a document
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        update.message.reply_text("⚠️ Please /export by replying to the uploaded `subscribers_export.txt` file.")
        return

    document = update.message.reply_to_message.document

    # Basic check to ensure it's a text file
    if not document.file_name.lower().endswith('.txt'):
        update.message.reply_text("❌ The file must be a `.txt` file.")
        return

    try:
        # 1. Download the file using an in-memory buffer (the fix!)
        file_id = document.file_id
        new_file = bot.get_file(file_id)
        
        # Create an in-memory binary stream
        buffer = io.BytesIO()
        new_file.download(out=buffer)
        
        # Move the pointer to the beginning of the stream and read the content
        buffer.seek(0) 
        content_str = buffer.read().decode('utf-8')

        new_subscribers = {}
        successful_imports = 0

        # 2. Process the content line by line
        for line in content_str.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            try:
                # Expect format: user_id|YYYY-MM-DD HH:MM:SS
                user_id_str, expiry_str = line.split('|')
                
                user_id = int(user_id_str.strip())
                # Convert the string back to a datetime object
                expiry_date = datetime.datetime.strptime(expiry_str.strip(), '%Y-%m-%d %H:%M:%S')
                
                new_subscribers[user_id] = expiry_date
                successful_imports += 1
            except Exception as e:
                logging.error(f"Error parsing line '{line}': {e}")
                
        # 3. Merge the data and save it persistently
        subscribers.update(new_subscribers) 
        save_data(subscribers) # Save to the subscribers.pkl file

        update.message.reply_text(
            f"✅ Data successfully imported! Loaded {successful_imports} subscriptions. "
            f"Total active users: {len(subscribers)}."
        )

    except Exception as e:
        update.message.reply_text(f"❌ An unexpected error occurred during import: {e}")

# ---------- Subscription check ----------

def check_subscriptions():
    now = datetime.datetime.now()
    data_changed = False # Flag to track if we removed any user
    
    # Use list() to iterate over a copy, allowing modification of the original dict
    for user_id, expiry in list(subscribers.items()):
        if now > expiry:
            try:
                bot.ban_chat_member(CHANNEL_ID, user_id)
                del subscribers[user_id]
                logging.info(f"Removed expired user {user_id}")
                data_changed = True 
            except Exception as e:
                logging.error(f"Error removing {user_id}: {e}")
                
    if data_changed:
        save_data(subscribers) # ✅ Automatic Export if a user was removed

# ---------- Main run ----------

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add_user", add_user))
    
    # New Manual Import/Export Commands
    dp.add_handler(CommandHandler("import", download_data))  # /import = Download TXT
    dp.add_handler(CommandHandler("export", upload_data))    # /export = Upload/Restore TXT

    logging.info("✅ Bot started successfully!")

    updater.start_polling()

    # The check runs every 3600 seconds (1 hour)
    while True:
        check_subscriptions()
        time.sleep(3600)

if __name__ == "__main__":
    main()
