"""Command to create an epub file from a link to a webnovel."""

import argparse
import logging

from webnovel import actions, turn_on_logging


def setup_logging():
    """Initialize logging settings."""
    logger = logging.getLogger("webnovel")
    loghandler = logging.StreamHandler()
    loghandler.setFormatter(
        logging.Formatter("PYWN: %(levelname)s: %(asctime)s: %(filename)s(%(lineno)d): %(message)s")
    )
    logger.addHandler(loghandler)
    loghandler.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)


def get_cli_options():
    """Parse the CLI options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-u", "--novel-url", help="The URL of the novel. Only used on ")
    parser.add_argument("-f", "--filename", help="The name of the epub file to create.")
    parser.add_argument("--cover-image-url", help="Provide an alternative cover image url.")
    options = parser.parse_args()
    return options


def run():
    """Run the command."""
    turn_on_logging()
    options = get_cli_options()
    actions.create_epub(
        options.novel_url,
        options.filename,
        cover_image_url=options.cover_image_url,
        chapter_limit=None,
    )


if __name__ == "__main__":
    run()
