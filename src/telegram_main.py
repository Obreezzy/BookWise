import asyncio
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.error import NetworkError
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from bot import handle_photo, handle_text
from db import connect
from extract import extract_receipt
from send_day import local_send_date

load_dotenv()

INCOMING = "incoming"
BUSY = "I can't read photos right now. Please try again later."
DOWNLOAD_FAILED = "I could not download that photo. Please send it again."
WAIT = 30  # seconds to wait for Telegram before giving up


def business_id_for(user_id):
    return f"tg_{user_id}"


async def with_retry(step, action, tries=3):
    """Run an async action, retrying when the network to Telegram times out."""
    for attempt in range(1, tries + 1):
        try:
            return await action()
        except NetworkError as e:  # TimedOut is a kind of NetworkError
            print(f"{step}: {type(e).__name__} (try {attempt} of {tries})")
            if attempt == tries:
                raise
            await asyncio.sleep(2)


def read_photo(business_id, user_id, image_path, sent_on):
    # A new database connection per job: SQLite connections
    # cannot be shared between threads.
    conn = connect()
    try:
        return handle_photo(conn, business_id, user_id, image_path,
                            sent_on, extract_receipt)
    finally:
        conn.close()


def read_text(business_id, user_id, text):
    conn = connect()
    try:
        return handle_text(conn, business_id, user_id, text)
    finally:
        conn.close()


async def send_reply(message, text):
    try:
        await with_retry("reply", lambda: message.reply_text(text))
    except Exception as e:
        print("reply failed:", type(e).__name__)


async def on_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_reply(
        update.message,
        "Hello! Send me a photo of a receipt. I will read it and ask "
        "you to check it.")


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id

    if message.photo:
        file_id = message.photo[-1].file_id  # the largest size
        ext = ".jpg"
    else:  # the photo was sent "as file"
        file_id = message.document.file_id
        ext = ".png" if message.document.mime_type == "image/png" else ".jpg"

    os.makedirs(INCOMING, exist_ok=True)
    image_path = os.path.join(INCOMING, f"{user_id}_{message.message_id}{ext}")

    stage = "notice"
    try:
        # The notice is nice to have. If it fails, carry on.
        try:
            await message.reply_text("Reading your receipt, this takes a few seconds...")
        except NetworkError as e:
            print("notice failed:", type(e).__name__)

        stage = "download"

        async def fetch():
            tg_file = await context.bot.get_file(file_id)
            await tg_file.download_to_drive(image_path)

        await with_retry("download", fetch)

        stage = "read"
        sent_on = local_send_date(message.date)
        # The model call is slow, so run it off the main loop.
        reply = await asyncio.to_thread(
            read_photo, business_id_for(user_id), user_id, image_path, sent_on)
    except Exception as e:
        # Print only the type, never the full message, in case it has the token.
        print(f"photo failed at {stage}:", type(e).__name__)
        reply = DOWNLOAD_FAILED if stage == "download" else BUSY

    await send_reply(message, reply)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id
    reply = read_text(business_id_for(user_id), user_id, message.text)
    await send_reply(message, reply)


def main():
    app = (
        Application.builder()
        .token(os.environ["TELEGRAM_TOKEN"])
        .connect_timeout(WAIT)
        .read_timeout(WAIT)
        .write_timeout(WAIT)
        .pool_timeout(WAIT)
        .get_updates_connect_timeout(WAIT)
        .get_updates_read_timeout(WAIT)
        .get_updates_write_timeout(WAIT)
        .get_updates_pool_timeout(WAIT)
        .build()
    )
    app.add_handler(CommandHandler("start", on_start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    print("Bot is running. Press Ctrl+C to stop.")
    # bootstrap_retries=5: if the first connection to Telegram fails,
    # try again up to 5 times instead of quitting.
    app.run_polling(bootstrap_retries=5)


if __name__ == "__main__":
    main()