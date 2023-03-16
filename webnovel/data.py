"""Define all of the basic datastructures we'll use to pass novels around."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from bs4 import Tag


class NovelStatus(Enum):
    """Representation of the status of a webnovel."""

    ONGOING = "On Going"
    HIATUS = "Hiatus"
    DROPPED = "Dropped"
    COMPLETED = "Completed"
    UNKNOWN = "Unknown"


@dataclass
class Image:
    """An (web-hosted) Image."""

    url: str
    data: Optional[bytes] = None
    mimetype: Optional[str] = None
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
        """Return the filename extension to use for this image (based on the mime-type)."""
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
    """
    A Person associated with a novel.

    A generic class meant to represent any person that might be associated with
    a webnovel (e.g. author, translator, editor, etc). Rather than just having a
    string field with the name of the person, this allows for a URL and/or email
    to be associated with the person.

    This allows credits information generated at the start of the ebooks to also
    contain this information. For example, the author's name could be wrapped in
    a link if the url is provided, or the author's name could be formatted as::

      Author Name <author.name@gmail.com>

    if the email was provided.
    """

    name: str
    email: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Chapter:
    """Representation of a chapter of a webnovel."""

    url: str
    title: Optional[str] = None
    chapter_no: Optional[str] = None
    slug: Optional[str] = None
    html_content: Optional[Tag] = None


@dataclass
class Novel:
    """Representation of the webnovel itself."""

    url: str
    novel_id: str
    site_id: Optional[str] = None
    title: Optional[str] = None
    status: Optional[NovelStatus] = None
    summary: Optional[str] = None
    genres: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    author: Optional[Person] = None
    translator: Optional[Person] = None
    chapters: Optional[list[Chapter]] = None
    cover_image: Optional[Image] = None
