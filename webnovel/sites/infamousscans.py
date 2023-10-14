"""InfamousScans scrapers and utilities."""

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
    """Scraper for Infamous-Scans.com chapter content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"infamous-scans\.com/manga/(?P<NovelID>[\w\d-]+)/(?P<ChapterID>[\w\d-]+)/"
    content_selector = Selector(".reading-content div.text-left")

    def post_process_content(self, chapter, content) -> None:
        """Do extra chapter title processing."""
        remove_queue = []
        # expected_elements = ["p", "center", "p", "hr", "p", "center"]
        elements = list(itertools.islice(content.children, 6))

        #
        # Remove the cover image at the top of each chapter
        #
        if is_empty_paragraph(elements[0]) and elements[1].name == "center" and elements[1].find("img"):
            remove_queue.append(elements[0])
            remove_queue.append(elements[1])

        #
        # Remove the horizontal rule between the title and the cover image
        #
        if (
            len(remove_queue)
            and is_empty_paragraph(elements[2])
            and elements[3].name == "hr"
            and is_empty_paragraph(elements[4])
        ):
            remove_queue += elements[2:5]

        #
        # Remove and process the title at the top of the chapter
        #
        if (
            len(remove_queue)
            and elements[5].name == "center"
            and (match := re.match(r"\s*»»————-\s*(?P<ChapterTitle>.+)\s*————-««\s*", elements[5].text))
        ):
            chapter.title = Chapter.clean_title(match.group("ChapterTitle"))
            remove_queue.append(elements[5])

        for element in remove_queue:
            remove_element(element)


class NovelScraper(NovelScraperBase):
    """Scraper for Infamous-Scans.com."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"infamous-scans\.com/manga/(?P<NovelID>[\w\d-]+)/"
    title_selector = Selector("#manga-title")
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED}
    cover_image_url_selector = Selector(".summary_image img", attribute="src")

    def get_summary(self, page: BeautifulSoup) -> str | Tag:
        """Extract the Novel's summary."""
        h5 = page.find("h5", text=re.compile("Summary"))
        return h5.find_next_sibling("div") if h5 else ""

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

    def get_status(self, page):
        """
        Get novel status.

        Can't get status with selectors alone, so need to override.
        """
        items = page.select(".col-novel-main > .col-info-desc > .desc > .info-meta > li")
        for item in items:
            section = item.find("h3").text.strip()
            if section.lower() in ("status", "status:"):
                return self.status_map.get(item.find("a").text.strip().lower(), NovelStatus.UNKNOWN)
        return NovelStatus.UNKNOWN

    def get_novel_id(self, url: str) -> str:
        """Extract the novel's id from the url."""
        return match.group("NovelID") if (match := re.match(self.url_pattern, url)) else ""

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances."""
        novel_id = self.get_novel_id(url)
        ajax_url = f"https://infamous-scans.com/manga/{novel_id}/ajax/chapters/"
        page = self.get_page(ajax_url, method="post")
        return [
            Chapter(
                url=(url := chapter_li.select_one("A").get("href")),
                title=Chapter.clean_title(chapter_li.select_one("A").text.strip()),
                chapter_no=idx,
                pub_date=(
                    datetime.datetime.strptime(date_string, "%B %d, %Y")
                    if (
                        (release_el := chapter_li.select_one(".chapter-release-date"))
                        and (date_string := release_el.text.strip())
                    )
                    else None
                ),
                slug=ChapterScraper.get_chapter_slug(url),
            )
            for idx, chapter_li in enumerate(reversed(page.select(".wp-manga-chapter.free-chap")))
        ]
