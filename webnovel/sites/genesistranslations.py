"""Scrapers for Genesis Translations."""

import logging
import re

from webnovel import html, logs, scraping

SITE_NAME = "Genesis Translations"
logger = logging.getLogger(__name__)
timer = logs.LogTimer(logger)


class NovelScraper(scraping.NovelScraperBase):
    """Novel Scraper for Genesis Translations."""

    site_name = SITE_NAME
    url_pattern = scraping.HTTPS_PREFIX + r"genesistls.com/series/(?P<NovelID>[\w\d-]+)/?"
    extra_css = ""

    def get_novel_id(self, url: str) -> str:
        """Extract the novel's id from the url."""
        return match.group("NovelID") if (match := re.match(self.url_pattern, url)) else ""
