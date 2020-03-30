# !/usr/bin/python
import argparse
import json
import logging
import os

import main.bot.telegram.jobs as jobs
import main.bot.telegram.commands as commands
import main.config.db_config as db_config
import main.data.orm as orm

from telegram.ext import CommandHandler
from main.bot.telegram.TelegramBotFacade import TelegramBotFacade
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main.visitors.rss import RssSubscriptionsVisitor

# Init logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Init argument parser
arg_parser = argparse.ArgumentParser(description='Start the newsfeed bot.')
arg_parser.add_argument('--resources', default='/opt/newsfeed_bot/resources', dest='resource_dir', help='directory containing resources and configurations')
args = arg_parser.parse_args()

# fetch cmdline arguments
resource_dir = args.resource_dir

# load bot config
with open(resource_dir + '/bot/config.json') as file:
    config = json.load(file)

# init bot
logger.info("Inititating bot...")
with open(resource_dir + '/bot/token') as file:
    bot_token = file.read()
bot_facade = TelegramBotFacade(bot_token)

# init visitors
logger.info("Initiating visitors...")
rss_subscriptions_visitor = RssSubscriptionsVisitor(resource_dir + '/rss/subscriptions.json') 

# init database
engine = create_engine(db_config.prod_db)
session = orm.get_session(engine)

# add command handlers
bot_facade.add_handler('start', lambda updater, context : commands.start(updater, context, session))
bot_facade.add_handler('stop', lambda updater, context : commands.stop(updater, context, session))
bot_facade.add_handler('help', lambda updater, context : commands.help(updater, context))

bot_facade.add_handler('feeds', lambda updater, context : commands.feeds(updater, context, session))
bot_facade.add_handler('subscribe', lambda updater, context : commands.subscribe(updater, context, session))

# add jobs and start bot
# Welcome message
bot_facade.updater.job_queue.run_once(
    lambda context : jobs.broadcast_welcome_job(context, chat_id_visitor), 0
    )

# Rss subscriptions
logger.info("Starting bot")
# bot_facade.add_job_interval(
#     lambda context : jobs.broadcast_rss_job(context, chat_id_visitor, rss_subscriptions_visitor),
#     interval_in_seconds = config['broadcast_interval_in_seconds'],
#     start = 0,
#     name = 'RSS Broadcast'
#     )

bot_facade.start_bot()