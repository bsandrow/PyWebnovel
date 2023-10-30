"""PyWebnovel Configuration."""

from configparser import ConfigParser
from dataclasses import dataclass, field, fields
import os
from pathlib import Path

from webnovel import utils

# from typing import Any, Callable


CONFIG_DIR = Path("~/.config/pywebnovel")
CONFIG_FILE = CONFIG_DIR / "settings.ini"


# @dataclass
# class EnvironmentVariable:
#     name: str
#     local: str
#     type: Callable[[Any], Any] = str


# DEFAULT_SETTINGS = {
#     "DEBUG": False,
#     "FORMAT": "epub",
#     "WEBNOVEL_DIRECTORY": None,
# }

# ENV_VARS = [
#     EnvironmentVariable("PYWEBNOVEL_DIR", "WEBNOVEL_DIRECTORY", Path),
#     EnvironmentVariable("PYWEBNVEOL_FORMAT", "FORMAT"),
#     EnvironmentVariable(
#         name="PYWEBNOVEL_DEBUG",
#         local="DEBUG",
#         type=lambda x: x.strip().lower() not in ("0", "", "false", "no", "none", "null", "off"),
#     )
# ]


@dataclass
class WebnovelDirectoryOptions(utils.DataclassSerializationMixin):
    """Options for handling webnovel directories."""

    # The default directory to use for webnovel directory operations.
    directory: str | Path | None = None


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


# class EnvironmentVariableSettings(dict):
#     """A dictionary populated from environment variables."""

#     @classmethod
#     def initialize(cls, env_vars: list[EnvironmentVariable]) -> "EnvironmentVariableSettings":
#         """Initialize the dictionary from a list of EnvironmentVariable instances."""
#         return cls(
#             **{
#                 environment_variable.local: environment_variable.type(data)
#                 for environment_variable in env_vars
#                 if environment_variable.name in os.environ and (data := os.environ[environment_variable.name])
#             }
#         )


# class SettingsProxyObject:
#     _settings_groups: list[dict] = None


#     def __init__(self) -> None:
#         self._settings_groups = [
#             EnvironmentVariableSettings.initialize(ENV_VARS),
#             DEFAULT_SETTINGS,
#         ]

#     def __getattr__(self, name: str) -> None:
#         for settings_group in self._settings_groups:
#             if name in settings_group:
#                 return settings_group[name]


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
    # Options to handling webnovel directories
    #
    directory_options: WebnovelDirectoryOptions = field(default_factory=WebnovelDirectoryOptions)

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
        webnovel_directory_kwargs = {}
        config = ConfigParser()
        filename = Path(filename) if filename else CONFIG_FILE

        if filename.exists():
            with open(filename, "r") as fh:
                config.read_string(fh.read())

            if "pywn" in config:
                for fname in ("debug", "format"):
                    if fname in config["pywn"]:
                        kwargs[fname] = config["pywn"][fname]

            if "pywn.directory" in config:
                section = config["pywn.directory"]
                for field in fields(WebnovelDirectoryOptions):
                    if field.name in section:
                        webnovel_directory_kwargs[field.name] = section[field.name]

            if "pywn.cookies" in config:
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

        if webnovel_directory_kwargs:
            kwargs["directory_options"] = WebnovelDirectoryOptions(**webnovel_directory_kwargs)

        if cookies:
            kwargs["cookies"] = cookies

        return cls(**kwargs)
