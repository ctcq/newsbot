import logging
import main.data.orm as orm
import parsedatetime
import sqlalchemy
import telegram

from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Filters
from pytz import timezone

logger = logging.getLogger(__name__)
TITLE, TIMESTAMP, CONFIRM_DATE = range(3)       

class ReminderConversation():

    def __init__(self, session : sqlalchemy.orm.Session):
        self.session = session
        self.message = ""
        self.date_string = ""
        self.datetime = ""
        self.chat = None

    def get_conv_handler(self, session : sqlalchemy.orm.Session):
        conv_handler = ConversationHandler(
            entry_points = [CommandHandler('remind', self.start)],
            states = {
                TITLE : [MessageHandler(Filters.regex("^[^/]"), self.timestamp)],
                TIMESTAMP : [MessageHandler(Filters.regex("^[^/]"), self.confirm_date)],
                CONFIRM_DATE : [MessageHandler(Filters.regex("^[YyNn]$"), self.confirm_date_response)]     
            },
            fallbacks = [CommandHandler('cancel', self.cancel)]
        )

        return conv_handler

    def start(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        self.chat = orm.user_exists(self.session, updater.effective_chat.id)
        logger.debug("User is answering to message inquiry...")
        updater.message.reply_text("I will ask you for some details on the reminder.\nSend /cancel to stop this.\nWhat should I remind you about?")
        return TITLE

    def timestamp(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        self.message = updater.message.text
        logger.debug(f"Title is {self.message}.")
        updater.message.reply_text("When should I remind you?")
        return TIMESTAMP

    def confirm_date(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        self.date_string = updater.message.text
        cal = parsedatetime.Calendar()
        self.datetime = cal.parseDT(datetimeString=self.date_string, tzinfo=timezone(self.chat.timezone))[0]
        logger.debug(f"Given string was {self.datetime}.")
        updater.message.reply_text(f"You want to be reminded of\n{self.message}\non {self.datetime},\nright? (Y/N)")
        return CONFIRM_DATE

    def confirm_date_response(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        confirm_response = updater.message.text
        logger.debug(f"Given response for confirm date was {confirm_response}")
        if confirm_response.lower() == "y":
            reminder = orm.Reminder(message = self.message, timestamp = self.datetime.timestamp())
            self.chat.reminders.append(reminder)
            self.session.commit()
            logger.debug(f"Set timestamp reminder for user {self.chat.chat_id} to {self.datetime}")
            updater.message.reply_text(f"I've set a reminder about\n{self.message}\nfor\n{self.datetime}")
        else:
            logger.debug(f"User {self.chat.chat_id} did not finally approve the reminder.")
            updater.message.reply_text(f"Okay. I won't save any reminder.")
        return ConversationHandler.END
    
    def cancel(self, updater : telegram.ext.Updater, context : telegram.ext.CallbackContext):
        logging.debug("User canceled /reminder")
        updater.message.reply_text("Alright, I won't set a reminder for you.")
        return ConversationHandler.END