"""Managed directory of web novels."""

from dataclasses import dataclass, field
import datetime
import enum
from functools import cached_property
import logging
import os.path
from pathlib import Path
from typing import TYPE_CHECKING, Union
import zipfile

from apptk.files import cwd
from requests import HTTPError

from webnovel import data, events, utils
from webnovel.errors import DirectoryDoesNotExistError

if TYPE_CHECKING:
    from webnovel.actions import App


logger = logging.getLogger(__name__)


class WNDVersion(enum.Enum):
    """WebNovelDirectory version."""

    v1 = 1
    v2 = 2


class WebNovelStatus(enum.Enum):
    """The status of a webnovel managed by the webnovel directory."""

    ONGOING = "ongoing"
    PAUSED = "paused"
    DROPPED = "dropped"
    COMPLETE = "complete"


@dataclass
class WNDItem(utils.DataclassSerializationMixin):
    """A Webnovel ebook inside of the WebNovelDirectory."""

    #: The path to the webnovel (relative to the base directory).
    path: Path

    #: The current status of this webnovel.
    status: WebNovelStatus = WebNovelStatus.ONGOING

    #: The last time that this webnovel was updated
    last_updated: datetime.datetime | None = None

    @staticmethod
    def normalize_path(wn_path: Path, base_dir: Path) -> Path:
        """Make the path relative to the WebNovelDirectory."""
        return Path(os.path.relpath(str(wn_path), start=str(base_dir))) if wn_path.is_absolute() else wn_path

    def get_bucket_path(self) -> Path:
        """Return the directory of the bucket."""
        return Path(self.status.value)

    def update_bucket(self, basedir: Path):
        """Move the webnovel to the bucket for the current status."""
        with cwd(basedir):
            bucket = self.get_bucket_path()
            bucket.mkdir(parents=True, exist_ok=True)
            new_path = bucket / self.path.name
            self.path.rename(new_path)
            self.path = new_path


def is_pywebnovel_epub(path: Union[str, Path]) -> bool:
    """Check an epub file for pywebnovel.json to see if it's a managed by PyWebnovel."""
    path = Path(path)
    if not zipfile.is_zipfile(path):
        return False
    # with zipfile.Zipfile(path, "r") as zf:
    return zipfile.Path(path, at="pywebnovel.json").exists()


@dataclass
class WebNovelDirectory(utils.DataclassSerializationMixin):
    """Representation of the status of a WebNovelDirectory."""

    #: Path
    path: Path

    #: All of the webnovels
    webnovels: list[WNDItem] = field(default_factory=list)

    #: The last time that an update was run.
    last_run: datetime.datetime | None = None

    #: Status version. Used for dealing with changes to the format when it comes
    #: to loading/saving.
    version: WNDVersion | None = WNDVersion.v1

    @classmethod
    def from_path(cls, path: Path | str) -> "WebNovelDirectory":
        """
        Create a WebNovelDirectory from a path to a directory.

        :params path: The path to the webnovel directory.
        """
        path = Path(path)
        file = path / "status.json"

        if not path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        if not file.exists():
            return cls(path=path)

        with file.open("r") as fh:
            wnd = cls.from_json(fh.read())

        wnd.path = path
        return wnd


class WNDController:
    """A directory of webnovel files for batch processing."""

    directory: WebNovelDirectory

    def __init__(self, directory: WebNovelDirectory) -> None:
        self.directory = directory

    @classmethod
    def from_path(cls, path: Path | str) -> "WNDController":
        """
        Create a WNDController instance from a directory path.

        Automatically creates the WebNovelDirectory instance that the controller wraps.

        :params path: The path to the directory.
        """
        return cls(WebNovelDirectory.from_path(path))

    @property
    def status_file(self) -> Path:
        """Return a Path of the status file."""
        return self.directory.path / "status.json"

    def clean(self):
        """Cleanup Various Aspects of the webnovel directory."""
        for webnovel in self.directory.webnovels:
            print(f"[0] webnovel.path = {webnovel.path}")
            print(f"[0] self.directory.path = {self.directory.path}")
            webnovel.path = webnovel.normalize_path(webnovel.path, self.directory.path)
            print(f"[1] webnovel.path = {webnovel.path}")
            webnovel.update_bucket(self.directory.path)
            print(f"[2] webnovel.path = {webnovel.path}")
        self.save()

    def save(self):
        """Save the status of the WebNovelDirectory."""
        events.trigger(event=events.Event.WEBNOVEL_DIR_SAVE_START, context={"dir": self.directory}, logger=logger)
        with self.status_file.open("w") as fh:
            print(f"HERE: {self.status_file}")
            fh.write(self.directory.to_json(sort_keys=True, indent=2))
        events.trigger(event=events.Event.WEBNOVEL_DIR_SAVE_END, context={"dir": self.directory}, logger=logger)

    @classmethod
    def load(cls, directory: Union[str, Path]) -> "WNDController":
        """
        Load a WebNovelDirectory from an existing directory.

        :params directory: The path to the directory to load.
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise DirectoryDoesNotExistError
        return cls.from_path(directory)

    @classmethod
    def create(cls, directory: Union[str, Path]) -> "WNDController":
        """
        Create a new WebNovelDirectory.

        :params directory: The path to the webnovel directory to create.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return cls.from_path(directory)

    def validate(self) -> bool:
        """Validate if this is a WebNovelDirectory or not."""
        return self.directory.path.is_dir() and self.status_file.exists()

    def update(self, app: "App") -> None:
        """Run App.update on all of the webnovels in this directory."""
        events.trigger(event=events.Event.WEBNOVEL_DIR_UPDATE_START, context={"dir": self.directory})
        try:
            for webnovel in self.directory.webnovels:
                if webnovel.status == WebNovelStatus.COMPLETE:
                    events.trigger(
                        event=events.Event.WEBNOVEL_DIR_SKIP_COMPLETE_NOVEL,
                        context={"dir": self.directory, "novel": webnovel},
                        logger=logger,
                    )
                    continue

                if webnovel.status == WebNovelStatus.DROPPED:
                    continue

                if webnovel.status == WebNovelStatus.PAUSED:
                    events.trigger(
                        event=events.Event.WEBNOVEL_DIR_SKIP_PAUSED_NOVEL,
                        context={"dir": self.directory, "novel": webnovel},
                        logger=logger,
                    )
                    continue

                events.trigger(
                    event=events.Event.WEBNOVEL_DIR_NOVEL_UPDATE_START,
                    context={"dir": self.directory, "novel": webnovel},
                    logger=logger,
                )

                try:
                    chapters_added = app.update(ebook=webnovel.path, ignore_path=self.directory.path)
                    if chapters_added > 0:
                        webnovel.last_updated = datetime.datetime.now()
                    self.save()

                except HTTPError as error:
                    print(f"HTTP Error: {error.response.status_code} on URL {error.request.url!r}")

                finally:
                    events.trigger(
                        event=events.Event.WEBNOVEL_DIR_NOVEL_UPDATE_END,
                        context={"dir": self.directory, "novel": webnovel},
                        logger=logger,
                    )

            self.directory.last_run = datetime.datetime.now()
        finally:
            events.trigger(event=events.Event.WEBNOVEL_DIR_UPDATE_END, context={"dir": self.directory})

    def add(self, epub_or_url: str, app: "App") -> None:
        """Add webnovel to directory."""
        if epub_or_url.startswith("http"):
            filename = Path(app.create_ebook(novel_url=epub_or_url, directory=self.directory.path))
        elif (path := Path(epub_or_url)) and path.exists():
            filename = path
        else:
            raise Exception()  # TODO better error here

        webnovel = WNDItem(path=filename, last_updated=datetime.datetime.now())
        self.directory.webnovels.append(webnovel)
        self.save()
        events.trigger(
            event=events.Event.WEBNOVEL_DIR_WEBNOVEL_ADDED,
            context={"dir": self.directory, "webnovel": webnovel, "path": filename},
            logger=logger,
        )
