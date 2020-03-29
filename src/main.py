# !/usr/bin/python

import argparse
import json
import logging
import os

from telegram.ext import CommandHandler
from visitors.ChatIdVisitor import ChatIdVisitor
from visitors.RssSubscriptionsVisitor import RssSubscriptionsVisitor
from bot.TelegramBotFacade import TelegramBotFacade
from bot import jobs
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot import commands

# Init logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Init argument parser
arg_parser = argparse.ArgumentParser(description='Start the newsfeed bot.')
arg_parser.add_argument('--resources', default='/opt/newsfeed_bot/resources', dest='resource_dir', help='directory containing resources and configurations')
args = arg_parser.parse_args()

resource_dir = args.resource_dir

# Init ORM
engine = create_engine("sqlite://")
session = sessionmaker(bind=engine)

# load bot config
with open(resource_dir + '/bot/config.json') as file:
    config = json.load(file)

# init bot
logger.info("Inititating bot...")
with open(resource_dir + '/bot/token') as file:
    bot_token = file.read()
bot_facade = TelegramBotFacade(bot_token)

# init visitors
logger.info("Initiating visitors")
chat_id_visitor = ChatIdVisitor(resource_dir + '/bot/chat_ids.json')
rss_subscriptions_visitor = RssSubscriptionsVisitor(resource_dir + '/rss/subscriptions.json') 

# add command handlers
bot_facade.add_handler('start', commands.start)
bot_facade.add_handler('help', commands.help)

# add jobs and start bot
# Welcome message
bot_facade.updater.job_queue.run_once(
    lambda context : jobs.broadcast_welcome_job(context, chat_id_visitor), 0
    )

# Rss subscriptions
logger.info("Starting bot")
bot_facade.add_job_interval(
    lambda context : jobs.broadcast_rss_job(context, chat_id_visitor, rss_subscriptions_visitor),
    interval_in_seconds = config['broadcast_interval_in_seconds'],
    start = 0,
    name = 'RSS Broadcast'
    )

bot_facade.start_bot()