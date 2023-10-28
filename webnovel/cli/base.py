"""Helpers for webnovel.cli."""

import logging
from types import ModuleType

from apptk.importing import import_all_from_submodules
import click

from webnovel.actions import App

# Make sure we are always passing App instance.
pass_app = click.make_pass_decorator(App)


def auto_add_commands(group: click.Group, package: str | ModuleType) -> None:
    """Add all click commands from the provided package to the Group."""
    commands = import_all_from_submodules(package=package, filter=lambda x: isinstance(x, click.Command))
    for _, command in commands.items():
        group.add_command(command)


class Handler(logging.StreamHandler):
    """StreamHandler that adds short log-level prefixes to the formatted log records."""

    PREFIX = {
        logging.INFO: "[i]",
        logging.DEBUG: "[d]",
        logging.WARNING: "[w]",
        logging.ERROR: "[!]",
        logging.FATAL: "!!!",
        logging.CRITICAL: "!!!",
    }

    def format(self, record) -> str:
        """Prefix messages with a shortened form of the logging level."""
        formatted_string = super().format(record)
        prefix = self.PREFIX.get(record.levelno, "[-]")
        return f"{prefix} {formatted_string}"


def turn_on_logging(debug: bool = False):
    """Enable the console logging config."""
    logger = logging.getLogger("webnovel")
    handler = Handler()
    formatter = logging.Formatter("%(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)


class Namespace(dict):
    """A simple wrapper around dict that allows accessing items as attributes."""

    def __getattr__(self, name):
        """Return items via __getitem__ if it's not a pre-existing attribute on self."""
        if name in self:
            return self[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute {name!r}")

    def __setattr__(self, name, value):
        """Allow setting of attributes to be handled via __setitem__."""
        self[name] = value
