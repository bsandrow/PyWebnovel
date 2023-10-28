"""Command: dir add."""

import click

from webnovel.actions import App

from ..base import pass_app


@click.command()
@click.argument("directory")
@click.argument("epub_or_url")
@pass_app
def add(app: App, directory: str, epub_or_url: str) -> None:
    """Add a webnovel to directory."""
    app.dir_add(directory, epub_or_url)
