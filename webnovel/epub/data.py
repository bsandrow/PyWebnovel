"""Representations of scraper data to be stored within the EPUB file."""

from dataclasses import dataclass
import urllib.parse

from webnovel.data import Chapter, Image, Novel


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


class EpubNovel(Novel):
    @property
    def novel_id(self):
        result = urllib.parse.urlparse(self.url)
        return ":".join(result.path)

    @property
    def site_id(self):
        result = urllib.parse.urlparse(self.url)
        return result.hostname
