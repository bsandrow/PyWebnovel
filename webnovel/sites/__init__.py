"""Scrapers for specific sites."""

import inspect

from webnovel.scraping import ChapterScraper, NovelScraper
from webnovel.sites import novelbin, novelcool, reaperscans, scribblehub, wuxiaworld_site, wuxiaworldeu

__all__ = [
    "novelbin",
    "novelcool",
    "reaperscans",
    "scribblehub",
    "wuxiaworld_site",
    "find_scraper",
]

SITES = [
    novelbin,
    novelcool,
    reaperscans,
    scribblehub,
    wuxiaworld_site,
    wuxiaworldeu,
]

NOVEL_SCRAPERS: list[type[NovelScraper]] = [
    item
    for site in SITES
    for item in map(lambda x: getattr(site, x), dir(site))
    if inspect.isclass(item) and issubclass(item, NovelScraper) and item != NovelScraper
]

CHAPTER_SCRAPERS: list[type[ChapterScraper]] = [
    item
    for site in SITES
    for item in map(lambda x: getattr(site, x), dir(site))
    if inspect.isclass(item) and issubclass(item, ChapterScraper) and item != ChapterScraper
]


def find_scraper(url: str) -> type[NovelScraper]:
    """Find a scraper class that matches the provided url."""
    for scraper in NOVEL_SCRAPERS:
        if scraper.validate_url(url):
            return scraper


def find_chapter_scraper(url: str) -> type[ChapterScraper]:
    """Find a ChapterScraper class that matches the provided url."""
    for scraper in CHAPTER_SCRAPERS:
        if scraper.supports_url(url):
            return scraper
