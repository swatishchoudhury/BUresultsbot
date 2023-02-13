import os
import requests
from bs4 import BeautifulSoup
import base64

from telegram import (
    Update,
    WebAppInfo,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    Application,
    ApplicationBuilder,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """Send roll number in this format: `<batch> <semester> <roll no\.>`
Example: `2020-23 1ST SV2121***`

Source: https://github\.com/swatishchoudhury/BUresultsbot""",
        disable_web_page_preview=True,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        text = text.upper()
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

        pdfurl = (
            "https://berhampuruniversity.silicontechlab.com/buerp/build/examination/mark_sheet_pdf.php?regn_no="
            + base642_text
            + "&sem="
            + base641_text
            + "&batch="
            + base640_text
            + "&cmbType=Regular"
        )
        weburl = (
            "https://berhampuruniversity.silicontechlab.com/buerp/build/examination/mark_sheet_db.php?type=GET_DETAILS&regn_no="
            + msg[2]
            + "&sem="
            + msg[1]
            + "&batch="
            + msg[0]
            + "&cmbType=Regular"
        )
        keyboard = [
            [
                InlineKeyboardButton(
                    "Results",
                    web_app=WebAppInfo(weburl),
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        url = weburl
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table")

        table_data = ""
        for row in table.find_all("tr"):
            cells = [cell.text for cell in row.find_all("td")]
            table_data += "\t".join(cells) + "\n"

        # Send the table data as a single message
        await update.message.reply_text(
            table_data, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )
        await update.message.reply_document(document=pdfurl)

    except Exception as e:
        print(e)
        await update.message.reply_text("Error!")


def main():
    application = Application.builder().token(token=os.environ.get("BOT_API")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, pdf))

    application.run_polling()


if __name__ == "__main__":
    main()
