"""Command: set."""

import enum
import logging

import click

from webnovel import actions, data

from .base import pass_app

logger = logging.getLogger(__name__)


class EnumChoice(click.Choice):
    """A wrapper around Choice that allows an Enum to be used."""

    def __init__(self, enum) -> None:
        super().__init__(map(lambda x: str(x.value), enum))
        self.enum = enum

    def convert(self, value, param, ctx):
        """Convert the value from an instance of the Enum."""
        value = super().convert(value, param, ctx)
        return self.enum(value)


class Variable(enum.Enum):
    """The choices for a property to set from the CLI."""

    COVER = "cover"
    TITLE = "title"


@click.command()
@click.argument("variable", metavar="VAR", type=EnumChoice(Variable))
@click.argument("value")
@click.argument("ebook")
@pass_app
def setprop(app: actions.App, variable: str, value: str, ebook: str) -> None:
    """Set a value on the ebook."""
    if variable == Variable.COVER:
        actions.set_cover_image_for_epub(ebook, value)
    else:
        actions.set_title_for_epub(ebook, value)
