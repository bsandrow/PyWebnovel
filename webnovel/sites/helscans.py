"""HelScans scrapers."""

import logging
import re

from bs4 import BeautifulSoup, Tag

from webnovel.data import Chapter, NovelStatus, Person
from webnovel.html import remove_element
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector

from .divinedaolibrary import Volume

SITE_NAME = "HelScans"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class ChapterScraper(ChapterScraperBase):
    """Scraper for HelScans chapter content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"helscans.com/(?P<ChapterID>[\w\d-]+)/?"
    content_selector = Selector("#readerarea")

    def post_process_content(self, chapter, content):
        """Post-Process Chapter Content."""
        for tag in content.select("script"):
            remove_element(tag)

        for tag in content.select("[id]"):
            id_value = tag.get("id")
            if id_value.lower().startswith("ezoic-pub-ad-"):
                remove_element(tag)


class NovelScraper(NovelScraperBase):
    """Scraper for HelScans."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"helscans.com/manga/(?P<NovelID>[\w\d-]+)/?"
    title_selector = Selector(".infox h1.entry-title")
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED}
    cover_image_url_selector = Selector(".thumbook img", attribute="src")
    extra_css = ""

    def get_genres(self, page: BeautifulSoup) -> list[str]:
        """Extract genres listed for this novel."""
        return [genre.text for genre in page.select(".mgen a")]

    def get_summary(self, page: BeautifulSoup) -> str | Tag:
        """Extract the Novel's summary."""
        element = page.select_one("#synopsis")
        element["style"] = "white-space: pre-line; width: 100%;"
        return element

    def get_author(self, page):
        """Extract the author from the page content."""
        author_content = None
        for fmed_element in page.select(".fmed"):
            author_content = fmed_element.find("h2", text=re.compile("Author"))
            if author_content:
                break
        if not author_content:
            return None
        author_name = author_content.find_next_sibling("span")
        if not author_name:
            return None
        return Person(name=author_name.text.strip())

    def get_status(self, page):
        """Extract the novel's status."""
        status_candidates = page.select(".imptdt")
        status_raw = ""
        for candidate in status_candidates:
            if candidate.text.strip().startswith("Status"):
                status_raw = candidate.find("i").text

        if not status_raw:
            return NovelStatus.UNKNOWN

        return self.status_map.get(status_raw.strip().lower(), NovelStatus.UNKNOWN)

    def get_novel_id(self, url: str) -> str:
        """Extract the novel's id from the url."""
        return match.group("NovelID") if (match := re.match(self.url_pattern, url)) else ""

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances."""
        chapter_list_els: list = page.select("#chapterlist > ul > li")
        return [
            Chapter(
                #
                # chapter_li.select_one(".epl-num")    => Ch. 333
                # chapter_li.select_one(".epl-title")  => Novel Title Chapter 333
                # chapter_li.select_one(".epl-date")   => August 11, 2023
                #
                url=(url := chapter_li.select_one("A").get("href")),
                title=Chapter.clean_title(self._text(chapter_li.select_one(".chapternum"))),
                chapter_no=idx,
                pub_date=self._date(self._text(chapter_li.select_one(".chapterdate"))),
                slug=ChapterScraper.get_chapter_slug(url),
            )
            for idx, chapter_li in enumerate(reversed(chapter_list_els))
        ]
