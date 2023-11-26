"""Command: dir add."""

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
    events.register(
        event=events.Event.WN_CREATE_START,
        callback=lambda ctx: click.echo(f"Creating ebook for: {ctx.novel_url}"),
    )
    events.register(
        event=events.Event.WN_CREATE_END,
        callback=lambda ctx: click.echo(f"Ebook created: {Path(ctx.ebook.filename).name}"),
    )
    events.register(event=events.Event.WN_CHAPTER_BATCH_START, callback=handle_chapter_batch)
    app.dir_add(app.settings.directory_options.directory, epub_or_url)


def handle_chapter_batch(ctx: events.Context) -> None:
    """Handle the PROCESS_CHAPTER_BATCH_START event."""
    suffix = f" [batch: {ctx.batch_no}/{ctx.total_batches}]" if ctx.total_batches > 1 else ""
    click.secho(f" » Scraping {ctx.batch_size} chapter(s)" + suffix, fg="magenta")
