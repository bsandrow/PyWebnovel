"""Command-line Interface for PyWebNovel."""

from pathlib import Path

import click

from webnovel import conf
from webnovel.actions import App

from .base import auto_add_commands, turn_on_logging


@click.group()
@click.option("--config-file", "config_path", default=None, help=f"Configuration file. (Default: {conf.CONFIG_FILE})")
@click.option("--debug/--no-debug", default=None, help="Enable/disable debugging output.")
@click.option("--user-agent", help="Set the User-Agent header for all requests.")
@click.option("--cookie", "cookies", metavar="VAR=VALUE", multiple=True, help="Set a cookie value.")
@click.option(
    "--format",
    metavar="FORMAT",
    default=None,
    help="Specify the format of the ebook. Currently only 'epub' is supported.",
)
@click.pass_context
def pywn(ctx, config_path, debug, user_agent, cookies, format):
    """
    Create, edit and update ebooks of webnovels.

    NOTE: Only ebooks created by PyWebnovel can be managed in this way as
          application data is stored in a JSON file within the ebook itself.
    """
    if config_path is not None and not Path(config_path).exists():
        ctx.fail(f"File does not exist: {config_path}")

    settings = conf.Settings.load(config_path)

    if debug is not None:
        settings.debug = debug

    if format:
        settings.format = format

    if user_agent:
        settings.user_agent = user_agent

    for cookie in cookies:
        name, _, value = cookie.partition("=")
        settings.cookies[name] = value

    turn_on_logging(debug)

    ctx.obj = app = App(settings)


auto_add_commands(pywn, package=__name__)
