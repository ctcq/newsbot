#!/usr/bin/python
import json
import logging

import main.bot.telegram.jobs as jobs
import main.bot.telegram.commands as commands
import main.data.orm as orm

from telegram.ext import CommandHandler
from sqlalchemy import create_engine
from main.bot.telegram.TelegramBotFacade import TelegramBotFacade
from sqlalchemy.orm import sessionmaker

# Init logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# load config
logger.info("Loading config...")
with open('./resources/config/config.json') as file:
    config = json.load(file)

# init database
db_address = config['db_production']
logger.info(f"Starting database {db_address}...")
engine = create_engine(db_address)
session = orm.get_session(engine)

# init bot
logger.info("Initiating bot...")
with open('./resources/bot/token') as file:
    bot_token = file.read()
bot_facade = TelegramBotFacade(bot_token)

# add command handlers
logger.info("Adding bot handlers...")
bot_facade.add_command_handler('start', lambda updater, context : commands.start(updater, context, session))
bot_facade.add_command_handler('stop', lambda updater, context : commands.stop(updater, context, session))
bot_facade.add_command_handler('help', lambda updater, context : commands.help(updater, context))

bot_facade.add_command_handler('feeds', lambda updater, context : commands.feeds(updater, context, session))
bot_facade.add_command_handler('subscribe', lambda updater, context : commands.subscribe(updater, context, session))
bot_facade.add_command_handler('unsubscribe', lambda updater, context : commands.unsubscribe(updater, context, session))

# add job handlers
logger.info("Adding job handlers...")
bot_facade.add_job_interval(
    'RSS Broadcast',
    lambda context : jobs.broadcast_new_rss_messages(context, engine),
    0,
    config['broadcast_interval_in_seconds']
)

logger.info("Starting bot...")
bot_facade.start_bot()