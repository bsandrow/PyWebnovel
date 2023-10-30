"""Command group: dir."""

import pathlib

import click

from webnovel.actions import App

from ..base import auto_add_commands, pass_app


@click.group()
@click.option("--directory", default=None, help=f"Set the directory to use as the webnovel directory.")
@pass_app
def dir(app: App, directory: str | None) -> None:
    """Command for managing directories of webnovels."""
    if directory:
        app.settings.directory_options.directory = pathlib.Path(directory).expanduser()


auto_add_commands(group=dir, package=__name__)
