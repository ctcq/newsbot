import json
import logging
import sqlalchemy.orm
import telegram.ext
from main.visitors.voice import SpeechParser 

from telegram import ParseMode

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

with open('/resources/config/config.json') as file:
    config = json.load(file)

def handle_voice(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id
    voice_file = f"/tmp/{chat_id}.oga"
    wav_file = f"/tmp/{chat_id}.wav"
    context.bot.getFile(update.message.voice.file_id).download(voice_file)

    # init parser
    parser = SpeechParser(engine = config['text_to_speech_engine'])
    # convert to wav
    parser.to_wav(voice_file)
    # parse speech
    result = parser.parse(wav_file)

    context.bot.send_message(chat_id=chat_id, text=result, parse_mode=ParseMode.MARKDOWN)