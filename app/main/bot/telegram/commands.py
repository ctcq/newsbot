import logging
import feedparser
import main.data.orm as orm
import main.visitors.rss as rss
import telegram
import sqlalchemy.orm
import wikipedia
import requests

from io import BytesIO
from PIL import Image
from sqlalchemy.sql import exists
from telegram import ParseMode
from time import time

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

def rimg(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id
    args = update.message.text.split(' ')
    if len(args) > 1:
        random_string = ''.join(args[1:])
    else:
        random_string = time()


    api_url = f"https://gitlab.com/api/v4/avatar?email={random_string}"
    logger.info(f"Getting random image data from {api_url}")

    response = requests.get(api_url, params={'email' : random_string})
    response_json = response.json()
    img_url = response_json['avatar_url']
    logger.debug(f"Image url {img_url}")
    # response = requests.get(img_url)
    # img = Image.open(BytesIO(response.content))
    context.bot.send_photo(chat_id=chat_id, photo=img_url)

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

# convenience command for subscribing to youtube channel / user rss feed
def youtube(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id

    # check if user exists
    if (chat := orm.user_exists(session, chat_id)):
        # parse query
        message_split = update.message.text.split(" ")
        if len(message_split) != 3 or message_split[1] not in ['user', 'channel', 'playlist']:
            logger.debug(f"Invalid number of arguments for /youtube by user {chat_id}")
            context.bot.send_message(chat_id=chat_id, text="*Wrong syntax*: Please enter the command like:\n /youtube <channel | user | playlist> <id>", parse_mode=ParseMode.MARKDOWN)
        else:
            # build a /subscribe request for the url associated with the given youtube entity
            scope = message_split[1]

            if scope in ['channel', 'playlist']:
                scope += "_id"

            id = message_split[2]
            url = f"https://www.youtube.com/feeds/videos.xml?{scope}={id}"
            logger.debug(f"User {chat_id} subscribing to youtube {scope} with id {id}")
            update.message.text = f"/subscribe {url}"
            subscribe(update = update, context=context, session=session)

def unsubscribe(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id

    # check if user exists
    if (chat := orm.user_exists(session, chat_id)):
        # parse query
        message_split = update.message.text.split(" ")
        if len(message_split) != 2:
            logger.debug(f"Missing argument for /subscribe by user {chat_id}")
            context.bot.send_message(chat_id=chat_id, text="*Wrong syntax*: Please enter the command like:\n /unsubscribe <url>", parse_mode=ParseMode.MARKDOWN)
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

def reminder(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id

    # check if user exists
    if (chat := orm.user_exists(session, chat_id)):
        logger.debug(f"Listing reminders for user {chat_id}")
        if len(chat.reminders) == 0:
            context.bot.send_message(chat_id=chat_id, text = "You don't have any reminders set.\nEnter /remind to add one.")
            return
        else:
            message_text = "You have set the following reminders:\n"
            for reminder in chat.reminders:
                message_text += f"{reminder.get_markdown()}\n"
            context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode=ParseMode.MARKDOWN)
    else:
        logger.debug(f"Unregistered user {chat_id} issued /reminder")
        return

def trackings(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id

    if (chat:= orm.user_exists(session, chat_id)):
        logger.debug(f"Listing trackings for user {chat_id}")
        if len(chat.trackings) == 0:
            context.bot.send_message(chat_id=chat_id, text="You don't have any data trackings registered.")
            return
        else:
            message_text = "You have set data trackings for the following urls:\n"
            for tracking in chat.trackings:
                message_text += f"{tracking}\n"
            context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode=ParseMode.MARKDOWN)
    else:
        logger.debug(f"Unregistered user {chat_id}, issued /trackings")
        return

def untrack(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    chat_id = update.effective_chat.id
    tracking_title = update.message.text.split(" ")[1]
    if (chat:= orm.user_exists(session, chat_id)):
        logger.debug(f"Deleting tracking {tracking_title} for {chat_id}")
        trackings = session.query(orm.Tracking).filter(orm.Tracking.title == tracking_title and orm.Tracking.user_id == chat.id).all()
        if (len(trackings) > 0):
            session.delete(trackings[0])
            session.commit()
            context.bot.send_message(chat_id=chat_id, text=f"I have deleted the tracking of {tracking_title}", parse_mode=ParseMode.MARKDOWN)
        else:
            context.bot.send_message(chat_id=chat_id, text=f"There are not trackings with the name *{tracking_title}*", parse_mode=ParseMode.MARKDOWN)
    else:
        logger.debug(f"Unregistered user {chat_id}, issued /untrack")
        return

def qwiki(update : telegram.ext.Updater, context : telegram.ext.CallbackContext):
    message = update.message.text
    message_split = message.split(" ")
    search_text = ''.join(message_split[1:])
    if len(message_split) < 2:
        logging.debug("User issued /qwiki with invalid syntax")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid syntax!\nYou need to supply a search time like this:\n/qwiki London")
        return
    else:
        logging.debug(f"User issued /qwiki with search term {message_split[0]}")
        results = wikipedia.search(search_text)
        message = ""
        for result in results:
            message += f"{result}\n"
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return

def wiki(update : telegram.ext.Updater, context : telegram.ext.CallbackContext, length : int):
    message = update.message.text
    message_split = message.split(" ")
    if (len(message_split) < 2):
        logging.debug("User issued /wiki with invalid syntax")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid syntax!\nYou need to supply a search time like this:\n/wiki London")
        return
    else:
        search_text = ''.join(message_split[1:])
        logging.debug(f"User issued /wiki with search term {search_text}")
        summary = wikipedia.summary(search_text, sentences=length)
        context.bot.send_message(chat_id=update.effective_chat.id, text=summary)
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
    /youtube channel <channel-id> - subscribe to a youtube channel
    /youtube user <username> - subscribe to a youtube user
    /youtube playlist <playlist-id> subscribe to a youtube playlist
    /unsubscribe <url> - unsubscribe from a feed

    /remind - Start the reminder dialog
    /reminder - List all reminders

    /qwiki <word> - Search wikipedia for the given word
    /wiki <word> - Show a wikipedia summary for a word

    /rimg <word> - Show a random graphic

    """
    context.bot.send_message(chat_id = update.effective_chat.id, text = help_string, parse_mode = ParseMode.MARKDOWN)