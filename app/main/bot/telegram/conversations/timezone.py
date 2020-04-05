import logging
import pytz
import sqlalchemy
import telegram
from telegram import ParseMode
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters
import main.data.orm as orm

# Response constants
TIMEZONE = 0

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class TimezoneConversation():

    def get_conv_handler(self, session : sqlalchemy.orm.Session):
        conv_handler = ConversationHandler(
            entry_points = [CommandHandler('set_timezone', lambda updater, context : self.start(updater, context))],
            states = {
                TIMEZONE : [MessageHandler(Filters.regex("^[^/]"), lambda updater, context : self.check_and_update(updater, context, session))]
            },
            fallbacks = [CommandHandler('cancel', self.cancel)]
        )

        return conv_handler

    def start(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        updater.message.reply_text("Please enter your timezone.\nIt should look something like this:\nEurope/Berlin")
        return TIMEZONE

    def check_and_update(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
        message = updater.message.text
        if message in pytz.all_timezones:
            logger.debug(f"User changed timezone to valid timezone {message}")
            chat = orm.user_exists(session, updater.effective_chat.id)
            chat.timezone = message
            session.commit()
            message = updater.message.reply_text(f"I have set your timezone to\n{message}")
            return ConversationHandler.END
        else:
            logger.debug(f"User requested invalid timezone {message}")
            message = updater.message.reply_text("Sorry, I don't know that timezone.\nPlease enter another one or exit with /cancel")
            return TIMEZONE

    def cancel(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        logging.debug("User canceled set_timezone")
        updater.message.reply_text("Alright, your timezone will not be changed.")
        return ConversationHandler.END

    def error(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        logger.warning(f"Update {updater} cause error {context.error}", updater, context.error)