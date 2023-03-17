"""Representations of scraper data to be stored within the EPUB file."""

from dataclasses import dataclass
from typing import TYPE_CHECKING
import urllib.parse

from webnovel.data import Chapter, Image, Novel

if TYPE_CHECKING:
    from webnovel.epub.pkg import NovelInfo


class EpubChapter(Chapter):
    """An extension of Chapter class to add epub-specific fields."""

    # Path to the HTML file (within the EPUB package) for this chapter.
    html_file: str = None

    # Path to the Markdown file (within the EPUB package) for this chapter.
    markdown_file: str = None


@dataclass
class EpubMetadata:
    """Representation of the scraper.json file stored in .epub file."""

    # The list of chapters within this EPUB package.
    chapters: list[EpubChapter] = None


@dataclass
class NovelData:
    """Novel Data stored in ebook."""

    epub_uid: str
    novel_info: "NovelInfo"
    epub_version: str
    pkg_opf_path: str
    include_images: bool
    default_language_code: str = "en"

    # The version of NovelData used. Probably won't be needed, but if there
    # needs to be upgrades between changes to old version this will help to keep
    # track.
    version: str = "1.0"
