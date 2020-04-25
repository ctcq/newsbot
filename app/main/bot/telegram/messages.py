import logging
import sqlalchemy.orm
import telegram.ext

from telegram import ParseMode

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def handle_voice(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id
    voice_file = f"/tmp/{chat_id}.oga"
    wav_file = f"/tmp/{chat_id}.wav"
    context.bot.getFile(update.message.voice.file_id).download(voice_file)

    if wav_file:
        logger.info(f"Handling voice from chat {chat_id}")

        # Recognize audio from audiofile
        
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)