"""DivineDaoLibrary.com scrapers."""

from dataclasses import dataclass
import logging

from bs4 import BeautifulSoup, Tag

from webnovel import logs, scraping
from webnovel.data import Chapter, NovelStatus, Person

SITE_NAME = "DivineDaoLibrary.com"
logger = logging.getLogger(__name__)
timer = logs.LogTimer(logger)


@dataclass
class Volume:
    """A volume."""

    name: str
    insert_before: int | None = None
    insert_after: int | None = None


class NovelScraper(scraping.NovelScraperBase):
    """Novel Scraper for DivineDaoLibrary.com."""

    site_name = SITE_NAME
    url_pattern = scraping.HTTPS_PREFIX + r"divinedaolibrary\.com/(?P<NovelID>[\w\d-]+)/"
    title_selector = scraping.Selector(".entry-header .entry-title")
    cover_image_url_selector = scraping.Selector(".entry-content p:first-child img", attribute="data-ezsrc")

    def get_status(self, page: BeautifulSoup) -> NovelStatus:
        """There is no status on the page, so we just always return UNKNOWN."""
        return NovelStatus.UNKNOWN

    def get_author(self, page: BeautifulSoup) -> Person | None:
        """
        Extract the author.

        The author is in a <h3> with "Author: " preceeding it, so we just need
        to find that heading tag, and pull the name out. There is not author
        link.
        """
        for h3 in page.select(".entry-content h3"):
            if h3.text.strip().lower() == "author":
                return Person(name=h3.text.strip()[7:].strip())

    def get_summary(self, page: BeautifulSoup) -> str | Tag:
        """
        Extract the summary.

        There's no single element that contains all of the summary and only the
        summary, so we need to find the "Description" header, and then pull out
        all of the following siblings to that element until we hit another
        heading (<h3>) or a divider (<hr>).
        """
        container = page.new_tag("div")
        for h3 in page.select(".entry-content h3"):
            if h3.text.strip().lower() == "description":
                ptr = h3
                while (ptr := ptr.next_sibling) and ptr.name.lower() not in ("hr", "h3"):
                    container.append(ptr)
        return container

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of chapters scraped from the chapter list."""
        chapters = []
        volumes = []

        for volume_element in page.select(".collapseomatic"):
            volume = Volume(name=volume_element.get("title").strip(), insert_before=len(chapters))
            volid = volume_element.get("id")

            logger.debug("Processing Chapters for Volume '%s'", volume.name)

            # Note, we extract <a> instead of <li> here since there are chapter
            # entries with no links. I'm guessing these are placeholders for
            # chapters that have raws, but no translation yet.
            volume_chapters = page.select(f"#target-{volid} > ul > li a")

            for idx, chapter_anchor in enumerate(volume_chapters, start=len(chapters)):
                chapter = Chapter(
                    url=(_url := chapter_anchor.get("href")),
                    title=Chapter.clean_title(chapter_anchor.text),
                    chapter_no=idx + 1,
                    slug=ChapterScraper.get_chapter_slug(_url),
                )
                chapters.append(chapter)

            if len(chapters) > volume.insert_before:
                volumes.append(volume)

        return chapters

    def post_processing(self, page, url, novel):
        """Scrape extra information from the novel page."""
        novel.extras = {}

        for h3 in page.select(".entry-content h3"):
            if h3.text.strip().lower().startswith("raws:"):
                novel.extras["raws_name"] = h3.text.strip()[5:].strip()
                novel.extras["raws_url"] = h3.select_one("a").get("href")

        return super().post_processing(page, url, novel)


class ChapterScraper(scraping.ChapterScraperBase):
    """Scraper for DivineDaoLibrary.com Chapters."""

    site_name = SITE_NAME
    url_pattern = scraping.HTTPS_PREFIX + r"divinedaolibrary\.com/(?P<ChapterID>[\w\d-]+)/"
    content_selector = scraping.Selector("article > .entry-content")
