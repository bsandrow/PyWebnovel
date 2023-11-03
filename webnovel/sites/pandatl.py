"""PandaTL scrapers and utilities."""

import logging
import re

from bs4 import Tag

from webnovel import data
from webnovel.data import Chapter, NovelStatus
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector

SITE_NAME = "PandaTL"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


def is_empty_paragraph(tag: Tag) -> bool:
    """Test if the tag is a <p> and has no content."""
    return tag.name == "p" and tag.text.strip() == ""


class ChapterScraper(ChapterScraperBase):
    """Scraper for PandaTL chapter content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"https://pandatl.com/novel/(?P<NovelID>[\w\d-]+)/(?P<ChapterID>[\w\d-]+)/?"
    content_selector = Selector(".reading-content div.text-left")


class NovelScraper(NovelScraperBase):
    """Scraper for PandaTL."""

    site_name = SITE_NAME

    url_pattern = HTTPS_PREFIX + r"https://pandatl.com/novel/(?P<NovelID>[\w\d-]+)/?"
    title_selector = Selector(".post-title h1")
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED}
    cover_image_url_selector = Selector(".summary_image img", attribute="src")
    summary_selector = Selector(".summary__content")

    def get_author(self, page):
        """Extract the author from the page content."""
        author_heading = page.find("h5", text=re.compile("Author\(s\)"))
        if not author_heading:
            return None
        author_text = author_heading.parent.find_next_sibling("div")
        if not author_text:
            return None
        return data.Person(name=author_text.text.strip())

    def get_status(self, page):
        """Extract the novel's status."""
        status_heading = page.find("h5", text=re.compile("Novel"))
        if not status_heading:
            return NovelStatus.UNKNOWN
        status_text = status_heading.parent.find_next_sibling("div")
        if not status_text:
            return NovelStatus.UNKNOWN
        return self.status_map.get(status_text.text.strip().lower(), NovelStatus.UNKNOWN)

    def get_novel_id(self, url: str) -> str:
        """Extract the novel's id from the url."""
        return match.group("NovelID") if (match := re.match(self.url_pattern, url)) else ""

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances."""
        novel_id = self.get_novel_id(url)
        ajax_url = f"https://pandatl.com/novel/{novel_id}/ajax/chapters/"
        page = self.get_page(ajax_url, method="post")
        return [
            Chapter(
                url=(url := chapter_li.select_one("A").get("href")),
                title=Chapter.clean_title(chapter_li.select_one("A").text.strip()),
                chapter_no=idx,
                pub_date=self._date(self._text(chapter_li.select_one(".chapter-release-date"))),
                slug=ChapterScraper.get_chapter_slug(url),
            )
            for idx, chapter_li in enumerate(reversed(page.select(".wp-manga-chapter.free-chap")))
        ]
