import logging
import telegram
from html2texttg import html2text
import sqlalchemy.orm
from sqlalchemy.sql import exists
from telegram import ParseMode
import main.visitors.rss

"""
    This module contains callback functions as jobs
"""

def broadcast_welcome_job(context : telegram.ext.CallbackContext, session : sqlalchemy.orm.Session):
    logger = logging.getLogger(__name__)


    chat_ids = session.query(Chats)
    logger.info(f"Welcoming {len(chat_ids)} clients...")

    welcome_message = "*Hello*. I'm awake now!"

    for chat_id in chat_ids:
        context.bot.send_message(chat_id=chat_id, text=welcome_message, parse_mode = ParseMode.MARKDOWN)

def broadcast_rss_job(context : telegram.ext.CallbackContext, rss_subscriptions_visitor : main.visitors.rss.RssSubscriptionsVisitor):
    logger = logging.getLogger(__name__)
    
    # Look for new messages
    updated_rss_subscriptions, new_rss_messages = rss_subscriptions_visitor.visit()

    # Stop if no new messages are found
    if len(new_rss_messages) == 0:
        logger.info("broadcast_rss job finished")
        return

    # Get current chat ids to broadcast to
    chat_ids = chat_id_visitor.visit()
    if len(chat_ids) == 0:
        logger.warning("No chat ids found")

    # Broadcast rss messages        
    for chat_id in chat_ids:
        for msg in new_rss_messages:
            # Set proper format
            text = f"<b>{msg['title']}</b><p>{msg['description']}</p>"
            text = html2text(text)
            
            try:
                context.bot.send_message(chat_id = chat_id, text = text, parse_mode = ParseMode.MARKDOWN)
            except telegram.error.BadRequest:
                # If html has error, just send plainly formatted
                logger.warn(f"Bad message format in message {msg['title']}")
                context.bot.send_message(chat_id = chat_id, text = text)

    # Update rss file
    rss_subscriptions_visitor.persist_subscriptions(updated_rss_subscriptions)
    logger.info("broadcast_rss job finished")