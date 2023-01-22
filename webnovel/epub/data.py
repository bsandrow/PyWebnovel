"""Representations of scraper data to be stored within the EPUB file."""

from dataclasses import dataclass

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
    pass
