import io
import datetime
from contextlib import contextmanager
from copy import deepcopy

from typing import Callable

import unittest
import unittest.mock


cron = __import__("cron")


class TestCase(unittest.TestCase):
    pass


class TestTimeInput(TestCase):
    def test_time_input(self):
        class Mock:
            time = cron.TimeInput()

            def __init__(self, time_input):
                self.time = time_input

        assert Mock("1:13").time == datetime.time(1, 13)
        assert Mock("16:10").time == datetime.time(16, 10)
        assert Mock("23:59").time == datetime.time(23, 59)


class TestTimeArg(TestCase):
    def test_time_arg(self):
        # time expression: 10:15
        time_arg = cron.TimeArg(time_expr="10:15")
        assert time_arg.time == datetime.time(10, 15)

        # time expression: 13:05
        time_arg = cron.TimeArg(time_expr="13:05")
        assert time_arg.time == datetime.time(13, 5)

        # time expression: 13:5
        time_arg = cron.TimeArg(time_expr="13:5")
        assert time_arg.time == datetime.time(13, 5)

        # time expression: 3:6
        time_arg = cron.TimeArg(time_expr="3:6")
        assert time_arg.time == datetime.time(3, 6)

        # time expression: 03:6
        time_arg = cron.TimeArg(time_expr="03:6")
        assert time_arg.time == datetime.time(3, 6)


class TestTimeTab(TestCase):
    def test_time_tab(self):
        class Mock:
            time = cron.TimeTab()

            def __init__(self, tab_time_fmt):
                self.time = tab_time_fmt

        assert Mock("* *").time == datetime.time(0, 0)
        assert Mock("30 1").time == datetime.time(1, 30)
        assert Mock("* 20").time == datetime.time(20, 0)
        assert Mock("15 *").time == datetime.time(0, 15)

    def test_time_tab_invalid_format(self):
        class Mock:
            time = cron.TimeTab()

            def __init__(self, tab_time_fmt):
                self.time = tab_time_fmt

        with self.assertRaises(cron.CronExpection):
            Mock("*")

        with self.assertRaises(cron.CronExpection):
            Mock("62 *")

        with self.assertRaises(cron.CronExpection):
            Mock("30 24")


class TestCronTabCommand(TestCase):
    def test_instructions(self):
        command = "30 1 /bin/run_me_daily"
        current_time = "16:10"

        results = cron.CronTabCommand(command, current_time)

        assert results.time_now.time == datetime.time(16, 10)
        assert results.time_to_run.time == datetime.time(1, 30)

        assert results.time_to_run_next == datetime.time(1, 30)
        assert results.when_to_run == "tomorrow"

    def test_representation(self):
        command = "* * /bin/run_some_time"
        current_time = "10:15"

        results = cron.CronTabCommand(command, current_time)

        assert str(results) == "10:15 today - /bin/run_some_time"

    def test_get_next(self):
        current_time = datetime.time(16, 10)
        expected_time = datetime.time(1, 30)
        results = cron.CronTabCommand.get_next(current_time, expected_time)
        assert results == datetime.time(1, 30)

        current_time = datetime.time(1, 0)
        expected_time = datetime.time(1, 30)
        results = cron.CronTabCommand.get_next(current_time, expected_time)
        assert results == datetime.time(1, 30)

        current_time = datetime.time(16, 10)
        expected_time = datetime.time(0, 45)
        results = cron.CronTabCommand.get_next(current_time, expected_time)
        assert results == datetime.time(16, 45)

        current_time = datetime.time(10, 0)
        expected_time = datetime.time(0, 30)
        results = cron.CronTabCommand.get_next(current_time, expected_time)
        assert results == datetime.time(10, 30)

        current_time = datetime.time(16, 10)
        expected_time = datetime.time(0, 0)
        results = cron.CronTabCommand.get_next(current_time, expected_time)
        assert results == datetime.time(16, 10)

        current_time = datetime.time(16, 10)
        expected_time = datetime.time(19, 0)
        results = cron.CronTabCommand.get_next(current_time, expected_time)
        assert results == datetime.time(19, 0)

        current_time = datetime.time(19, 10)
        expected_time = datetime.time(19, 0)
        results = cron.CronTabCommand.get_next(current_time, expected_time)
        assert results == datetime.time(19, 10)

        current_time = datetime.time(10, 11)
        expected_time = datetime.time(10, 0)
        results = cron.CronTabCommand.get_next(current_time, expected_time)
        assert results == datetime.time(10, 11)

    def test_get_when_run(self):
        current_time = datetime.time(16, 10)
        expected_time = datetime.time(1, 30)
        results = cron.CronTabCommand.get_when_run(current_time, expected_time)
        assert results == "tomorrow"

        current_time = datetime.time(16, 10)
        expected_time = datetime.time(16, 45)
        results = cron.CronTabCommand.get_when_run(current_time, expected_time)
        assert results == "today"

        current_time = datetime.time(16, 10)
        expected_time = datetime.time(16, 10)
        results = cron.CronTabCommand.get_when_run(current_time, expected_time)
        assert results == "today"

        current_time = datetime.time(16, 10)
        expected_time = datetime.time(19, 0)
        results = cron.CronTabCommand.get_when_run(current_time, expected_time)
        assert results == "today"


@contextmanager
def mock(object, attribute, return_object):
    copy = deepcopy(getattr(object, attribute, None))
    try:
        setattr(object, attribute, return_object)
        yield object
    finally:
        setattr(object, attribute, copy)


class TestConfigParser(TestCase):
    @unittest.mock.patch("cron.sys")
    def test_read(self, mock_sys):
        mock_sys.stdin = io.StringIO("line 1\nline 2\nline 3")

        assert next(cron.ConfigParser.read()) == "line 1"
        assert next(cron.ConfigParser.read()) == "line 2"
        assert next(cron.ConfigParser.read()) == "line 3"

        with self.assertRaises(StopIteration):
            next(cron.ConfigParser.read())


if __name__ == "__main__":
    unittest.main()
