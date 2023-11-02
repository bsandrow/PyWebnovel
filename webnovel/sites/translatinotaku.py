"""Translatin Otaku scrapers."""

import datetime
import itertools
import logging
import re
from typing import Union

from bs4 import BeautifulSoup, Tag

from webnovel import data, errors
from webnovel.data import Chapter, NovelStatus
from webnovel.html import DEFAULT_FILTERS, remove_element
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector

SITE_NAME = "Infamous-Scans.com"
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


class NovelScraper(NovelScraperBase):
    """Scraper for TranslatinOtaku.net."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"translatinotaku.net/novel/(?P<NovelID>[\w\d-]+)/"
    title_selector = Selector(".post-title h1")
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED}
    cover_image_url_selector = Selector(".summary_image img", attribute="src")

    def get_genres(self, page: BeautifulSoup) -> list[str]:
        """Extract genres listed for this novel."""
        return [genre.text for genre in page.select(".genres-content > a")]

    def get_summary(self, page: BeautifulSoup) -> str | Tag:
        """Extract the Novel's summary."""
        content = page.select_one(".summary__content")

        code = content.select_one(".code-block")
        if code:
            remove_element(code)

        return content

    def get_author(self, page):
        """Extract the author from the page content."""
        return None

    def get_status(self, page):
        """Extract the novel's status."""
        status_heading = page.find("h5", text=re.compile("Status"))
        if not status_heading:
            return NovelStatus.UNKNOWN
        status_text = status_heading.parent.find_next_sibling("div")
        if not status_text:
            return NovelStatus.UNKNOWN
        return self.status_map.get(status_text.text.strip().lower(), NovelStatus.UNKNOWN)

    def get_novel_id(self, url: str) -> str:
        """Extract the novel's id from the url."""
        return match.group("NovelID") if (match := re.match(self.url_pattern, url)) else ""

    @staticmethod
    def _date(release_date_el: Tag) -> datetime.datetime | None:
        """Extract a datetime from the release date element."""
        if not release_date_el or not (date_string := release_date_el.text.strip()):
            return None

        if match := re.search(r"(\d+) hours? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(hours=int(match.group(1)))

        if match := re.search(r"(\d+) minutes? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(minutes=int(match.group(1)))

        if match := re.search(r"(\d+) seconds? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(seconds=int(match.group(1)))

        if match := re.search(r"(\d+) days? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(days=int(match.group(1)))

        return datetime.datetime.strptime(date_string, "%B %d, %Y")

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances."""
        novel_id = self.get_novel_id(url)
        ajax_url = f"https://translatinotaku.net/novel/{novel_id}/ajax/chapters/"
        page = self.get_page(ajax_url, method="post")
        return [
            Chapter(
                url=(url := chapter_li.select_one("A").get("href")),
                title=Chapter.clean_title(chapter_li.select_one("A").text.strip()),
                chapter_no=idx,
                pub_date=self._date(release_date_el=chapter_li.select_one(".chapter-release-date")),
                slug=ChapterScraper.get_chapter_slug(url),
            )
            for idx, chapter_li in enumerate(reversed(page.select(".wp-manga-chapter")))
        ]
