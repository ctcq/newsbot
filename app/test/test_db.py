import json
import unittest
import main.data.orm as orm
from sqlalchemy import create_engine

test_db = "sqlite:///"

class TestDbPersistence(unittest.TestCase):

    def test_feed(self):
        # setup db
        engine = create_engine(test_db)
        session = orm.get_session(engine)
        orm.setup_database(engine)
        feed = orm.Feed("link", "title", "description", "format", "last_message_hash")
        session.add(feed)

        # insert feed
        feeds = session.query(orm.Feed).all()

        # assertions
        # check if insert was successful
        self.assertEqual(len(feeds), 1)
        loadedFeed = feeds[0]
        self.assertEqual(repr(loadedFeed), repr(feed))

        # check if deletion was successful
        session.delete(loadedFeed)
        self.assertFalse(orm.user_exists(session, loadedFeed.link))

    def test_chat(self):
        # setup db
        engine = create_engine(test_db)
        session = orm.get_session(engine)
        chat = orm.Chat("chat_id")
        session.add(chat)

        # insert chat
        chats = session.query(orm.Chat).all()

        # assertions
        # check if insert was successful
        self.assertTrue(orm.user_exists(session, chat.chat_id))
        self.assertEqual(len(chats), 1)
        loadedChat = chats[0]
        self.assertEqual(repr(loadedChat), repr(chat))

        # check if deletion was sucessful
        session.delete(loadedChat)
        self.assertFalse(orm.user_exists(session, loadedChat.chat_id))

    def test_feedsubscriptions(self):
        #setup db
        engine = create_engine(test_db)
        session = orm.get_session(engine)

        # Create objects and link them together
        chat = orm.Chat("chat_id")
        feed = orm.Feed("link", "title", "description", "format", "last_message_hash")
        chat.feeds.append(feed)

        # insert data
        session.add(chat)
        session.add(feed)

        # assertions
        associatedFeed = session.query(orm.Feed).filter(orm.Feed.chats.any(chat_id='chat_id')).all()[0]
        self.assertEqual(repr(associatedFeed), repr(feed))

        associatedChat = session.query(orm.Chat).filter(orm.Chat.feeds.any(link='link')).all()[0]
        self.assertEqual(repr(associatedChat), repr(chat))