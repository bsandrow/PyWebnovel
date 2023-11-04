"""DaoTranslate scrapers."""

import logging
import re

from bs4 import BeautifulSoup, Tag

from webnovel.data import Chapter, NovelStatus, Person
from webnovel.html import remove_element
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector

from .divinedaolibrary import Volume

SITE_NAME = "DaoTranslate"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


def is_empty_paragraph(tag: Tag) -> bool:
    """Test if the tag is a <p> and has no content."""
    return tag.name == "p" and tag.text.strip() == ""


class ChapterScraper(ChapterScraperBase):
    """Scraper for DaoTranslate chapter content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"daotranslate.com/(?P<ChapterID>[\w\d-]+)/?"
    content_selector = Selector("div.epcontent")

    def post_process_content(self, chapter, content):
        """Post-Process Chapter Content."""
        for tag in content.select(".code-block"):
            remove_element(tag)


class NovelScraper(NovelScraperBase):
    """Scraper for DaoTranslate."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"daotranslate.com/series/(?P<NovelID>[\w\d-]+)/?"
    title_selector = Selector(".infox h1.entry-title")
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED}
    cover_image_url_selector = Selector(".thumbook img", attribute="src")
    extra_css = ""

    def get_genres(self, page: BeautifulSoup) -> list[str]:
        """Extract genres listed for this novel."""
        return [genre.text for genre in page.select(".genxed a")]

    def get_tags(self, page: BeautifulSoup) -> list[str]:
        """Extract tags from the novel page."""
        return [tag.text for tag in page.select(".bottom.tags a")]

    def get_summary(self, page: BeautifulSoup) -> str | Tag:
        """Extract the Novel's summary."""
        content = page.select_one(".summary__content")

        for tag in content.select(".lnbad-tag"):
            remove_element(tag)

        return content

    def get_author(self, page):
        """Extract the author from the page content."""
        author_content = page.select_one("div.spe").find("b", text=re.compile("Author"))
        author_names = author_content.parent.select("a")
        if len(author_names) == 2:
            return Person(name=f"{author_names[0].text.strip()} ({author_names[1].text.strip()})")
        else:
            return Person(name=author_names[0].text.strip())

    def get_status(self, page):
        """Extract the novel's status."""
        status_heading = page.select_one("div.spe").find("b", text=re.compile("Author"))
        if not status_heading:
            return NovelStatus.UNKNOWN
        status_text = status_heading.find_next_sibling()
        if not status_text:
            return NovelStatus.UNKNOWN
        return self.status_map.get(status_text.text.strip().lower(), NovelStatus.UNKNOWN)

    def get_novel_id(self, url: str) -> str:
        """Extract the novel's id from the url."""
        return match.group("NovelID") if (match := re.match(self.url_pattern, url)) else ""

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances."""
        chapter_list_els: list = page.select("div.eplisterfull > ul > li")
        return [
            Chapter(
                #
                # chapter_li.select_one(".epl-num")    => Ch. 333
                # chapter_li.select_one(".epl-title")  => Novel Title Chapter 333
                # chapter_li.select_one(".epl-date")   => August 11, 2023
                #
                url=(url := chapter_li.select_one("A").get("href")),
                title=Chapter.clean_title(self._text(chapter_li.select_one(".epl-title"))),
                chapter_no=idx,
                pub_date=self._date(self._text(chapter_li.select_one(".epl-date"))),
                slug=ChapterScraper.get_chapter_slug(url),
            )
            for idx, chapter_li in enumerate(reversed(chapter_list_els))
        ]
