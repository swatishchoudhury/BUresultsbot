import os
import requests
from bs4 import BeautifulSoup
import base64
import logging
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


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

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


TEMP_FOLDER = ".temp"


def handle_request_error(error, error_type="request"):
    """Centralized error handling for requests"""
    if isinstance(error, requests.exceptions.SSLError):
        logger.warning(f"SSL certificate issue during {error_type}")
        return "SSL certificate error. The university server has certificate issues."
    elif isinstance(error, requests.exceptions.Timeout):
        logger.warning(f"Request timeout during {error_type}")
        return "Request timed out. The university server is responding slowly."
    else:
        logger.error(f"Request error during {error_type}: {error}")
        return f"Error fetching {error_type} data. Please try again later."


async def result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle marksheet requests."""
    try:
        text = update.message.text
        text = text.upper()
        msg = text.split(" ")
        
        if len(msg) < 3:
            raise IndexError("Not enough arguments")

        # For HTML URL - use plain text parameters
        batch_plain = msg[0]
        sem_plain = msg[1]
        roll_plain = msg[2]

        # For PDF URL - use base64 encoded parameters
        batch_bytes = msg[0].encode("ascii")
        base64_bytes = base64.b64encode(batch_bytes)
        batch_encoded = base64_bytes.decode("ascii")

        sem_bytes = msg[1].encode("ascii")
        base64_bytes = base64.b64encode(sem_bytes)
        sem_encoded = base64_bytes.decode("ascii")

        roll_bytes = msg[2].encode("ascii")
        base64_bytes = base64.b64encode(roll_bytes)
        roll_encoded = base64_bytes.decode("ascii")

        # HTML URL uses plain text parameters
        weburl = (
            "https://berhampuruniversity.silicontechlab.com/buerp/build/examination/mark_sheet_db.php"
            f"?type=GET_DETAILS&regn_no={roll_plain}&sem={sem_plain}&batch={batch_plain}&cmbType=Regular"
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
        
        try:
            response = requests.get(weburl, timeout=15, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            table = soup.find("table")
            if table:
                table_data = ""
                for row in table.find_all("tr"):
                    cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
                    if cells:
                        table_data += "\t".join(cells) + "\n"
                
                if table_data.strip():
                    await update.message.reply_text(
                        f"<pre>{table_data}</pre>", 
                        reply_markup=reply_markup, 
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await update.message.reply_text(
                        "No data found in the result table.",
                        reply_markup=reply_markup
                    )
            else:
                await update.message.reply_text(
                    "No result table found. Please check your details.",
                    reply_markup=reply_markup
                )
        except requests.RequestException as e:
            error_msg = handle_request_error(e, "result")
            await update.message.reply_text(error_msg, reply_markup=reply_markup)

        # Generate and send PDF - PDF URL uses base64 encoded parameters
        pdfurl = (
            "https://berhampuruniversity.silicontechlab.com/buerp/build/examination/mark_sheet_pdf.php"
            f"?regn_no={roll_encoded}&sem={sem_encoded}&batch={batch_encoded}&cmbType=Regular"
        )
        
        chat_id = update.effective_message.chat_id

        # Create temp folder if it doesn't exist
        if not os.path.exists(TEMP_FOLDER):
            os.makedirs(TEMP_FOLDER)
        
        try:
            response = requests.get(pdfurl, timeout=45, verify=False)
            response.raise_for_status()
            
            if response.content and len(response.content) > 100:  # Basic check for valid PDF
                filename = os.path.join(TEMP_FOLDER, f"{msg[2]}.pdf")
                with open(filename, "wb") as file:
                    file.write(response.content)
                
                # Send the PDF document
                with open(filename, "rb") as pdf_file:
                    await context.bot.send_document(
                        document=pdf_file,
                        chat_id=chat_id,
                        filename=f"marksheet_{msg[2]}.pdf"
                    )
            else:
                await update.message.reply_text("Unable to generate PDF. The result server may be unavailable.")
        except requests.RequestException as e:
            error_msg = handle_request_error(e, "PDF")
            await update.message.reply_text(error_msg)
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            await update.message.reply_text("Error processing PDF file.")
        finally:
            # Clean up temp files
            try:
                if os.path.exists(TEMP_FOLDER):
                    files = os.listdir(TEMP_FOLDER)
                    for file in files:
                        file_path = os.path.join(TEMP_FOLDER, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    if not os.listdir(TEMP_FOLDER):  # Remove folder if empty
                        os.rmdir(TEMP_FOLDER)
            except Exception as e:
                logger.warning(f"Error cleaning up temp files: {e}")

    except IndexError:
        await update.message.reply_text(
            """Error! Please ensure that you are sending the query in the correct format:
<code>batch semester rollno.</code>
Example: <code>2020-23 1ST SV2121***</code>""",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Unexpected error in result handler: {e}")
        await update.message.reply_text(
            "Error! Probably the result server is acting up!"
        )


async def gradesheet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle gradesheet requests."""
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            """Error! Please ensure that you are sending the query in the correct format:
<code>/grade batch rollno.</code>
Example: <code>/grade 2020-23 SV2121***</code>""",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        batch_bytes = args[0].encode("ascii")
        base64_bytes = base64.b64encode(batch_bytes)
        batch_encoded = base64_bytes.decode("ascii")

        roll_bytes = args[1].encode("ascii")
        base64_bytes = base64.b64encode(roll_bytes)
        roll_encoded = base64_bytes.decode("ascii")

        pdfurl = (
            "https://berhampuruniversity.silicontechlab.com/buerp/build/examination/final_grad_sheet_pdf.php"
            f"?roll={roll_encoded}&batch={batch_encoded}"
        )

        chat_id = update.effective_message.chat_id

        # Create temp folder if it doesn't exist
        if not os.path.exists(TEMP_FOLDER):
            os.makedirs(TEMP_FOLDER)
        
        try:
            response = requests.get(pdfurl, timeout=45, verify=False)
            response.raise_for_status()
            
            if response.content and len(response.content) > 100:
                filename = os.path.join(TEMP_FOLDER, f"{args[1]}.pdf")
                with open(filename, "wb") as file:
                    file.write(response.content)
                
                # Send the PDF document
                with open(filename, "rb") as pdf_file:
                    await context.bot.send_document(
                        document=pdf_file,
                        chat_id=chat_id,
                        filename=f"gradesheet_{args[1]}.pdf"
                    )
            else:
                await update.message.reply_text("Unable to generate PDF. The result server may be unavailable.")
        except requests.RequestException as e:
            error_msg = handle_request_error(e, "gradesheet PDF")
            await update.message.reply_text(error_msg)
        except Exception as e:
            logger.error(f"Error processing gradesheet PDF: {e}")
            await update.message.reply_text("Error processing gradesheet PDF file.")
        finally:
            # Clean up temp files
            try:
                if os.path.exists(TEMP_FOLDER):
                    files = os.listdir(TEMP_FOLDER)
                    for file in files:
                        file_path = os.path.join(TEMP_FOLDER, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    if not os.listdir(TEMP_FOLDER):  # Remove folder if empty
                        os.rmdir(TEMP_FOLDER)
            except Exception as e:
                logger.warning(f"Error cleaning up temp files: {e}")

    except IndexError:
        await update.message.reply_text(
            """Error! Please ensure that you are sending the query in the correct format:
<code>/grade batch rollno.</code>
Example: <code>/grade 2020-23 SV2121***</code>""",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.error(f"Unexpected error in gradesheet handler: {e}")
        await update.message.reply_text(
            "Error! Probably the result server is acting up!"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}")


def main() -> None:
    """Start the bot."""

    token = os.environ.get("BOT_API")
    if not token:
        print("Error: BOT_API environment variable is not set. Please copy .env.local to .env and set your BOT_API token.")
        return

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("grade", gradesheet))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, result))
    
    application.add_error_handler(error_handler)

    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()