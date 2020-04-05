#!/usr/bin/python
import argparse
import json
import logging

import main.bot.telegram.jobs as jobs
import main.bot.telegram.commands as commands
from main.bot.telegram.conversations.timezone import TimezoneConversation
from main.bot.telegram.conversations.reminder import ReminderConversation
from main.bot.telegram.conversations.tracking import TrackingConversation
import main.data.orm as orm

from telegram.ext import CommandHandler
from sqlalchemy import create_engine
from main.bot.telegram.TelegramBotFacade import TelegramBotFacade
from sqlalchemy.orm import sessionmaker

# Parse cmdline arguments
parser = argparse.ArgumentParser(description="Additional options for the newsfeed bot")
parser.add_argument('resources', metavar='R', type=str, default="/resources", nargs="?", help='path pointing to bot resources')
parser.add_argument('data', metavar='D', type=str, default="/data", nargs="?", help='path pointing to bot data')
args = parser.parse_args()
resource_dir = args.resources
data_dir = args.data

# Init logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# load config
logger.info("Loading config...")
with open(f"{resource_dir}/config/config.json") as file:
    config = json.load(file)

# init database
db_address = f"sqlite:///{data_dir}/newsbot.db"
logger.info(f"Starting database {db_address}...")
engine = create_engine(db_address)
session = orm.get_session(engine)

# init bot
logger.info("Initiating bot...")
with open(f"{resource_dir}/bot/token") as file:
    bot_token = file.read()
bot_facade = TelegramBotFacade(bot_token)

# add command handlers
logger.info("Adding bot handlers...")
bot_facade.add_command_handler('start', lambda updater, context : commands.start(updater, context, session))
bot_facade.add_command_handler('stop', lambda updater, context : commands.stop(updater, context, session))
bot_facade.add_command_handler('help', lambda updater, context : commands.help(updater, context))

bot_facade.add_command_handler('feeds', lambda updater, context : commands.feeds(updater, context, session))
bot_facade.add_command_handler('subscribe', lambda updater, context : commands.subscribe(updater, context, session))
bot_facade.add_command_handler('trackings', lambda updater, context : commands.trackings(updater, context, session))
bot_facade.add_command_handler('unsubscribe', lambda updater, context : commands.unsubscribe(updater, context, session))
bot_facade.add_command_handler('youtube', lambda updater, context : commands.youtube(updater, context, session))
bot_facade.add_command_handler('untrack', lambda updater, context : commands.untrack(updater, context, session))
bot_facade.add_command_handler('wiki', lambda updater, context : commands.wiki(updater, context, config['wikipedia_summary_sentences']))
bot_facade.add_command_handler('qwiki', commands.qwiki)

bot_facade.add_command_handler('reminder', lambda updater, context : commands.reminder(updater, context, session))

# add conversation handlers
logger.info("Adding conversation handlers...")
tz_conv = TimezoneConversation()
bot_facade.add_conversation_handler('set_timezone',tz_conv.get_conv_handler(session))

reminder_conv = ReminderConversation(session)
bot_facade.add_conversation_handler('/remind',reminder_conv.get_conv_handler(session))

tracking_conv = TrackingConversation(session)
bot_facade.add_conversation_handler('/track',tracking_conv.get_conv_handler(session))

# add job handlers
logger.info("Adding job handlers...")
bot_facade.add_job_interval(
    'RSS Broadcast',
    lambda context : jobs.broadcast_new_rss_messages(context, engine),
    0,
    config['broadcast_interval_in_seconds']
)
bot_facade.add_job_interval(
    'Reminders Notification',
    lambda context : jobs.notify_reminders(context, engine, config['reminder_notify_ahead_seconds']),
    0,
    config['reminder_interval_in_seconds']
)

logger.info("Starting bot...")
bot_facade.start_bot()