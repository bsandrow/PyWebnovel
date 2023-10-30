"""Command: dir update."""

import click

from webnovel.actions import App

from ..base import pass_app


@click.command()
@pass_app
def update(app: App) -> None:
    """Update webnovel directory."""
    app.dir_update(app.settings.webnovel_directory)
