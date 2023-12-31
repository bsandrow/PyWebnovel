"""Command: dir update."""

import click

from webnovel import events
from webnovel.actions import App

from ..base import CliUIBase, pass_app


@click.command()
@pass_app
def update(app: App) -> None:
    """Update webnovel directory."""
    CliUI()
    app.dir_update(app.settings.directory_options.directory)


class CliUI(CliUIBase):
    """Command-line Interface UI for Webnovel Directory Update command."""

    current_novel: str = None
    suffix: str = ""
    event_map: dict[events.Event, str] = {
        events.Event.WEBNOVEL_DIR_NOVEL_UPDATE_START: "update_start",
        events.Event.WN_UPDATE_NEW_CHAPTER_COUNT: "new_chapter_count",
        events.Event.WN_CHAPTER_BATCH_START: "chapter_batch_start",
        events.Event.WEBNOVEL_DIR_SKIP_PAUSED_NOVEL: "skip_paused_novel",
        events.Event.WEBNOVEL_DIR_SKIP_COMPLETE_NOVEL: "skip_complete_novel",
        events.Event.WN_UPDATE_NO_NEW_CHAPTERS: "no_new_chapters",
        events.Event.WEBNOVEL_DIR_NOVEL_UPDATE_END: "update_end",
    }

    def clear(self):
        """Clear the current state start a new line."""
        self.current_novel = None
        self.suffix = ""
        click.echo("", nl=True)

    def echo(self, prefix: str = None, suffix: str = None) -> str:
        """Print the current state of the app."""
        line = "\r"
        line += prefix if prefix else ""
        line += self.current_novel
        line += self.suffix if self.suffix else ""
        line += suffix if suffix else ""
        click.echo(line, nl=False)

    def update_start(self, ctx):
        """Start updating a novel in the webnovel directory."""
        self.current_novel = ctx.novel.path.name
        self.echo(suffix="...")

    def update_end(self, ctx):
        """Finish updating a novel in the webnovel directory."""
        if self.current_novel is not None:
            self.clear()

    def no_new_chapters(self, ctx):
        """Handle no new chapters for webnovel."""
        self.suffix += " " + click.style("[new: 0]", fg="black", bold=True)
        self.echo()
        self.clear()

    # def skip_complete_novel(self, ctx):
    #     """Handle a novel skipped because it's completed."""
    #     self.suffix += " " + click.style("[complete]", fg="black", bold=True)
    #     self.echo()
    #     self.clear()

    def skip_paused_novel(self, ctx):
        """Handle a novel skipped because it's paused."""
        self.current_novel = ctx.novel.path.name
        self.suffix += " " + click.style("[paused]", fg="black", bold=True)
        self.echo()
        self.clear()

    def new_chapter_count(self, ctx):
        """Handle update to new chapter count."""
        self.suffix += " " + click.style(f"[new: {ctx.new}]", fg="green", bold=True)
        self.echo()

    def chapter_batch_start(self, ctx):
        """Handle start of processing a batch of chapters."""
        self.suffix += " " + click.style(f"[batch: {ctx.batch_no}/{ctx.total_batches}]")
        self.echo()
        # suffix = f" [batch: {ctx.batch_no}/{ctx.total_batches}]" if ctx.total_batches > 1 else ""
        # is_last_batch = ctx.batch_no != ctx.total_batches
        # click.secho(f" » Scraping {ctx.batch_size} chapter(s)" + suffix, fg="magenta", nl=is_last_batch)
