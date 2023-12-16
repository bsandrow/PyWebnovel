"""
Support for scraping BWebNovel.Wordpress.com.

Note: This is a one-novel translation Wordpress site.
"""

import datetime
import json
import logging
import re
from typing import Union

from bs4 import BeautifulSoup, NavigableString, Tag

from webnovel import html
from webnovel.data import Chapter, NovelStatus
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector

SITE_NAME = "BIBELL"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class NovelScraper(NovelScraperBase):
    """Scraper for BIBELL."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"bwebnovel.wordpress.com/"
    status_map = {}

    def get_title(self, page: BeautifulSoup) -> str:
        """Return the Title."""
        return "ReLife Player"

    def get_summary(self, page: BeautifulSoup) -> str | Tag:
        """Return the Summary."""
        return ""

    def get_status(self, page):
        """Return the status."""
        # """This translator dropped the novel."""
        return NovelStatus.DROPPED

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances for NovelBin.net."""
        _page = self.get_page("https://bwebnovel.wordpress.com/category/relife-player-contents/")
        chapters = []

        while _page is not None:

            entries = _page.select(".wp-block-post-template .wp-block-post")
            next_page_link = _page.select_one("nav.wp-block-query-pagination > a")
            next_page_url = next_page_link.get("href") if next_page_link else None

            for entry in entries:
                title_element = entry.select_one(".block-post-title")
                post_date_element = entry.select_one(".wp-block-post-date > time")
                title_text = title_element.text.strip()
                chapter_url = title_element.get("href")
                post_date_raw = post_date_element.get("datetime")

            _page = self.get_page(next_page_url) if next_page_url else None

        for idx, chapter_list_element in enumerate(reversed(chapter_list_elements)):
            svg = chapter_list_element.select_one("span.bg-red > svg")
            is_paywalled = svg is not None
            if is_paywalled:
                continue

            title_element = chapter_list_element.select_one("div > div > span")
            title_text = title_element.text.strip()

            pub_date_element = chapter_list_element.select_one("div > span.text-xs")
            pub_date_text = pub_date_element.text.strip()

            chapter = Chapter(
                url=(url := chapter_list_element.get("href")),
                title=Chapter.clean_title(title_text),
                chapter_no=idx + 1,
                slug=ChapterScraper.get_chapter_slug(url),
                pub_date=self._date(pub_date_text),
            )

            chapters.append(chapter)

        return chapters


# class ChapterScraper(ChapterScraperBase):
#     """Scraper for ReadHive.org Chapters."""

#     site_name = SITE_NAME
#     url_pattern = HTTPS_PREFIX + r"readhive.org/series/(?P<NovelID>\d+)/(?P<ChapterID>\d+)/?"
#     content_selector = Selector("#chp_raw")

#     @classmethod
#     def get_chapter_slug(cls, url: str) -> str | None:
#         """Generate a chapter slug from the ChapterID and NovelID."""
#         if not cls.supports_url(url):
#             raise ValueError(f"Not a valid chapter url for {cls.site_name}: {url}")
#         if match := re.match(cls.url_pattern, url):
#             return "-".join([
#                 "novel",
#                 match.group("NovelID"),
#                 "chapter",
#                 match.group("ChapterID"),
#             ])
#         return None
