"""Scrapers for specific sites."""

import inspect

from apptk.importing import iter_submodules

from webnovel.scraping import ChapterScraperBase, NovelScraperBase

NOVEL_SCRAPERS: list[type[NovelScraperBase]] = [
    item
    for submodule in iter_submodules(__name__)
    for _, item in submodule.__dict__.items()
    if inspect.isclass(item) and issubclass(item, NovelScraperBase) and item != NovelScraperBase
]

CHAPTER_SCRAPERS: list[type[ChapterScraperBase]] = [
    item
    for submodule in iter_submodules(__name__)
    for _, item in submodule.__dict__.items()
    if inspect.isclass(item) and issubclass(item, ChapterScraperBase) and item != ChapterScraperBase
]


def find_scraper(url: str) -> type[NovelScraperBase]:
    """Find a scraper class that matches the provided url."""
    for scraper in NOVEL_SCRAPERS:
        if scraper.supports_url(url):
            return scraper


def find_chapter_scraper(url: str) -> type[ChapterScraperBase]:
    """Find a ChapterScraper class that matches the provided url."""
    for scraper in CHAPTER_SCRAPERS:
        if scraper.supports_url(url):
            return scraper
