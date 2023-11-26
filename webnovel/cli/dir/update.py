"""Command: dir update."""

import click

from webnovel import events
from webnovel.actions import App

from ..base import pass_app


@click.command()
@pass_app
def update(app: App) -> None:
    """Update webnovel directory."""
    events.register(
        event=events.Event.WEBNOVEL_DIR_NOVEL_UPDATE_START,
        callback=lambda ctx: click.echo(f"{ctx.novel.path.name}...", nl=False),
    )
    events.register(
        event=events.Event.WEBNOVEL_DIR_SKIP_PAUSED_NOVEL,
        callback=lambda ctx: click.secho(f"{ctx.novel.path.name} [paused]", fg="black", bold=True),
    )
    events.register(
        event=events.Event.WEBNOVEL_DIR_SKIP_COMPLETE_NOVEL,
        callback=lambda ctx: click.secho(f"{ctx.novel.path.name} [complete]", fg="black", bold=True),
    )
    events.register(
        event=events.Event.WEBNOVEL_UPDATE_NO_NEW_CHAPTERS,
        callback=lambda ctx: click.secho(f"\r{ctx.path.name} [no updates]", fg="black", bold=True, nl=False),
    )
    events.register(
        event=events.Event.WEBNOVEL_UPDATE_NEW_CHAPTER_COUNT,
        callback=lambda ctx: click.secho(f"\r{ctx.path.name} [New Chapters: {ctx.new}]...", fg="green"),
    )
    events.register(event=events.Event.PROCESS_CHAPTER_BATCH_START, callback=handle_chapter_batch)
    events.register(event=events.Event.WEBNOVEL_DIR_NOVEL_UPDATE_END, callback=lambda ctx: click.echo("", nl=True))
    app.dir_update(app.settings.directory_options.directory)


def handle_chapter_batch(ctx: events.Context) -> None:
    """Handle the PROCESS_CHAPTER_BATCH_START event."""
    suffix = f" [batch: {ctx.batch_no}/{ctx.total_batches}]" if ctx.total_batches > 1 else ""
    is_last_batch = ctx.batch_no != ctx.total_batches
    click.secho(f" » Scraping {ctx.batch_size} chapter(s)" + suffix, fg="magenta", nl=is_last_batch)
