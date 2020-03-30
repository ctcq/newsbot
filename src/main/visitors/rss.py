import sqlalchemy
import sqlalchemy.orm
import feedparser
import hashlib
import logging
import telegram.ext
import time

"""
Visitor class for checking subscribed feeds
"""
class RssSubscriptionsVisitor():

    def __init__(self, session : sqlalchemy.orm.Session):
        self.logger = logging.getLogger(__name__)
        self.session = session

    def persist_subscriptions(self, subscriptions : list):
        self.logger.info(f"Updating subscripitions in {self.subscriptions_file}")
        with open(self.subscriptions_file, 'w') as file:
            json.dump(subscriptions, file, indent=4)

    # Read subscriptions file and load all feeds
    def visit(self):
        self.logger.info(f"Visiting subscriptions")

        # New messages to be sent
        new_messages = []

        # Go through feeds an look for new messages
        for feed_data in subscriptions:
            rss = feedparser.parse(feed_data['link'])

            # Some feeds are contained in a channel, some are not
            if ('channel' in rss.keys()):
                feed = rss.channel.feed
            else:
                feed = rss.feed

            # Assign format
            if not 'format' in feed_data.keys():
                feed_data['format'] = ""

            # Assign metadata to feed
            if 'title' in feed.keys():
                feed_data['title'] = feed.title
            else:
                self.logger.warn(f"No title for feed {feed_data['link']}")
                feed_data['title'] = "NO FEED TITLE"
            
            if 'description' in feed.keys():
                feed_data['description'] = feed.description
            else:
                self.logger.warn(f"Not description for feed {feed_data['link']}")
                feed_data['description'] = "NO FEED DESCRIPTION"

            # Set last updated key if it doesn't exist yet
            if not 'last_message_hash' in feed_data.keys():
                feed_data['last_message_hash'] = ""

            # Check if there are new messages
            if len(rss.entries) > 0 and (hash := hashlib.sha256(rss.entries[0].title.encode()).hexdigest()) != feed_data['last_message_hash']:
                latest_message_hash = hash
                self.logger.info(f"New messages for {feed_data['title']}")
            else:
                self.logger.info(f"No new messages for {feed_data['title']}")
                continue

            # Add messages newer than last message recorded
            for message in rss.entries:
                # Stop iterating through messages if a known hash is encountered
                if (hash := hashlib.sha256(message.title.encode()).hexdigest()) != feed_data['last_message_hash']:
                    data = {
                        'title' : feed_data['title'],
                        'description' : message['description'],
                        'link' : message['link'],
                        'format' : feed_data['format']
                    }
                    # Add message data to new message
                    new_messages.append(data)
                else:
                    break

            # Update last message hash
            if latest_message_hash != "":
                feed_data['last_message_hash'] = latest_message_hash
        # Return updated subscription file and new messages
        self.logger.info(f"Read {len(new_messages)} new messages.")
        new_messages.reverse() # Reverse so latest message comes last
        return subscriptions, new_messages
