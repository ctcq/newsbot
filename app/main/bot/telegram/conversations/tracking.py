import json
import logging
import requests
import sqlalchemy
import telegram
from telegram import ParseMode
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters
import main.data.orm as orm

# Response constants
TITLE, URL, VALIDATE = range(3)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class TrackingConversation():

    def __init__(self, session : sqlalchemy.orm.Session):
        self.title = None
        self.link = None
        self.session = session

    def get_conv_handler(self, session : sqlalchemy.orm.Session):
        conv_handler = ConversationHandler(
            entry_points = [CommandHandler('track', lambda updater, context : self.start_conv(updater, context))],
            states = {
                TITLE : [MessageHandler(Filters.regex("^[^/]"), self.title_conv)],
                VALIDATE : [MessageHandler(Filters.regex("^[^/]"), self.validate_conv)]
            },
            fallbacks = [CommandHandler('cancel', self.cancel)]
        )

        return conv_handler

    def start_conv(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        updater.message.reply_text("What is the title of that tracking?")
        return TITLE

    def title_conv(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        self.title = updater.message.text
        updater.message.reply_text(r"What is the URL of the API? If an api key is nescessary, fill replace it with {KEY}")
        return VALIDATE

    def validate_conv(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        self.link = updater.message.text
        try :
            # check if the link contains valid json
            logger.debug(f"Sending request to {self.link}")
            data = requests.get(self.link)
            json.loads(data.content)

            # persists the tracker
            chat = orm.user_exists(self.session, updater.effective_chat.id)
            tracking = orm.Tracking(self.title, self.link, chat.id)
            self.session.add(tracking)
            self.session.commit()

            updater.message.reply_text(f"Tracking for\n{self.title}\n hast been added.")
        except json.JSONDecodeError:
            logger.debug("/track aborted due to invalid json")
            updater.message.reply_text("Sorry, the api doesn't provide valid json data.")
        except requests.exceptions.MissingSchema:
            logger.debug("/track aborted due to invalid url")
            updater.message.reply_text("Sorry, the given URL is invalid.")

    def cancel(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        logging.debug("User canceled set_timezone")
        updater.message.reply_text("Alright, I won't save any tracking.")
        return ConversationHandler.END

    def error(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        logger.warning(f"Update {updater} cause error {context.error}", updater, context.error)