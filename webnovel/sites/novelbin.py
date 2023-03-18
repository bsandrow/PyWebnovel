"""NovelBin scrapers and utilities."""

import json
import re

from webnovel.data import Chapter, NovelStatus
from webnovel.html import DEFAULT_FILTERS
from webnovel.scraping import HTTPS_PREFIX, NovelScraper, Selector

NOVEL_URL_PATTERN = HTTPS_PREFIX + r"novelbin\.net/n/([\w-]+)"


class NovelBinScraper(NovelScraper):
    """Scraper for NovelBin.net."""

    site_name = "NovelBin.com"

    title_selector = Selector(".col-novel-main > .col-info-desc > .desc > .title")
    status_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(5) > a")
    status_map = {"Ongoing": NovelStatus.ONGOING, "Completed": NovelStatus.COMPLETED}
    genre_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(3) > a")
    author_name_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(2) > a")
    author_url_selector = Selector(
        ".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(2) > a", attribute="href"
    )
    summary_selector = Selector("div.tab-content div.desc-text")

    chapter_content_selector = Selector("#chr-content")
    chapter_content_filters = DEFAULT_FILTERS

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

    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances for NovelBin.net."""
        novel_id = self.get_novel_id(url)

        # This ajax requests also returns the list, but as a <select> with
        # <option>s so parsing will be different.
        # page = self.get_page(f"https://novelbin.net/ajax/chapter-option?novelId={novel_id}")

        page = self.get_page(f"https://novelbin.net/ajax/chapter-archive?novelId={novel_id}")

        def get_chapter_no(title: str):
            match = re.match(r"^\s*Chapter\s*(\d+)[.: ]", title, re.IGNORECASE)
            chapter_no = match.group(1) if match is not None else None
            try:
                return int(chapter_no)
            except (ValueError, TypeError):
                print(f"Warning: Got bad chapter_no for title: {title}")
                return 0

        return [
            Chapter(
                url=chapter_li.select_one("A").get("href"),
                title=chapter_li.select_one("A").get("title"),
                chapter_no=get_chapter_no(chapter_li.select_one("A").get("title")),
            )
            for chapter_li in page.select("UL.list-chapter > LI")
        ]
