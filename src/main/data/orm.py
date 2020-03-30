from main.config import db_config
from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text, create_engine
from sqlalchemy.sql import exists
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

import logging
import sqlalchemy

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
    Column('chat_id', Integer)
)

# create chat<->feeds association table 
feed_subscription = Table('feed_subscription', Base.metadata,
    Column('chat_id', ForeignKey('chats.id'), primary_key=True),
    Column('feed_id', ForeignKey('feeds.id'), primary_key=True)
)

def user_exists(session : sqlalchemy.orm.Session, chat_id : str):
    return session.query(Chat.chat_id).filter(
        exists().where(Chat.chat_id == chat_id)
    ).count() > 0

def feed_exists(session : sqlalchemy.orm.Session, link : str):
    return session.query(Feed.link).filter(
        exists().where(Feed.link == link)
    ).count() > 0

class Chat(Base):
    __tablename__ = 'chats'
    
    # *-to-* Chat<->Feed
    feeds = relationship('Feed',
        secondary=feed_subscription,
        back_populates='chats'
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

    def __init__(self, link : str, title : str = "", description : str = "", format : str = "", last_message_hash : str = ""):
        self.link = link
        self.title = title
        self.description = description
        self.format = format
        self.last_message_hash = last_message_hash

    def __repr__(self):
        return f"<Feed(link={self.link}, title={self.title}, description={self.description}, format={self.format}, last_message_hash={self.last_message_hash})>"

# Create all tables
def setup_database(engine):
    Base.metadata.create_all(engine)

def get_session(engine):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()