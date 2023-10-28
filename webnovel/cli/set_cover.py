"""Command: set-cover."""

import click

from webnovel.actions import App

from .base import pass_app


@click.command()
@click.argument("ebook")
@click.argument("cover_image")
@pass_app
def set_cover(app: App, ebook: str, cover_image: str) -> None:
    """
    Set the cover image for EBOOK.

    COVER_IMAGE can be a path to an image file or a URL.
    """
    app.set_cover_image_for_epub(ebook, cover_image)
