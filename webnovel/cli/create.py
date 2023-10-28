"""Command: create."""

import click

from webnovel.actions import App

from .base import pass_app


@click.command()
@click.argument("novel_url")
@click.option(
    "--filename",
    "-f",
    help="The filename to save the ebook as. Defaults to: {{TITLE}}.{{EXTENSION}}",
)
@click.option(
    "--chapter-limit", default=None, type=int, help="Set the maximum number of chapters to build into the ebook."
)
@click.option(
    "--cover-image",
    help=(
        "Provide an alternative cover image to override the cover image "
        "parsed from the novel page. This should be a URL. In the future, "
        "providing a path to an image file will also be supported."
    ),
)
@pass_app
def create(app, novel_url, filename, chapter_limit, cover_image):
    """Create an ebook file from NOVEL_URL."""
    app.create_ebook(
        novel_url,
        filename,
        cover_image_url=cover_image,
        chapter_limit=chapter_limit,
    )
