from typing import Callable
import logging
from telegram.ext import Updater
from telegram.ext import CommandHandler

class TelegramBotFacade():

    def __init__(self, token : str):
        self.logger = logging.getLogger(__name__)
        self.updater = Updater(token, use_context = True)
        self.dispatcher = self.updater.dispatcher
        self.logger.info(f"Using bot: {self.updater.bot.get_me()['username']}")

    def start_bot(self):
        self.updater.job_queue.start()
        self.updater.start_polling()

    def add_job_interval(self, name : str, callback : Callable, start : int, interval_in_seconds : int):
        self.logger.info(f"Adding periodic job '{name}' at interval {interval_in_seconds} seconds")
        self.updater.job_queue.run_repeating(callback, interval = interval_in_seconds, first = start)

    def add_job_once(self, callback : Callable, name : str):
        self.logger.info(f"Adding job '{name}'")
        self.updater.job_queue.run_once(callback, 0)

    def add_command_handler(self, command : str, callback : Callable):
        self.logger.info(f"Adding handler for command {command}")
        self.dispatcher.add_handler(CommandHandler(command, callback))