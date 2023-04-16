"""The command-line interface to PyWebnovel."""

import click

from webnovel import actions, http, turn_on_logging


class App:
    """Central Application for PyWebnovel."""

    debug: bool = False
    format: str = "epub"
    client: http.HttpClient

    def __init__(self, debug: bool = False, format: str = "epub"):
        self.debug = debug
        self.format = format
        self.client = http.get_client()

    def __getattr__(self, name: str):
        """Override attribute access to pass through to 'actions'."""
        try:
            return getattr(actions, name)
        except AttributeError:
            raise AttributeError(name)

    def set_user_agent(self, user_agent_string: str) -> None:
        """Set the User-Agent header on the session."""
        self.client._session.headers["User-Agent"] = user_agent_string

    def set_cookie(self, cookie_name: str, cookie_value: str) -> None:
        """Set a cookie name/value pair on the current session."""
        self.client._session.cookies.set(cookie_name, cookie_value)


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


# Make sure we are always passing App instance.
pass_app = click.make_pass_decorator(App)


@click.group()
@click.option("--debug/--no-debug", default=False, help="Enable/disable debugging output.")
@click.option("--user-agent", help="Set the User-Agent header for all requests.")
@click.option("--cookie", "cookies", metavar="VAR=VALUE", multiple=True, help="Set a cookie value.")
@click.option(
    "--format",
    metavar="FORMAT",
    default="epub",
    help="Specify the format of the ebook. Currently only 'epub' is supported.",
)
@click.pass_context
def pywn(ctx, debug, user_agent, cookies, format):
    """
    Create, edit and update ebooks of webnovels.

    NOTE: Only ebooks created by PyWebnovel can be managed in this way as
          application data is stored in a JSON file within the ebook itself.
    """
    ctx.obj = app = App(debug=debug, format=format)
    app.set_user_agent(user_agent)
    for cookie in cookies:
        name, _, value = cookie.partition("=")
        app.set_cookie(name, value)


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
@pass_app
def create(app, novel_url, filename, chapter_limit, cover_image):
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
@pass_app
def update(app, ebook, limit):
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
@pass_app
def rebuild(app, ebook, reload_chapters):
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
@pass_app
def set_cover(app: App, ebook: str, cover_image: str) -> None:
    """
    Set the cover image for EBOOK.

    COVER_IMAGE can be a path to an image file or a URL.
    """
    turn_on_logging()
    actions.set_cover_image_for_epub(ebook, cover_image)
