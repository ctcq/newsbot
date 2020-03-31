import sqlalchemy
import sqlalchemy.orm
import telegram.ext

import feedparser
import hashlib
import logging

from main.data.orm import Feed 

logger = logging.getLogger(__name__)

# get hash for a message
def get_hash(message : str):
    return hashlib.sha256(message.encode()).hexdigest()

# get messages from given newer than 
def get_new_messages(feed : Feed):
    new_messages = []

    # parse feed
    rss = feedparser.parse(feed.link)

    # check find the right element group for messages
    if not 'feed' in rss:
        logger.error(f"No valid element group found for feed at url {feed.link}")
        return None

    # check for new messages
    if len(rss.entries) > 0:
        last_message_hash = get_hash(rss.entries[0].title)
        for entry in rss.entries:
            if get_hash(entry.title) == feed.last_message_hash:
                break # latest mesasge reached
            else:
                new_messages.append(entry)
        logger.info(f"{len(new_messages)} new messages for feed {feed.link}")
        new_messages.reverse() # to send oldest message first
        return new_messages, last_message_hash
    else:
        logger.warn(f"No entries for feed {feed.link}")
        return [], feed.last_message_hash