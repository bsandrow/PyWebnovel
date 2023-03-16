"""Command to create an epub file from a link to a webnovel."""

import argparse

from webnovel import actions


def get_cli_options():
    """Parse the CLI options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-u", "--novel-url", help="The URL of the novel. Only used on ")
    parser.add_argument("-f", "--filename", help="The name of the epub file to create.")
    options = parser.parse_args()
    return options


def run():
    """Run the command."""
    options = get_cli_options()
    actions.create_epub(options.novel_url, options.filename, chapter_limit=None)


if __name__ == "__main__":
    run()
