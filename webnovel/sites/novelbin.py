"""NovelBin scrapers and utilities."""

import logging
import re

from webnovel.data import Chapter, NovelStatus
from webnovel.html import DEFAULT_FILTERS, HtmlFilter, remove_element
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, NovelScraper, Selector

NOVEL_URL_PATTERN = HTTPS_PREFIX + r"novelbin\.net/n/([\w-]+)"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class RemoveStayTunedMessage(HtmlFilter):
    """
    Remove the 'Check back soon for more chapters' message.

    When you reach the most recent chapter, NovelBin adds a message:

        The Novel will be updated first on this website. Come back and continue
        reading tomorrow, everyone!

    Remove this, as it's not part of the chapter's content.
    """

    def filter(self, html_tree):
        """Filter out block containing the message."""
        for element in html_tree.select(".scehdule-text"):
            remove_element(element)


class NovelBinScraper(NovelScraper):
    """Scraper for NovelBin.net."""

    site_name = "NovelBin.com"

    title_selector = Selector(".col-novel-main > .col-info-desc > .desc > .title")
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED}
    genre_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(3) > a")
    author_name_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(2) > a")
    author_url_selector = Selector(
        ".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(2) > a", attribute="href"
    )
    summary_selector = Selector("div.tab-content div.desc-text")
    cover_image_url_selector = Selector("#novel div.book > img", attribute="src")

    chapter_content_selector = Selector("#chr-content")
    chapter_content_filters = DEFAULT_FILTERS + [RemoveStayTunedMessage()]

    @staticmethod
    def get_novel_id(url: str) -> str:
        """Return the novel id from the URL."""
        match = re.match(NOVEL_URL_PATTERN, url)
        if match is None:
            return None
        novel_id, _, _ = match.group(1).rpartition("-")
        return novel_id

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate that a URL matches something that works for NovelBin.net and the scraper should support."""
        return re.match(NOVEL_URL_PATTERN, url) is not None

    def chapter_extra_processing(self, chapter: Chapter) -> None:
        """Do extra chapter title processing."""
        target_html = chapter.html_content
        direct_descendants = target_html.find_all(recursive=False)

        while len(direct_descendants) == 1:
            target_html = direct_descendants[0]
            direct_descendants = target_html.find_all(recursive=False)

        title_header = target_html.find(["h4", "h3", "p"])
        if title_header and (
            match := re.match(r"(?:Chapter\s*)?(\d+(?:\.\d+)?)(?:\s*[-:.])? \w+.*", title_header.text, re.IGNORECASE)
        ):
            chapter.title = Chapter.clean_title(match.group(0))
            remove_element(title_header)

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

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances for NovelBin.net."""
        novel_id = self.get_novel_id(url)
        chapters = []

        # This ajax requests also returns the list, but as a <select> with
        # <option>s so parsing will be different.
        # page = self.get_page(f"https://novelbin.net/ajax/chapter-option?novelId={novel_id}")

        page = self.get_page(f"https://novelbin.net/ajax/chapter-archive?novelId={novel_id}")

        return [
            Chapter(
                url=chapter_li.select_one("A").get("href"),
                title=(title := Chapter.clean_title(chapter_li.select_one("A").get("title"))),
                chapter_no=Chapter.extract_chapter_no(title),
            )
            for chapter_li in page.select("UL.list-chapter > LI")
        ]
