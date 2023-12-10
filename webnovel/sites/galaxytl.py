"""Scrapers for GalaxyTL."""

import itertools
import logging
import re

from bs4 import BeautifulSoup, Tag

from webnovel import html, logs
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector, WpMangaNovelInfoMixin

SITE_NAME = "GalaxyTL"
logger = logging.getLogger(__name__)
timer = logs.LogTimer(logger)


class ChapterScraper(ChapterScraperBase):
    """Scraper for GalaxyTL chapter content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"galaxytranslations97.com/novel/(?P<NovelID>[\w\d-]+)/(?P<ChapterID>[\w\d-]+)/?"
    content_selector = Selector("div.reading-content")

    def post_process_content(self, chapter, content):
        """Post-Process Chapter Content."""
        for tag in itertools.chain(
            content.select("div.code-block"),
            content.select("#wp-manga-current-chap"),
            content.select("#text-chapter-toolbar"),
        ):
            html.remove_element(tag)


class NovelScraper(WpMangaNovelInfoMixin, NovelScraperBase):
    """Scraper for GalaxyTL novel content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"galaxytranslations97.com/novel/(?P<NovelID>[\w\d-]+)/?"
    chapter_date_format = "%d, %B %Y"
    extra_css = ""
    get_chapter_slug = ChapterScraper.get_chapter_slug

    def get_novel_id(self, url: str) -> str:
        """Extract the novel's id from the url."""
        return match.group("NovelID") if (match := re.match(self.url_pattern, url)) else ""

    def get_summary(self, page: BeautifulSoup) -> str | Tag:
        """Remove code blocks from summary content."""
        summary_html = super().get_summary(page)
        for item in summary_html.select("div.code-block"):
            html.remove_element(item)
        return summary_html
