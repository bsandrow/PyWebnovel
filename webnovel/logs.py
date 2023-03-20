"""Logging functionality / utilities."""

import contextlib
import datetime
import logging


class LogTimer:
    """A timer for logging the start and end of an action with the amount of time that it took."""

    logger: logging.Logger

    def __init__(self, logger: logging.Logger, log_level: int = logging.DEBUG) -> None:
        self.logger = logger
        self.log_level = log_level

    def _log(self, message: str, args, **kwargs):
        self.logger._log(self.log_level, message, args, **kwargs)

    @contextlib.contextmanager
    def __call__(self, message: str, *args, **kwargs):
        """
        Log the amount of time that it takes a piece of code to run.

        Example::

            logger = logging.getLogger(__name__)
            timer = LogTimer(logger)

            with timer("Perform Action"):
                ...

        Will result in logging like this::

            [2006-01-01 11:05:48] Starting timer «Perform Action»...
            [2006-01-01 11:06:00] Finished timer «Perform Action» in 12.19528 second(s)...
        """
        start_time = datetime.datetime.now()
        self._log(f"Starting timer «{message}»...", args, **kwargs)
        yield
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        self._log(f"Finished timer «{message}» in {duration.total_seconds()} second(s).", args, **kwargs)
