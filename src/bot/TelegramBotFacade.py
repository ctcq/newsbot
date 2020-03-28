from typing import Callable
import logging
from telegram.ext import Updater

class TelegramBotFacade():

    def __init__(self, token : str):
        self.logger = logging.getLogger(__name__)
        self.bot = Updater(token, use_context = True)
        self.logger.info(f"Using bot: {self.bot.bot.get_me()['username']}")

    def start_bot(self):
        self.bot.job_queue.start()
        self.bot.idle()

    def add_job_interval(self, callback : Callable, interval_in_seconds : int, start : int, name : str):
        self.logger.info(f"Adding periodic job '{name}' at interval {interval_in_seconds} seconds")
        self.bot.job_queue.run_repeating(callback, interval = interval_in_seconds, first = start)

    def add_job_once(self, callback : Callable, name : str):
        self.logger.info(f"Adding job '{name}'")
        self.bot.job_queue.run_once(callback, 0)