import unittest

from main.telegram.commands
from sqlalchemy import create_engine

test_db = "sqlite:///"

class TestDbPersistence(unittest.TestCase):

    def test_plan_cmd():
        commands = [
            {
                "cmd" : ["/remind", "2.1.2020", "1:00", "Test 1"],
                "timezone" : [""]
                "expect" : []
            },
            ["/remind", "2.1.2020", "1:00", "Test 2"],
        ]
        timestamp : int,
        message = "" : str,
        n_reminders = 0 : int,
        unit_reminders = HOURS : TimeUnit