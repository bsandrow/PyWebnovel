"""Translatin Otaku scrapers."""

import datetime
import logging
import re

from bs4 import BeautifulSoup, Tag

from webnovel.data import Chapter, NovelStatus
from webnovel.html import remove_element
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector, WpMangaNovelInfoMixin

SITE_NAME = "TranslatinOtaku"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


def is_empty_paragraph(tag: Tag) -> bool:
    """Test if the tag is a <p> and has no content."""
    return tag.name == "p" and tag.text.strip() == ""


class ChapterScraper(ChapterScraperBase):
    """Scraper for TranslatinOtaku.net chapter content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"translatinotaku.net/novel/(?P<NovelID>[\w\d-]+)/(?P<ChapterID>[\w\d-]+)/"
    content_selector = Selector(".reading-content div.text-left")
    extra_css = """
    ul.wp-biographia-list {
        margin: 0 0 0 0;
    }
    ul.wp-biographia-list-icon li {
        margin: 0 5px 0 0;
    }
    ul.wp-biographia-list-text li, ul.wp-biographia-list-icon li {
        display: inline-block;
        list-style-type: none;
        background: none;
        padding: 0 0 5px;
    }
    .wp-biographia-item-icon {
        margin: 0 auto 20px;
        height: 32px !important;
        width: 32px !important;
        max-width: 100%;
    }
    """


class NovelScraper(WpMangaNovelInfoMixin):
    """Scraper for TranslatinOtaku.net."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"translatinotaku.net/novel/(?P<NovelID>[\w\d-]+)/"
    chapter_date_format = "%B %d, %Y"
    chapter_selector = ".wp-manga-chapter"
    extra_css = """
    ul.wp-biographia-list {
        margin: 0 0 0 0;
    }
    ul.wp-biographia-list-icon li {
        margin: 0 5px 0 0;
    }
    ul.wp-biographia-list-text li, ul.wp-biographia-list-icon li {
        display: inline-block;
        list-style-type: none;
        background: none;
        padding: 0 0 5px;
    }
    .wp-biographia-item-icon {
        margin: 0 auto 20px;
        height: 32px !important;
        width: 32px !important;
        max-width: 100%;
    }
    """

    def get_genres(self, page: BeautifulSoup) -> list[str]:
        """Extract genres listed for this novel."""
        return [genre.text for genre in page.select(".genres-content > a")]

    def get_novel_id(self, url: str) -> str:
        """Extract the novel's id from the url."""
        return match.group("NovelID") if (match := re.match(self.url_pattern, url)) else ""
