"""Command: dir clean."""

from pathlib import Path

import click

from webnovel import events
from webnovel.actions import App

from ..base import pass_app


@click.command()
@click.argument("epub_or_url")
@pass_app
def add(app: App, epub_or_url: str) -> None:
    """Add a webnovel to directory."""
    app.dir_clean(app.settings.directory_options.directory)


def handle_chapter_batch(ctx: events.Context) -> None:
    """Handle the PROCESS_CHAPTER_BATCH_START event."""
    suffix = f" [batch: {ctx.batch_no}/{ctx.total_batches}]" if ctx.total_batches > 1 else ""
    click.secho(f" » Scraping {ctx.batch_size} chapter(s)" + suffix, fg="magenta")
