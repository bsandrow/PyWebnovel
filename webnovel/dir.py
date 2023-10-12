"""Managed directory of web novels."""

from dataclasses import dataclass, field
import datetime
import enum
from functools import cached_property
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union
import zipfile

from requests import HTTPError

from webnovel.errors import DirectoryDoesNotExistError

if TYPE_CHECKING:
    from webnovel.actions import App


logger = logging.getLogger(__name__)


class WebNovelStatus(enum.Enum):
    """The status of a webnovel managed by the webnovel directory."""

    ONGOING = "ongoing"
    PAUSED = "paused"
    COMPLETE = "complete"


@dataclass
class WebNovel:
    """A Webnovel ebook inside of the WebNovelDirectory."""

    path: Path
    status: WebNovelStatus = WebNovelStatus.ONGOING
    last_updated: Optional[datetime.datetime] = None

    def to_json(self) -> dict:
        """Convert to dict."""
        return {
            "path": str(self.path),
            "status": self.status.value,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    @classmethod
    def from_json(cls: type["WebNovel"], data: dict) -> "WebNovel":
        """Convert from dict."""
        return cls(
            path=Path(data["path"]),
            status=WebNovelStatus(data["status"]) if data.get("status") else WebNovelStatus.ONGOING,
            last_updated=datetime.datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else None,
        )


def is_pywebnovel_epub(path: Union[str, Path]) -> bool:
    """Check an epub file for pywebnovel.json to see if it's a managed by PyWebnovel."""
    path = Path(path)
    if not zipfile.is_zipfile(path):
        return False
    # with zipfile.Zipfile(path, "r") as zf:
    return zipfile.Path(path, at="pywebnovel.json").exists()


@dataclass
class WebNovelDirectoryStatus:
    """Representation of the status of a WebNovelDirectory."""

    webnovels: list[WebNovel] = field(default_factory=list)
    last_run: Optional[datetime.datetime] = None

    @classmethod
    def from_json(cls, data: dict) -> "WebNovelDirectoryStatus":
        """Load from dict."""
        return cls(
            webnovels=[WebNovel.from_json(a) for a in data["webnovels"]],
            last_run=datetime.datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
        )

    def to_json(self) -> dict:
        """Convert to dict."""
        return {
            "webnovels": [wn.to_json() for wn in self.webnovels],
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }


class WebNovelDirectory:
    """A directory of webnovel files for batch processing."""

    directory: Path

    def __init__(self, directory: Union[str, Path]) -> None:
        self.directory = Path(directory)

    @property
    def status_file(self) -> Path:
        """Return a Path of the status file."""
        return self.directory / "status.json"

    @cached_property
    def status(self) -> WebNovelDirectoryStatus:
        """Return an instance of WebNovelDirectoryStatus either from file, or build a new one."""
        if self.status_file.exists():
            with self.status_file.open("r") as fh:
                string_data = fh.read()
                if string_data.strip():
                    data = json.loads(string_data)
                    return WebNovelDirectoryStatus.from_json(data)

        webnovels = []
        for epub_file in self.directory.glob("*.epub"):
            if is_pywebnovel_epub(epub_file):
                webnovels.append(WebNovel(path=epub_file))
        return WebNovelDirectoryStatus(webnovels=webnovels)

    def save(self):
        """Save the status of the WebNovelDirectory."""
        with self.status_file.open("w") as fh:
            data = self.status.to_json()
            fh.write(json.dumps(data))

    @classmethod
    def load(cls, directory: Union[str, Path]) -> "WebNovelDirectory":
        """
        Load a WebNovelDirectory from an existing directory.

        :params directory: The path to the directory to load.
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise DirectoryDoesNotExistError
        return cls(directory)

    @classmethod
    def create(cls, directory: Union[str, Path]) -> "WebNovelDirectory":
        """
        Create a new WebNovelDirectory.

        :params directory: The path to the webnovel directory to create.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return cls(directory)

    def validate(self) -> bool:
        """Validate if this is a WebNovelDirectory or not."""
        return self.directory.is_dir()

    def update(self, app: "App") -> None:
        """Run App.update on all of the webnovels in this directory."""
        for webnovel in self.status.webnovels:
            try:
                chapters_added = app.update(ebook=webnovel.path, ignore_path=self.directory)
                if chapters_added > 0:
                    webnovel.last_updated = datetime.datetime.now()
                self.save()
            except HTTPError as error:
                print(f"HTTP Error: {error.response.status_code} on URL {error.request.url!r}")
        self.status.last_run = datetime.datetime.now()

    def add(self, epub_or_url: str, app: "App") -> None:
        """Add webnovel to directory."""
        if epub_or_url.startswith("http"):
            filename = Path(app.create_ebook(novel_url=epub_or_url, directory=self.directory))
        elif (path := Path(epub_or_url)) and path.exists():
            filename = path
        else:
            raise Exception()  # TODO better error here

        webnovel = WebNovel(path=filename, last_updated=datetime.datetime.now())
        self.status.webnovels.append(webnovel)
        self.save()
        logger.info("Webnovel %s added to directory.", filename.name)
