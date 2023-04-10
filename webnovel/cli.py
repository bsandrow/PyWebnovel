"""The command-line interface to PyWebnovel."""

import click

from webnovel import actions, turn_on_logging


class Namespace(dict):
    """A simple wrapper around dict that allows accessing items as attributes."""

    def __getattr__(self, name):
        """Return items via __getitem__ if it's not a pre-existing attribute on self."""
        if name in self:
            return self[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute {name!r}")

    def __setattr__(self, name, value):
        """Allow setting of attributes to be handled via __setitem__."""
        self[name] = value


@click.group()
@click.option("--debug/--no-debug", default=False, help="Enable/disable debugging output.")
@click.option(
    "--format",
    metavar="FORMAT",
    default="epub",
    help="Specify the format of the ebook. Currently only 'epub' is supported.",
)
@click.pass_context
def pywn(ctx, debug, format):
    """
    Create, edit and update ebooks of webnovels.

    NOTE: Only ebooks created by PyWebnovel can be managed in this way as
          application data is stored in a JSON file within the ebook itself.
    """
    ctx.ensure_object(Namespace)
    ctx.obj.debug = debug
    ctx.obj.format = format


@pywn.command()
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
@click.pass_obj
def create(opts, novel_url, filename, chapter_limit, cover_image):
    """Create an ebook file from NOVEL_URL."""
    turn_on_logging()
    actions.create_epub(
        novel_url,
        filename,
        cover_image_url=cover_image,
        chapter_limit=chapter_limit,
    )


@pywn.command()
@click.argument("ebook")
@click.option("--limit", type=int, default=None)
@click.pass_obj
def update(opts, ebook, limit):
    """Update EBOOK with any new chapters that have been published."""
    turn_on_logging()
    actions.update(ebook, limit)


@pywn.command()
@click.argument("ebook")
@click.option(
    "--reload-chapter",
    "reload_chapters",
    metavar="SLUG",
    multiple=True,
    help="Redownload / process the specified chapter(s)",
)
@click.pass_obj
def rebuild(opts, ebook, reload_chapters):
    """
    Rebuild an existing ebook.

    This is useful if the building code (e.g. the xhtml templates) have changed
    and you want to update the ebook without building a completely new ebook
    from scratch which would include re-downloading all chapters, images, etc.
    """
    turn_on_logging()
    actions.rebuild(ebook, reload_chapters=reload_chapters)


@pywn.command()
@click.argument("ebook")
@click.argument("cover_image")
@click.pass_obj
def set_cover(opts: Namespace, ebook: str, cover_image: str) -> None:
    """
    Set the cover image for EBOOK.

    COVER_IMAGE can be a path to an image file or a URL.
    """
    click.echo("GOT HERE!")
    turn_on_logging()
    actions.set_cover_image_for_epub(ebook, cover_image)
