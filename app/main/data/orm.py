from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text, create_engine
from sqlalchemy.sql import exists
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

import datetime
import logging
import pytz
import sqlalchemy
import time

Base = declarative_base()

# Create feed table
feeds = Table('feeds', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('link', String),
    Column('title', String),
    Column('description', String),
    Column('format', String),
    Column('last_message_hash', String)
)

# create chat table
chats = Table('chats', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('chat_id', Integer),
    Column('timezone', String)
)

# create reminder table
reminders = Table('reminders', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('timestamp', Integer),
    Column('message', String),
    Column('user_id', Integer, ForeignKey('chats.id'))
)

# create tracking table
trackings = Table('trackings', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String),
    Column('url', String),
    Column('user_id', Integer, ForeignKey('chats.id'))
)

tracking_data = Table('tracking_data', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('tracking_id', Integer, ForeignKey('trackings.id')),
    Column('timestamp', Integer),
    Column('value', String)
)

# create chat<->feeds association table 
feed_subscription = Table('feed_subscription', Base.metadata,
    Column('chat_id', ForeignKey('chats.id'), primary_key=True),
    Column('feed_id', ForeignKey('feeds.id'), primary_key=True)
)

def user_exists(session : sqlalchemy.orm.Session, chat_id : str):
    if session.query(Chat.chat_id).filter(exists().where(Chat.chat_id == chat_id)).count() > 0:
        return session.query(Chat).filter(Chat.chat_id == chat_id).all()[0]
    else:
        return None 

def feed_exists(session : sqlalchemy.orm.Session, link : str):
    if session.query(Feed.link).filter(exists().where(Feed.link == link)).count() > 0:
        return session.query(Feed).filter(Feed.link == link).all()[0]
    else:
        return None

class Chat(Base):
    __tablename__ = 'chats'
    
    # *-to-* Chat<->Feed
    feeds = relationship('Feed',
        secondary=feed_subscription,
        back_populates='chats'
    )

    # 1-to-* Chat<->Reminder
    reminders = relationship('Reminder',
        back_populates='chat'
    )

    trackings = relationship('Tracking',
        back_populates='chat'
    )

    def __init__(self, chat_id : str):
        self.chat_id = chat_id

    def __repr__(self):
        return f"<Chat(chat_id={self.chat_id})>"

class Feed(Base):
    __tablename__ = 'feeds'

    # *-to-* Chat<->Feed
    chats = relationship('Chat',
        secondary=feed_subscription,
        back_populates='feeds'
    )

    def __init__(self, link : str, title : str = "", last_message_hash : str = ""):
        self.link = link
        self.title = title
        self.last_message_hash = last_message_hash

    def __repr__(self):
        return f"<Feed(link={self.link}, title={self.title}, description={self.description}, format={self.format}, last_message_hash={self.last_message_hash})>"

class Reminder(Base):
    __tablename__ = 'reminders'
    chat = relationship('Chat',
        back_populates='reminders'
    )

    def __init__(self, timestamp : int, message : str = "", user_id : int = 0):
        self.timestamp = timestamp
        self.message = message
        self.user_id = user_id

    def __repr__(self):
        return f"<Reminder(timestamp={self.timestamp}, message={self.message}, chat={self.chat})>"

class Tracking(Base):
    __tablename__ = 'trackings'
    chat = relationship('Chat',
        back_populates='trackings'
    )

    data = relationship('TrackingData',
        back_populates='tracking'
    )

    def __init__(self, title : str, url : str, user_id : int):
        self.title = title
        self.url = url
        self.user_id = user_id

    def __repr__(self):
        return f"<Tracking(title={self.title}, url={self.url}, user_id={self.user_id})>"

class TrackingData(Base):
    __tablename__ = 'tracking_data'
    tracking = relationship('Tracking',
        back_populates='data'
    )

    def __init__(self, tracking_id : int, timestamp : int, value : str):
        self.tracking_id = tracking_id
        self.timestamp = timestamp
        self.value = value

    def __repr__(self):
        return f"<Trackingdata(tracking_id={self.tracking_id}, timestamp={self.timestamp}, value={self.value})>"

# Create all tables
def setup_database(engine):
    Base.metadata.create_all(engine)

def get_session(engine):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()