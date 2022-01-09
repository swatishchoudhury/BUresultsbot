import os
import base64

from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    Filters,
)


def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        """Format: <batch> <sem> <roll no.>
                              Eg: 2020-23 1ST SV2121***"""
    )


def pdf(update: Update, context: CallbackContext):
    text = update.message.text
    msg = text.split(" ")

    text0_bytes = msg[0].encode("ascii")
    base64_bytes = base64.b64encode(text0_bytes)
    base640_text = base64_bytes.decode("ascii")

    text1_bytes = msg[1].encode("ascii")
    base64_bytes = base64.b64encode(text1_bytes)
    base641_text = base64_bytes.decode("ascii")

    text2_bytes = msg[2].encode("ascii")
    base64_bytes = base64.b64encode(text2_bytes)
    base642_text = base64_bytes.decode("ascii")

    url = (
        "https://berhampuruniversity.silicontechlab.com/buerp/build/examination/mark_sheet_pdf.php?regn_no="
        + base642_text
        + "&sem="
        + base641_text
        + "&batch="
        + base640_text
        + "&cmbType=Regular"
    )
    update.message.reply_document(document=url)
    print("file sent")


def main():
    updater = Updater(token=os.environ["bot_api"])
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, pdf))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
