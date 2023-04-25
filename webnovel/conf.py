"""PyWebnovel Configuration."""

from configparser import ConfigParser
from dataclasses import dataclass, field, fields
from pathlib import Path

from webnovel import utils

CONFIG_DIR = Path("~/.config/pywebnovel")
CONFIG_FILE = CONFIG_DIR / "settings.ini"


@dataclass
class ParsingOptions(utils.DataclassSerializationMixin):
    """Options that control parsing of HTML content from sites."""

    # Control whether or not to include "Author's Notes" sections in the chapter
    # content, or to remove it entirely.
    include_authors_notes: bool = True

    # Control which html parsr to use with BeautifulSoup. Default is the
    # built-in html.parser. This is not meant to be exposed to users (e.g. via
    # the command-line)
    html_parser: str = "html.parser"


@dataclass
class Settings(utils.DataclassSerializationMixin):
    """Overall application settings for PyWebnovel."""

    #
    # All of the parsing-related options grouped togther. Note that these are
    # grouped together so that they can be serialized into the pywebnovel.json
    # in the ebook. There are many other settings that don't make sense to embed
    # into the book (for example paths to files in the local filesystem are not
    # portable and wouldn't make sense to embed in the ebook).
    #
    parsing_options: ParsingOptions = field(default_factory=ParsingOptions)

    #
    # Debug mode
    #
    debug: bool = False

    #
    # The ebook format to use. Currently only epub is supported, but other
    # formats could be added in the future. This could also be changed to epub2
    # / epub3 as a way of controlling the epub version.
    #
    format: str = "epub"

    #
    #
    #
    cookies: dict = field(default_factory=dict)

    #
    # User-Agent string used for requests.Session
    #
    user_agent: str | None = None

    def __str__(self):
        # TODO cookies
        parts = [f"item = {repr(getattr(self, item))}" for item in ("format", "debug", "user_agent")]
        for name, value in self.parsing_options.to_dict().items():
            parts.append(f"parsing_options.{name} = {repr(value)}")
        return "\n".join(parts)

    @classmethod
    def load(cls, filename=None) -> "Settings":
        """Load config settings from a file."""
        kwargs = {}
        cookies = {}
        parsing_options_kwargs = {}
        config = ConfigParser()
        filename = Path(filename) if filename else CONFIG_FILE

        if filename.exists():
            with open(filename, "r") as fh:
                config.read_string(fh.read())

            if "pywn" in config:
                for fname in ("debug", "format"):
                    if fname in config["pywn"]:
                        kwargs[fname] = config["pywn"][fname]

            if "pwyn.cookies" in config:
                section = config["pywn.cookies"]
                for cookie_name, cookie_value in section.items():
                    cookies[cookie_name] = cookie_value

            if "pywn.parsing_options" in config:
                section = config["pywn.parsing_options"]
                for field in fields(ParsingOptions):
                    if field.name in section:
                        parsing_options_kwargs[field.name] = section[field.name]

        if parsing_options_kwargs:
            kwargs["parsing_options"] = ParsingOptions(**parsing_options_kwargs)

        if cookies:
            kwargs["cookies"] = cookies

        return cls(**kwargs)