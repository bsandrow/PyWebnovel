"""Command to create an epub file from a link to a webnovel."""

import argparse
import logging

from webnovel import actions, turn_on_logging

arg_parser = argparse.ArgumentParser(description="Create an .epub file ")
arg_parser.add_argument("-u", "--novel-url", help="The URL of the novel.")
arg_parser.add_argument("-f", "--filename", help='The name of the .epub file to create. Defaults to "Novel Title.epub"')
arg_parser.add_argument(
    "--cover-image-url",
    help=(
        "Provide an alternative cover image url. By default, this will be "
        "scraped from the novel URL. If provided, this option will override "
        "that."
    ),
)


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


def run():
    """Run the command."""
    turn_on_logging()
    options = arg_parser.parse_args()
    actions.create_epub(
        options.novel_url,
        options.filename,
        cover_image_url=options.cover_image_url,
        chapter_limit=None,
    )


if __name__ == "__main__":
    run()