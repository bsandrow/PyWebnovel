"""Scrapers for specific sites."""

import inspect

from webnovel.scraping import ChapterScraper, NovelScraperBase
from webnovel.sites import (
    novelbin,
    novelcool,
    novelnext,
    reaperscans,
    scribblehub,
    skydemonorder,
    wuxiarealm,
    wuxiaworld_site,
    wuxiaworldeu,
)

__all__ = [
    "novelbin",
    "novelcool",
    "novelnext",
    "reaperscans",
    "scribblehub",
    "skydemonorder",
    "wuxiarealm",
    "wuxiaworldeu",
    "wuxiaworld_site",
    "find_scraper",
]

SITES = [
    novelbin,
    novelcool,
    novelnext,
    reaperscans,
    scribblehub,
    skydemonorder,
    wuxiaworld_site,
    wuxiaworldeu,
    wuxiarealm,
]

NOVEL_SCRAPERS: list[type[NovelScraperBase]] = [
    item
    for site in SITES
    for item in map(lambda x: getattr(site, x), dir(site))
    if inspect.isclass(item) and issubclass(item, NovelScraperBase) and item != NovelScraperBase
]

CHAPTER_SCRAPERS: list[type[ChapterScraper]] = [
    item
    for site in SITES
    for item in map(lambda x: getattr(site, x), dir(site))
    if inspect.isclass(item) and issubclass(item, ChapterScraper) and item != ChapterScraper
]


def find_scraper(url: str) -> type[NovelScraperBase]:
    """Find a scraper class that matches the provided url."""
    for scraper in NOVEL_SCRAPERS:
        if scraper.supports_url(url):
            return scraper


def find_chapter_scraper(url: str) -> type[ChapterScraper]:
    """Find a ChapterScraper class that matches the provided url."""
    for scraper in CHAPTER_SCRAPERS:
        if scraper.supports_url(url):
            return scraper
