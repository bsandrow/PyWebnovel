"""Command: dir info."""

import click

from webnovel.actions import App

from ..base import pass_app


@click.command()
@click.argument("epub_or_url")
@pass_app
def info(app: App, epub_or_url: str) -> None:
    """Display information about the webnovel directory."""
