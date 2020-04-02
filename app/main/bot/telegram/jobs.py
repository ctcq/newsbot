import logging
import sqlalchemy
import telegram

from html2texttg import html2text
from telegram import ParseMode

import main.data.orm as orm
import main.visitors.rss as rss

"""
    This module contains callback functions as jobs
"""

logger = logging.getLogger(__name__)

def broadcast_new_rss_messages(context : telegram.ext.CallbackContext, engine : sqlalchemy.engine.Engine):
    # Iterate through all feeds and send messages to associated chats
    # Delete all orphan feeds you come across
    session = orm.get_session(engine)
    try:
        feeds = session.query(orm.Feed).all()
        logger.info(f"Broadcasting {len(feeds)} feeds...")
        for feed in feeds:
            # delete orphan feed
            if len(feed.chats) == 0:
                logger.info(f"Deleted orphan feed {feed}")
                session.delete(feed)
                continue
            else:
                # get new messages
                new_messages, last_message_hash = rss.get_new_messages(feed)

                # broadcast new messages to subscribed chats
                for message in new_messages:
                    text = f"*{feed.title}*\n[{message.title}]({message.link})"
                    logger.info(f"Broadcasting feed {feed.title} to {len(feed.chats)} chats...")      
                    for chat in feed.chats:
                        context.bot.send_message(chat_id=chat.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)

            logger.debug(f"Setting last_message_hash from {feed.last_message_hash} to {last_message_hash}")
            feed.last_message_hash = last_message_hash
            session.commit()
    finally:
        session.close()