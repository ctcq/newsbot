import logging
import feedparser
import main.data.orm as orm
import main.visitors.rss as rss
import telegram
import sqlalchemy.orm

from sqlalchemy.sql import exists
from telegram import ParseMode

logger = logging.getLogger(__name__)

# Subscribe to subscription service
def start(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id

    if not (chat := orm.user_exists(session, chat_id)):
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

            parsed_feed = feedparser.parse(feed_url)
            # check if feed is valid
            if not 'title' in parsed_feed.feed.keys() or len(parsed_feed.feed.keys()) == 0:
                logger.debug(f"User {chat_id} subsribed to invalid feed {feed_url}")
                context.bot.send_message(chat_id=chat_id, text=f"Sorry. It seems the url {feed_url} does not point to a valid rss feed.")
                return

            # check if feed is already known 
            if not (feed := orm.feed_exists(session, feed_url)):
                if len(parsed_feed.entries) > 1:
                    hash = rss.get_hash(parsed_feed.entries[1].title)
                elif len(parsed_feed) > 0:
                    hash = rss.get_hash(parsed_feed.entries[0].title)
                else:
                    hash = ""

                feed = orm.Feed(link = feed_url, title = parsed_feed.feed.title, last_message_hash=hash)
                session.add(feed)
            
            # fetch from db 
            feed = session.query(orm.Feed).filter(orm.Feed.link == feed_url).all()[0]
            chat = session.query(orm.Chat).filter(orm.Chat.chat_id == chat_id)[0]

            # check if chat has already subscribed
            if feed in chat.feeds:
                logger.debug(f"User {chat_id} is already subscribed to feed {feed.link}")
                context.bot.send_message(chat_id=chat_id, text=f"You are already subscribed to *{parsed_feed.feed.title}*", parse_mode=ParseMode.MARKDOWN)
            else:
                # Add feed to chat
                chat.feeds.append(feed)
                session.commit()

                logger.info(f"User {chat_id} has subscribed to feed {feed.link}")
                context.bot.send_message(chat_id=chat_id, text=f"I will now notify you on new activity from *{parsed_feed.feed.title}*", parse_mode=ParseMode.MARKDOWN)

def unsubscribe(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id

    # check if user exists
    if (chat := orm.user_exists(session, chat_id)):
        # parse query
        message_split = update.message.text.split(" ")
        if len(message_split) != 2:
            logger.debug(f"Missing argument for /subscribe by user {chat_id}")
            context.bot.send_message(chat_id=chat_id, text="*Wrong syntax*: Please enter the command like:\n /subscribe <url>", parse_mode=ParseMode.MARKDOWN)
        else:
            feed_url = message_split[1]
            # check if user is subscribed to feed
            if not (feed := orm.feed_exists(session, feed_url)) or not feed_url in [_feed.link for _feed in chat.feeds]:
                logger.debug(f"User {chat_id} issued /unsubscribe for untracked feed {feed_url}")
                context.bot.send_message(chat_id=chat_id, text=f"You are not subscribed to {feed_url}")
            else:
                context.bot.send_message(chat_id=chat_id, text=f"You will not recieve any updates from {feed.title}")
                chat.feeds.remove(feed)
                session.commit()

                # If feed has no more chats, remove the feed
                if len(feed.chats) == 0:
                    session.delete(feed) 

                logger.debug(f"User {chat_id} unsubscribed from {feed_url}")
    else:
        logger.debug(f"Not registered user {chat_id} issued /unsubscribe")    
        return

def feeds(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id

    # check if user exists
    if (chat := orm.user_exists(session, chat_id)):
        logger.debug(f"Listing subscribed feeds for user {chat_id}")

        if len(chat.feeds) == 0:
            context.bot.send_message(chat_id=chat_id, text = "You are not subscribed to any feeds. Enter /subscribe <url> to add one.")
            return
        else:
            message_text = "You are subscribed to the following feeds:\n"
            for feed in chat.feeds:
                message_text += f"[{feed.title}]({feed.link})\n"
            context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode=ParseMode.MARKDOWN)
    else:
        logger.debug(f"Unregistered user {chat_id} issued /feeds")
        return

def help(update : telegram.ext.Updater, context : telegram.ext.CallbackContext):
    logger.debug("Replying to command /help")
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