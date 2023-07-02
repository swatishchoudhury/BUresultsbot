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
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """<b><i>To get marksheet:</i></b>
Send roll number in this format: <code>batch semester rollno.</code>
Example: <code>2020-23 1ST SV2121***</code>

<b><i>To get gradesheet:</i></b>
Send roll number in this format: <code>/grade batch rollno.</code>
Example: <code>/grade 2020-23 SV2121***</code>

Source Code: https://github.com/swatishchoudhury/BUresultsbot""",
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML,
    )


folder = ".temp"


async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        text = text.upper()
        msg = text.split(" ")

        batch_bytes = msg[0].encode("ascii")
        base64_bytes = base64.b64encode(batch_bytes)
        batch = base64_bytes.decode("ascii")

        sem_bytes = msg[1].encode("ascii")
        base64_bytes = base64.b64encode(sem_bytes)
        sem = base64_bytes.decode("ascii")

        roll_bytes = msg[2].encode("ascii")
        base64_bytes = base64.b64encode(roll_bytes)
        roll = base64_bytes.decode("ascii")

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

        await update.message.reply_text(
            table_data, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )

        pdfurl = (
            "https://berhampuruniversity.silicontechlab.com/buerp/build/examination/mark_sheet_pdf.php?regn_no="
            + roll
            + "&sem="
            + sem
            + "&batch="
            + batch
            + "&cmbType=Regular"
        )
        chat_id = update.effective_message.chat_id

        if not os.path.exists(folder):
            os.makedirs(folder)
        response = requests.get(pdfurl)
        if response.status_code == 200:
            filename = os.path.join(f"./{folder}", f"{msg[2]}.pdf")
            with open(filename, "wb") as file:
                file.write(response.content)
        else:
            await update.message("Unable to send pdf.")
            return
        await context.bot.send_document(
            document=open(f"./{folder}/{msg[2]}.pdf", "rb"), chat_id=chat_id
        )
        files = os.listdir(f"./{folder}")
        for file in files:
            os.remove(f"./{folder}/{file}")
        os.rmdir(f"./{folder}")
    except IndexError:
        await update.message.reply_text(
            """Error! Please ensure that you are sending the query in the correct format:
<code>batch semester rollno.</code>
Example: <code>2020-23 1ST SV2121***</code>
            """,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await update.message.reply_text(
            "Error! Probably the result server is acting up!"
        )


async def gradesheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            """Error! Please ensure that you are sending the query in the correct format:
<code>/grade batch rollno.</code>
Example: <code>/grade 2020-23 SV2121***</code>
            """,
            parse_mode=ParseMode.HTML,
        )
        return
    try:
        batch_bytes = args[0].encode("ascii")
        base64_bytes = base64.b64encode(batch_bytes)
        batch = base64_bytes.decode("ascii")

        roll_bytes = args[1].encode("ascii")
        base64_bytes = base64.b64encode(roll_bytes)
        roll = base64_bytes.decode("ascii")

        pdfurl = f"https://berhampuruniversity.silicontechlab.com/buerp/build/examination/final_grad_sheet_pdf.php?roll={roll}&batch={batch}"

        chat_id = update.effective_message.chat_id

        if not os.path.exists(folder):
            os.makedirs(folder)
        response = requests.get(pdfurl)
        if response.status_code == 200:
            filename = os.path.join(f"./{folder}", f"{args[1]}.pdf")
            with open(filename, "wb") as file:
                file.write(response.content)
        else:
            await update.message("Unable to send pdf.")
            return
        await context.bot.send_document(
            document=open(f"./{folder}/{args[1]}.pdf", "rb"), chat_id=chat_id
        )
        files = os.listdir(f"./{folder}")
        for file in files:
            os.remove(f"./{folder}/{file}")
        os.rmdir(f"./{folder}")
    except IndexError:
        await update.message.reply_text(
            """Error! Please ensure that you are sending the query in the correct format:
<code>batch semester rollno.</code>
Example: <code>/grade 2020-23 SV2121***</code>
            """,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await update.message.reply_text(
            "Error! Probably the result server is acting up!"
        )


def main():
    application = Application.builder().token(token=os.environ.get("BOT_API")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("grade", gradesheet))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, result))

    application.run_polling()


if __name__ == "__main__":
    main()
