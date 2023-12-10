"""PandaTL scrapers and utilities."""

import logging
import re

from bs4 import Tag

from webnovel import data
from webnovel.data import Chapter, NovelStatus
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector, WpMangaNovelInfoMixin

SITE_NAME = "PandaTL"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


def is_empty_paragraph(tag: Tag) -> bool:
    """Test if the tag is a <p> and has no content."""
    return tag.name == "p" and tag.text.strip() == ""


class ChapterScraper(ChapterScraperBase):
    """Scraper for PandaTL chapter content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"pandatl.com/novel/(?P<NovelID>[\w\d-]+)/(?P<ChapterID>[\w\d-]+)/?"
    content_selector = Selector(".reading-content div.text-left")


class NovelScraper(WpMangaNovelInfoMixin, NovelScraperBase):
    """Scraper for PandaTL."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"pandatl.com/novel/(?P<NovelID>[\w\d-]+)/?"
    status_section_name = "Novel"
    chapter_date_format = "%B %d, %Y"
    get_chapter_slug = ChapterScraper.get_chapter_slug

    def get_novel_id(self, url: str) -> str:
        """Extract the novel's id from the url."""
        return match.group("NovelID") if (match := re.match(self.url_pattern, url)) else ""
