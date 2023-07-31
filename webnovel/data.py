"""Define all of the basic datastructures we'll use to pass novels around."""

from dataclasses import dataclass
import datetime
from enum import Enum
import imghdr
import re
from typing import Callable, Union

from apptk.http import HttpClient
from bs4 import BeautifulSoup, Tag

from webnovel import html, utils


def check_if_jpeg(data: bytes) -> bool:
    """
    Check if data has a JPEG header.

    Source: https://stackoverflow.com/questions/36870661/imghdr-python-cant-detec-type-of-some-images-image-extension
    """
    JPEG_MARK = (
        b"\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07"
        b"\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f"
    )
    return (
        # JPEG data in JFIF format
        b"JFIF" in data[:23]
        # JPEG with small header
        or (len(data) >= 32 and 67 == data[5] and data[:32] == JPEG_MARK)
        # JPEG data in JFIF or Exif format
        or (data[6:10] in (b"JFIF", b"Exif") or data[:2] == b"\xff\xd8")
    )


def patch_imghdr():
    """
    Monkey patch in additional test for JPEG to imghdr to deal with buggy detection.

    Source: https://stackoverflow.com/questions/36870661/imghdr-python-cant-detec-type-of-some-images-image-extension
    """
    from imghdr import tests

    tests.append(lambda h, f: "jpeg" if check_if_jpeg(h) else None)


patch_imghdr()


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
    data: bytes | None = None
    mimetype: str | None = None
    did_load: bool = False  # True if data/mimetype were loaded from the URL.

    extension_map = {
        "image/png": ".png",
        "image/jpg": ".jpg",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/svg": ".svg",
    }

    @staticmethod
    def get_mimetype_from_image_data(data: bytes):
        """Get a mimetype string from a blob of image data."""
        if not data:
            raise ValueError("Cannot determine mimetype without image data.")

        image_type = imghdr.what(file=None, h=data)

        if not image_type:
            return None

        return f"image/{image_type}"

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
                from webnovel.http import get_client

                client = get_client()
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
                    raise Exception(
                        f"Unknown image type: image_type={image_type!r} content_type={content_type!r} url={self.url!r}"
                    )
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
    email: str | None = None
    url: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Person":
        """Load a Person instance from a dict."""
        return cls(**utils.filter_dict(data, ("name", "email", "url")))

    def to_dict(self) -> dict:
        """Convert to a dictionary."""
        return {"name": self.name, "email": self.email, "url": self.url}


@dataclass
class Chapter:
    """Representation of a chapter of a webnovel."""

    url: str
    title: str | None = None
    chapter_no: str | None = None
    slug: str | None = None
    original_html: str | None = None
    html: str | None = None
    filters: list[str] | None = None
    pub_date: datetime.date | None = None

    def to_dict(self) -> dict:
        """Return a dict representation of this chapter."""
        return {
            "url": self.url,
            "title": self.title,
            "chapter_no": self.chapter_no,
            "slug": self.slug,
            "original_html": self.original_html,
            "html": str(self.html) if self.html else None,
            "filters": self.filters,
            "pub_date": self.pub_date.strftime("%Y-%m-%d") if self.pub_date else None,
        }

    @classmethod
    def from_dict(self, data: dict) -> "Chapter":
        """Load a Chapter instance from a dict representation."""
        required_keys = {"url", "title", "chapter_no"}
        valid_keys = {"url", "title", "chapter_no", "slug", "html", "original_html", "pub_date", "filters"}
        actual_keys = set(data.keys())

        missing_required_keys = required_keys - actual_keys
        if missing_required_keys:
            raise ValueError(f"Missing required keys: {missing_required_keys}")

        invalid_keys = actual_keys - valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid keys: {invalid_keys}")

        return Chapter(
            url=data["url"],
            title=data["title"],
            chapter_no=data["chapter_no"],
            slug=data.get("slug"),
            filters=data.get("filters"),
            original_html=data.get("original_html"),
            html=data.get("html"),
            pub_date=datetime.datetime.strptime(data["pub_date"], "%Y-%m-%d").date() if data.get("pub_date") else None,
        )

    @property
    def html_tree(self) -> BeautifulSoup:
        """Return Chapter.html as BeautifulSoup."""
        assert self.html is not None
        return BeautifulSoup(self.html, "html.parser") if self.html else None

    def generate_html(self) -> Tag | None:
        """
        Generate an HTML tree from original_html and apply the defined filters to it.

        Returns either None (of there is no original_html value) or a Tag
        instance. This allows futher processing to be done externally if
        desired.
        """
        if self.original_html is None:
            return None
        content = BeautifulSoup(self.original_html, "html.parser")
        filters = self.filters if self.filters is not None else html.DEFAULT_FILTERS
        html.run_filters(content, filters)
        return content

    def populate_html(self, callback: Callable[["Chapter", Tag], None] | None = None) -> None:
        """
        Populate the Chapter.html field.

        Create the content for Chapter.html by calling Chapter.generate_html to
        create an HTML tree (with the filters defined in Chapter.filters run on
        it). A callback (that takes the chapter and the html tree) can also be
        provided to additional processing.

        Currently, this will be used to extract titles that are duplicated at
        the top of the content and set them to Chapter.title for some scrapers.
        (Some sites have more accurate / clean titles in the chapter page
        content than in the heading at the top of the page.)

        :param callback: A callback function that takes the Chapter instance and
            the Tag instance as input allowing for external processing to happen.
        """
        content = self.generate_html()
        if content is not None:
            if callback:
                callback(self, content)
            self.html = str(content)

    @property
    def chapter_id(self):
        """Return the chapter URL as the chapter ID."""
        return self.url

    @staticmethod
    def clean_title(title: str) -> str:
        """Cleanup a Chapter title to normalize it a bit, detect common typos, etc."""
        title = title.strip()

        # Change "100 The Black Dragon" => "Chapter 100 The Black Dragon"
        if re.match(r"\d+", title):
            title = f"Chapter {title}"

        # Change "Chapter 100 - The Black Dragon" => "Chapter 100: The Black Dragon"
        # Change "Chapter 100. The Black Dragon" => "Chapter 100: The Black Dragon"
        # Change "Side Story 100 - The Black Dragon" => "Side Story 100: The Black Dragon"
        title = re.sub(
            r"(Chapter\s*\d+(?:\.\d+)?|(?:Chapter\s*)?Side\s*Story\s*\d+(?:\.\d+)?)( - |\. )", r"\1: ", title
        )

        # Deal with "Chapter Ch 102"
        title = re.sub(r"(Chapter)\s*Ch\s*(\d+(?:\.\d+)?)", "\1 \2", title, re.IGNORECASE)

        # Deal with "Chapter 100The Black Dragon" => "Chapter 100: The Black Dragon"
        # TODO replace a-zA-Z with unicode character class using \p{L} (requires separate regex library)
        title = re.sub(r"(Chapter \d+(?:\.\d+)?)([a-zA-Z]{3,})", r"\1: \2", title, re.IGNORECASE)

        # Deal with "Side Story 100The Black Dragon" => "Side Story 100: The Black Dragon"
        # TODO replace a-zA-Z with unicode character class using \p{L} (requires separate regex library)
        title = re.sub(r"((?:Chapter )?Side Story \d+(?:\.\d+)?)([a-zA-Z]{3,})", r"\1: \2", title, re.IGNORECASE)

        # Change "Chapter 100 The Black Dragon" => "Chapter 100: The Black Dragon"
        title = re.sub(
            r"^(Chapter |(?:Chapter )?Side Story )?(\d+(?:\.\d+)?) ([“”\w])", r"\1\2: \3", title, re.IGNORECASE
        )

        # Fix "Chapter 761: - No Openings" => "Chapter 761: No Openings"
        title = title.replace(": - ", ": ")

        # Fix titles like "Chapter 761: Chapter 761", but make it open enough
        # that _anything_ repeated with just ": " separating will get caught, so
        # "Side Story 1: Side Story 1" would also be caught.
        title = re.sub(r"^([^:]+): \1$", r"\1", title, re.IGNORECASE)

        # Change "Chapter 100: 100 The Black Dragon" => "Chapter 100: The Black Dragon"
        # -- it's possible for false matches here, but I'm deeming the likelihood low since
        #    it would have to be an exact match for the chapter number. E.g.:
        #       "Chapter 99: 99 Bottles of Beer on the Wall" =>
        #       "Chapter 99: Bottle of Beer on the Wall"
        title = re.sub(r"Chapter (\d+): \1 *", r"Chapter \1: ", title, re.IGNORECASE)

        return title

    @staticmethod
    def is_title_ish(text: str) -> re.Match:
        """Check if a line of text matches something that looks like a title."""
        return (
            # Matches:
            #   100. The Black Dragon
            #   100 - The Black Dragon
            #   100: The Black Dragon
            #   Chapter 100 : The Black Dragon
            #   Chapter 100.1: The Black Dragon
            re.match(r"(?:Chapter\s*)?(\d+(?:\.\d+)?)(?:\s*[-:.])? \w+.*", text, re.IGNORECASE)
            or
            # Matches:
            #   Chapter 100
            #   Chapter 100.1
            #   Chapter 100.
            #   Chapter 100:
            #   Chapter 100 -
            re.match(r"Chapter\s* \d+(?:\.\d+)?(?:\s*[-:.])", text, re.IGNORECASE)
        )

    @staticmethod
    def extract_chapter_no(title: str) -> str:
        """Extract a chapter number from the chapter title."""
        match = re.match(
            r"^\s*(?:Chapter|Chapter\s*Side\*Story|Side\s*Story|Bonus\s*Side\s*Story)\s*(\d+(?:\.\d+)?)([.: ]|$)",
            title,
            re.IGNORECASE,
        )
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
    site_id: str | None = None
    title: str | None = None
    status: NovelStatus | None = None
    summary: Union[str, Tag] | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    author: Person | None = None
    translator: Person | None = None
    chapters: list[Chapter] | None = None
    cover_image: Image | None = None
    extra_css: str | None = None
    extras: dict | None = None
    published_on: datetime.date | None = None
    last_updated_on: datetime.date | None = None
