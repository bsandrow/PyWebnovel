"""Command to create an epub file from a link to a webnovel."""

import argparse
import logging

from webnovel import actions, turn_on_logging

arg_parser = argparse.ArgumentParser(description="Set the cover image of an epub.")
arg_parser.add_argument("epub", help="The epub file to set the cover image for.")
arg_parser.add_argument("cover_image", help="The path (or URL) for the cover image.")


def run(args=None):
    """Run the command."""
    turn_on_logging()
    options = arg_parser.parse_args(args)
    actions.set_cover_image_for_epub(epub_file=options.epub, cover_image_path=options.cover_image)


if __name__ == "__main__":
    run()
