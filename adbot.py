#! /usr/bin/env python3
import logging
import handler
import argparse
import config
import errno
import os
from params import *
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update


reply_keyboard = [
    ["Age", "Favourite colour"],
    ["Number of siblings", "Something else..."],
    ["Done"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def resolve_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    # set higher logging level for httpx to avoid all GET and POST requests being logged
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)


def main():
    resolve_args()

    os.chdir(os.path.split(os.path.abspath(__file__))[0])

    try:
        os.mkdir(config.CACHE_DIR)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="conversationbot")
    application = (
        Application.builder().token(config.BOT_TOKEN).persistence(persistence).build()
    )

    # Add conversation handler with the states CHOOSING, CONFIRMATION and SEND_IMAGE
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", handler.start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex(r"" + NEW_AD), handler.adChoice),
                CommandHandler("start", handler.start),

            ],
            SEND_IMAGE: [
                MessageHandler(
                    filters.Regex(r"" + CANCEL),
                    handler.cancelOperation,
                ),
                MessageHandler(
                    filters.PHOTO & ~(filters.COMMAND | filters.Regex("^Done$")),
                    handler.receivedImage,
                ),
            ],
            SEND_TEXT: [
                MessageHandler(
                    filters.TEXT,
                    handler.receivedText,
                )
            ],
            CONFIRMATION: [
                MessageHandler(
                    filters.Regex(r"" + CANCEL),
                    handler.cancelOperation,
                ),
                MessageHandler(
                    filters.Regex(r"" + CONFIRM),
                    handler.confirmOperation,
                ),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), handler.done)],
        name="my_conversation",
        persistent=True,
    )

    application.add_handler(conv_handler)
    show_data_handler = CommandHandler("show_data", handler.show_data)
    application.add_handler(show_data_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
