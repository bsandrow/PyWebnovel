"""PyWebnovel Error Classes."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from webnovel.data import Chapter


class PyWebnovelError(Exception):
    """A Dummy "root" Exception for all PyWebnovel-specific errors to inherit from."""


class ParseError(ValueError, PyWebnovelError):
    """An error caused due to a failure during parsing."""


class NoMatchingNovelScraper(ValueError, PyWebnovelError):
    """An error caused when a scraper is needed, but no scraper matches the URL provided."""

    def __init__(self, url):
        self.url = url

    def __str__(self):
        return f"Unable to find a novel scraper that supports url: {self.url}"


class OrphanedUrlsError(ValueError, PyWebnovelError):
    """An error caused by chapter urls existing in an ebook that do _not_ exist in a freshly fetch chapter list for that novel."""

    def __init__(self, urls: list[str]):
        self.urls = urls

    def __str__(self):
        urls = "\n\t\t".join(self.urls)
        return f"Encountered the following orphaned URLs:\n{urls}"


class NonsequentialChaptersError(ValueError, PyWebnovelError):
    """An error caused by chapter order being mismatched between an existing ebook and the newly fetched chapter list."""

    def __init__(self, urls: list[str]):
        self.urls = urls

    def __str__(self):
        return (
            f"Found missing chapters that don't come after the most "
            f"recent chapters in the ebook. PyWebnovel currently does not support filling in gaps "
            f"between chapters or handling the author going back to add a chapter in "
            f"the middle of previous chapters. (Note: this may change in the future though).\n\n"
        ) + "\n\t\t".join(self.urls)


class ChapterContentNotFound(ParseError):
    """An error caused by ChapterScraper being unable to find chapter content within the chapter HTML page."""

    message: str

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self):
        return f"Unable to extract chapter content: {self.message}"


class DirectoryDoesNotExistError(OSError, PyWebnovelError):
    """Cannot create a WebNovelDirectory from a non-existant directory."""
