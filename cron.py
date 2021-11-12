#!/usr/bin/python3
import typing as t

import sys
import datetime


class CronExpection(ValueError):
    """
    Base cron exception.
    """


class ConfigParser:
    @staticmethod
    def read() -> t.Iterator[str]:
        line = sys.stdin.readline()
        while line:
            yield line.strip()
            line = sys.stdin.readline()


class TimeInput:
    """
    Descriptor for accessing parsed time argument.
    """

    def __init__(self, time_expr: t.Optional[str] = None) -> None:
        self.time = time_expr

    def __get__(self, instance, cls):
        return self.time

    def __set__(self, instance, value):
        self.time = datetime.time(*map(int, value.split(":")))


class TimeArg:
    """
    Cron time argument to native time.
    """

    time = TimeInput()

    def __init__(self, time_expr: str) -> None:
        self.time = time_expr


class TimeTab:
    def __init__(self, time_expr: t.Optional[str] = None) -> None:
        self.time = time_expr

    def __get__(self, instance, cls):
        return self.time

    def __set__(self, instance, value):
        self.time = datetime.time(*self._expand(value))

    @classmethod
    def _expand(cls, value: str) -> t.List[int]:
        expressions = value.split()
        if len(expressions) != 2:
            raise CronExpection("")

        _munite, _hour = expressions

        munite = int(_munite != "*" and _munite or 0)
        hour = int(_hour != "*" and _hour or 0)

        if hour > datetime.time.max.hour:
            raise CronExpection("")

        if munite > datetime.time.max.minute:
            raise CronExpection("")

        return [hour, munite]


class CronTabTime:
    """
    Cron tab time formater.
    """

    time = TimeTab()

    def __init__(self, tab_time_fmt: str) -> None:
        self.time = tab_time_fmt

    def __le__(self, other):
        return self.time <= other.time


class CronTabCommand:
    def __init__(self, command: str, base_time: str) -> None:
        """
        Crontab config line formater.
        """
        self.command = command
        self.base_time = base_time

        self._to_run = None

        self.time_expr, self.excutable = self.command.rsplit(" ", 1)

        self.time_now = TimeArg(self.base_time)
        self.time_to_run = CronTabTime(self.time_expr)

        self.time_to_run_next = self.get_next_run()
        self.when_to_run = self.get_when_run(self.time_now.time, self.time_to_run_next)

    def __str__(self) -> str:
        return (
            f"{self.time_to_run_next.strftime('%H:%M')} "
            f"{self.when_to_run} - "
            f"{self.excutable}"
        )

    def get_next_run(self):
        """
        Get next time to run.
        """
        if not self._to_run:
            current_time: datetime.time = self.time_now.time
            expected_time: str = self.time_to_run.time

            next_time = self.get_next(current_time, expected_time)
            self._to_run = next_time

        return self._to_run

    @classmethod
    def get_when_run(cls, current_time: datetime.time, next_time: datetime.time) -> str:
        """
        Get when to run.
        """

        return current_time > next_time and "tomorrow" or "today"

    @classmethod
    def get_next(
        cls, current_time: datetime.time, expected_time: datetime.time
    ) -> t.Optional[datetime.time]:
        """
        Getting next time to run utility
        """
        c_hour: int = current_time.hour
        c_minute: int = current_time.minute

        e_hour: int = expected_time.hour
        e_minute: int = expected_time.minute

        if e_hour and e_minute:
            return expected_time

        if not e_hour and not e_minute:
            return current_time

        if not e_hour and e_minute:
            return datetime.time(c_hour, max(c_minute, e_minute))

        if e_hour and not e_minute:
            if c_hour < e_hour:
                return datetime.time(e_hour, 0)
            else:
                return current_time
        return None


class Cron:
    def __init__(self) -> None:
        self.config = ConfigParser.read()

    def execute(self):
        while True:
            try:
                line = next(self.config)
                command = CronTabCommand(line, sys.argv[1])
                print(command)
            except StopIteration:
                break


if __name__ == "__main__":
    Cron().execute()
