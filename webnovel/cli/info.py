"""Command: info."""

import click

from webnovel.actions import App

from .base import pass_app


@click.command()
@click.argument("ebook")
@pass_app
def info(app: App, ebook: str) -> None:
    """Print out information about EBOOK."""
    info = app.info(ebook)
    click.echo(f"\nInfo for {ebook}:\n")
    max_key_size = max(len(key) for key in info)
    for key, value in info.items():
        click.echo(f" »» {key:{max_key_size + 1}s}: {value}")
    click.echo()
