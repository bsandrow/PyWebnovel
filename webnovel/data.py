"""Define all of the basic datastructures we'll use to pass novels around."""

from dataclasses import dataclass
from enum import Enum
import imghdr
from io import BytesIO
import re
from typing import Optional

from apptk.http import HttpClient
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

    def load(self, force: bool = False, client: HttpClient = None) -> bool:
        """
        Download the image from the URL, populating data and mimetype fields.

        Returns a boolean indicating if a load was performed.

        :param force: (optional) Force the load to happen even if the data/mimetype fields are already populated.
            Defaults to false.
        """
        if not self.did_load or force:
            if client is None:
                from webnovel.scraping import http_client as client
            # Accept headers prefer png or jpg over other formats. This mostly works to avoid WEBP when the server
            # is able to serve PNG or JPEG instead.
            response = client.get(self.url, headers={"Accept": "*/*, image/jpeg, image/png"})
            response.raise_for_status()
            self.data = response.content
            content_type = response.headers["content-type"]
            if content_type not in self.extension_map:
                image_type = imghdr.what(file=None, h=self.data)
                if image_type:
                    self.mimetype = "image/" + image_type
                else:
                    raise Exception("ERROR")
            else:
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

    def to_dict(self) -> dict:
        """Convert to a dictionary."""
        return {"name": self.name, "email": self.email, "url": self.url}


@dataclass
class Chapter:
    """Representation of a chapter of a webnovel."""

    url: str
    title: Optional[str] = None
    chapter_no: Optional[str] = None
    slug: Optional[str] = None
    html_content: Optional[Tag] = None

    @staticmethod
    def clean_title(title: str) -> str:
        """Cleanup a Chapter title to normalize it a bit, detect common typos, etc."""
        title = title.strip()

        # Change "100 The Black Dragon" => "Chapter 100 The Black Dragon"
        if re.match(r"\d+", title):
            title = f"Chapter {title}"

        # Change "Chapter 100 - The Black Dragon" => "Chapter 100: The Black Dragon"
        title = re.sub(r"(Chapter\s*\d+) - ", r"\1: ", title)

        # Deal with "Chapter Ch 102"
        title = re.sub(r"(Chapter)\s*Ch\s*(\d+)", "\1 \2", title, re.IGNORECASE)

        # Deal with "Chapter 100The Black Dragon" => "Chapter 100: The Black Dragon"
        # TODO replace a-zA-Z with unicode character class using \p{L} (requires separate regex library)
        title = re.sub(r"(Chapter \d+)([a-zA-Z]{3,})", r"\1: \2", title, re.IGNORECASE)

        # Change "Chapter 100 The Black Dragon" => "Chapter 100: The Black Dragon"
        title = re.sub(r"^(Chapter )?(\d+) ([“”\w])", r"\1\2: \3", title, re.IGNORECASE)

        # Fix "Chapter 761: - No Openings" => "Chapter 761: No Openings"
        title = title.replace(": - ", ": ")

        # Change "Chapter 100: 100 The Black Dragon" => "Chapter 100: The Black Dragon"
        # -- it's possible for false matches here, but I'm deeming the likelihood low since
        #    it would have to be an exact match for the chapter number. E.g.:
        #       "Chapter 99: 99 Bottles of Beer on the Wall" =>
        #       "Chapter 99: Bottle of Beer on the Wall"
        title = re.sub(r"Chapter (\d+): \1 *", r"Chapter \1: ", title, re.IGNORECASE)

        return title

    @staticmethod
    def extract_chapter_no(title: str) -> str:
        """Extract a chapter number from the chapter title."""
        match = re.match(r"^\s*Chapter\s*(\d+(?:\.\d+)?)([.: ]|$)", title, re.IGNORECASE)
        chapter_no = match.group(1) if match is not None else None
        try:
            return int(chapter_no)
        except (ValueError, TypeError):
            print(f"Warning: Got bad chapter_no for title: {title}")
            return 0


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
