"""Scrapers for specific sites."""

from webnovel.scraping import NovelScraper
from webnovel.sites import novelbin, reaperscans, wuxiaworld_site

__all__ = [
    "novelbin",
    "reaperscans",
    "wuxiaworld_site",
    "find_scraper",
]

SITES = [
    novelbin,
    reaperscans,
    wuxiaworld_site,
]

SCRAPERS = [item for site in SITES for item in dir(site) if issubclass(item, NovelScraper)]


def find_scraper(url: str) -> type[NovelScraper]:
    """Find a scraper class that matches the provided url."""
    for scraper in SCRAPERS:
        if scraper.validate_url(url):
            return scraper
