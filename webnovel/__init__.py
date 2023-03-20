"""A Python Package for dealing with webnovels and epubs."""

import logging

LOGGING_ON = False


def turn_on_logging():
    """Turn on logging."""
    global LOGGING_ON

    if not LOGGING_ON:
        logger = logging.getLogger(__name__)
        loghandler = logging.StreamHandler()
        loghandler.setFormatter(logging.Formatter("PYWN: %(levelname)s: %(asctime)s: %(name)s: %(message)s"))
        logger.addHandler(loghandler)
        loghandler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        LOGGING_ON = False
