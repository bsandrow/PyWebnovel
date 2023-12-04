"""Helpers for webnovel.cli."""

import logging
from types import ModuleType

from apptk.importing import import_all_from_submodules
import click

from webnovel import events
from webnovel.actions import App
from webnovel.utils import Namespace

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

    handler.setLevel(logging.DEBUG if debug else logging.WARNING)
    logger.setLevel(logging.DEBUG if debug else logging.WARNING)


class CliUIBase:
    """
    Base class for Command-line Interface UI.

    Allows for "packaging" a bunch of event handlers into a single class. This
    allows the event handlers to have a shared state between each other.
    """

    event_map = {event: event.name.lower() for event in events.Event}

    def __init__(self, delay_registry: bool = False) -> None:
        """
        Initialize the Cli UI.

        :param delay_registry: A boolean that controls if callbacks should be
                               registered to events during __init__, or if the
                               caller will register them manually later.
                               Defaults to False.
        """
        if not delay_registry:
            self.register()

    def register(self):
        """
        Register methods in event_map to their matching events.

        methods can be either direct references to a callable, or a string with
        the name of a method on self.
        """
        for event, callable_or_method_name in self.event_map.items():
            if isinstance(callable_or_method_name, str):
                method = getattr(self, callable_or_method_name, None)
                if method is not None and callable(method):
                    events.register(event=event, callback=method)
            elif callable(callable_or_method_name):
                events.register(event=event, callback=method)
            else:
                raise ValueError(f"{callable_or_method_name!r} needs to either be a string or a callable.")
