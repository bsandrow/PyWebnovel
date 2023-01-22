"""Define all of the basic datastructures we'll use to pass novels around."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class NovelStatus(Enum):
    ONGOING = "On Going"
    HIATUS = "Hiatus"
    DROPPED = "Dropped"
    COMPLETED = "Completed"
    UNKNOWN = "Unknown"


@dataclass
class Image:
    url: str
    data: bytes = None
    mimetype: str = None
    did_load: bool = False  # True if data/mimetype were loaded from the URL.

    extension_map = {
        "image/png": ".png",
        "image/jpg": ".jpg",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }

    @property
    def extension(self):
        return None if self.mimetype is None else self.extension_map[self.mimetype]

    def load(self, force: bool = False) -> bool:
        """
        Download the image from the URL, populating data and mimetype fields.

        Returns a boolean indicating if a load was performed.

        :param force: (optional) Force the load to happen even if the data/mimetype fields are already populated.
            Defaults to false.
        """
        if not self.did_load or force:
            from webnovel.scraping import http_client
            response = http_client.get(self.url)
            response.raise_for_status()
            self.data = response.content
            content_type = response.headers["content-type"]
            self.mimetype, _, _ = content_type.lower().partition(";")
            self.did_load = True
            return True
        return False


@dataclass
class Person:
    name: str
    email: str = None
    url: str = None


@dataclass
class Chapter:
    url: str
    title: str = None
    chapter_no: str = None


@dataclass
class Novel:
    url: str
    title: str = None
    status: NovelStatus = None
    summary: str = None
    genres: list[str] = None
    tags: list[str] = None
    author: Optional[Person] = None
    translator: Person = None
    chapters: list[Chapter] = None
    cover_image: Image = None
