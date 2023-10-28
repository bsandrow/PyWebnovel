"""Command: dir update."""

import click

from webnovel.actions import App

from ..base import pass_app


@click.command()
@click.argument("directory")
@pass_app
def update(app: App, directory: str) -> None:
    """Update webnovel directory."""
    app.dir_update(directory)
