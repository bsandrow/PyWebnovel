"""Command group: dir."""

import click

from webnovel.actions import App

from ..base import auto_add_commands, pass_app


@click.group()
@pass_app
def dir(app: App) -> None:
    """Command for managing directories of webnovels."""


auto_add_commands(group=dir, package=__name__)
