import logging
import main.data.orm as orm
import telegram
import sqlalchemy.orm

from sqlalchemy.sql import exists
from telegram import ParseMode

logger = logging.getLogger(__name__)

# Subscribe to subscription service
def start(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id

    if not orm.user_exists(session, chat_id):
        # add user
        logger.info(f"Adding new user {chat_id}")
        chat = orm.Chat(chat_id = chat_id)
        session.add(chat)
        session.commit()
        # notify user
        logger.debug(f"Replying to command /start from {chat_id}")
        context.bot.send_message(chat_id=chat_id, text="I'm the newsfeed bot. I can help you keep track of the information flow. Enter /help to see a list of all available commands.")
    else:
        logger.debug(f"Already registered user {chat_id} issued /start")

# Unsubscribe from subscription service
def stop(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id
    
    if orm.user_exists(session, chat_id):
        # remove user
        logger.info(f"Removing user {chat_id}")
        chat = session.query(orm.Chat).filter(orm.Chat.chat_id == chat_id).all()[0]
        session.delete(chat)
        session.commit()

        #notify user
        logger.debug(f"Replying to command /stop from {chat_id}")
        context.bot.send_message(chat_id=chat_id, text="I have deleted all your feed subscriptions and won't be messaging you anymore. If you want to register again, just message /start again.")
    else:
        logger.debug(f"Not registered user {chat_id} issued /stop")    

# def feeds(update : telegram.ext.Update, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
#     chat_id = update.effective_chat.id

#     if orm.user_exists(session, chat_id):
#         # remove user
#         logger.debug(f"Showing feeds for user {chat_id}")
#     pass # TODO

def subscribe(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id

    if orm.user_exists(session, chat_id):
        # parse query
        message_split = update.message.text.split(" ")
        if len(message_split) != 2:
            logger.debug(f"Missing argument for /subscribe by user {chat_id}")
            context.bot.send_message(chat_id=chat_id, text="*Wrong syntax*: Please enter the command like \n\n /subscribe <url>", parse_mode=ParseMode.MARKDOWN)
        else:
            feed_url = message_split[1]
            # check if feed is already known 
            if not orm.feed_exists(session, feed_url):
                feed = orm.Feed(link = feed_url)
                session.add(feed)

            feed = session.query(orm.Feed).filter(orm.Feed.link == feed_url).all()[0]
            chat = session.query(orm.Chat).filter(orm.Chat.chat_id == chat_id)[0]

            # check if chat has already subscribed
            if feed in chat.feeds:
                logger.debug(f"User {chat_id} is already subscribed to feed {feed.link}")
                context.bot.send_message(chat_id=chat_id, text=f"You are already subscribed to {feed.link}")
            else:
                # Add feed to chat
                chat.feeds.append(feed)
                session.commit()

                logger.info(f"User {chat_id} has subscribed to feed {feed.link}")
                context.bot.send_message(chat_id=chat_id, text=f"I will now notify you on new activity from {feed.link}")

def help(update : telegram.ext.Updater, context : telegram.ext.CallbackContext):
    logging.getLogger(__name__).debug("Replying to comment /help")
    help_string = """
    You may use the following services:
    
    *Bot Administration*
    /start - register for feed subscription
    /stop - unregister from feed subscription
    /help - show this help

    *Managment*
    /feeds - list all feeds you are subscribed to
    /subscribe <url> - subscribe to a feed
    /unsubscribe <url> - unsubscribe from a feed

    *Feedback*
    /bug <message> - report bugs and other inconveniences
    /canyou <message> - feature requests and improvements
    """
    context.bot.send_message(chat_id = update.effective_chat.id, text = help_string, parse_mode = ParseMode.MARKDOWN)