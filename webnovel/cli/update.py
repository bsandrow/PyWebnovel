"""Command: update."""

import click

from webnovel import events
from webnovel.actions import App

from .base import CliUIBase, pass_app


@click.command()
@click.argument("ebook")
@click.option("--limit", type=int, default=None)
@pass_app
def update(app: App, ebook, limit):
    """Update EBOOK with any new chapters that have been published."""
    CliUI()
    app.update(ebook, limit)


class CliUI(CliUIBase):
    """Command-line Interface UI for Webnovel Directory Update command."""

    current_novel: str = None
    suffix: str = ""
    event_map: dict[events.Event, str] = {
        events.Event.WN_UPDATE_START: "update_start",
        events.Event.WN_UPDATE_NEW_CHAPTER_COUNT: "new_chapter_count",
        events.Event.WN_CHAPTER_BATCH_START: "chapter_batch_start",
    }

    def update_start(self, ctx: events.Context) -> None:
        """Handle start of the update."""
        click.secho(f"Updating {ctx.path.name}...", bold=True)

    def new_chapter_count(self, ctx: events.Context) -> None:
        """Handle addition of the cound of new chapters found."""
        click.echo(f" » Found {ctx.new} new chapter(s).")

    def chapter_batch_start(self, ctx: events.Context) -> None:
        """Handle the start of processing a batch of chapters."""
        click.echo(f" » Downloading Batch #{ctx.batch_no}: " f'"{ctx.batch[0].title}" -> "{ctx.batch[-1].title}"')
