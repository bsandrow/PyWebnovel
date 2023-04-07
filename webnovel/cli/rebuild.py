"""Command to rebuild an epub file."""

import argparse

from webnovel import actions, turn_on_logging

arg_parser = argparse.ArgumentParser(
    description=(
        "Rebuild an existing epub file. This is useful if the building code (e.g. the xhtml templates) have changed"
        " and you want to update the epub file without building a new epub from scratch which would include re-downloading"
        " all of the content. Note that this only works for epub files built with PyWebnovel, and might not have expected"
        " results if there are significant changes to the internal JSON format between revisions."
    )
)
arg_parser.add_argument("epub_file", help="A .epub file to rebuild.")


def run(args=None):
    """Run the command."""
    turn_on_logging()
    options = arg_parser.parse_args(args)
    actions.rebuild(options.epub_file)


if __name__ == "__main__":
    run()
