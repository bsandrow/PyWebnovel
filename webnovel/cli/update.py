"""Command: update."""

import click

from webnovel.actions import App

from .base import pass_app


@click.command()
@click.argument("ebook")
@click.option("--limit", type=int, default=None)
@pass_app
def update(app, ebook, limit):
    """Update EBOOK with any new chapters that have been published."""
    app.update(ebook, limit)
