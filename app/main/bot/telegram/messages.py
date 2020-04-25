import logging
import sqlalchemy.orm
import speech_recognition as sr
import subprocess
import telegram.ext

from telegram import ParseMode

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def handle_voice(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id
    voice_file = f"/tmp/{chat_id}.oga"
    wav_file = f"/tmp/{chat_id}.wav"
    context.bot.getFile(update.message.voice.file_id).download(voice_file)

    # Convert to wav
    logger.info(f"Converting {voice_file} to {wav_file}...")
    subprocess.run(['ffmpeg', '-y', '-i', voice_file, wav_file])

    # Read voice file from telegram server
    logger.debug(f"Handling voice from {voice_file}")
    if wav_file:
        logger.info(f"Handling voice from chat {chat_id}")

        # Recognize audio from audiofile
        r = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            voice = r.record(source)  # read the entire audio file
        try:
            text = "I think you said " + r.recognize_sphinx(voice)
        except sr.UnknownValueError:
            text = "Sorry, I could not understand what you said."
        except sr.RequestError:
            text = "There was an error while trying to recognize what you said"

        context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)