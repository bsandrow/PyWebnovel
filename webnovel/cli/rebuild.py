"""Command: rebuild."""

import click

from webnovel.actions import App

from .base import pass_app


@click.command()
@click.argument("ebook")
@click.option(
    "--reload-chapter",
    "reload_chapters",
    metavar="SLUG",
    multiple=True,
    help="Redownload / process the specified chapter(s)",
)
@pass_app
def rebuild(app, ebook, reload_chapters):
    """
    Rebuild an existing ebook.

    This is useful if the building code (e.g. the xhtml templates) have changed
    and you want to update the ebook without building a completely new ebook
    from scratch which would include re-downloading all chapters, images, etc.
    """
    app.rebuild(ebook, reload_chapters=reload_chapters)
