"""Support for scraping ReadHive.org."""

"https://readhive.org/series/43151/153/"

import datetime
import json
import logging
import re

from bs4 import BeautifulSoup, NavigableString, Tag

from webnovel import html
from webnovel.data import Chapter, NovelStatus
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector

SITE_NAME = "ReadHive.org"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class NovelScraper(NovelScraperBase):
    """Scraper for ReadHive.org."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"readhive.org/series/(?P<NovelID>\d+)/"

    # <main>
    #   <section>
    #       <div></div>
    #       <div>
    #           <div>
    #               <div>
    #                   <img src=""/>   <-- Cover Image
    #                   <div></div>
    #               </div>
    #           </div>
    #           <div>
    #               <h1></h1>           <-- Title
    #           </div>
    #       </div>
    #   </section>
    #   <section>
    #       <div>
    #           <div>
    #               <a>Genre 1</a>      <-- Genre
    #               <a>Genre 2</a>      <-- Genre
    #           </div>
    #       </div>
    #       <div>
    #           <div>
    #               <div x-show="tab === 'about'">
    #                 <h2></h2>
    #                 <div></div>       <-- Summary
    #                 <h3></h3>
    #                 <div></div>
    #               </div>
    #               <div x-show="tab === 'releases'">
    #                   <h3></h3>
    #                   <div>
    #                       <div>
    #                           <a>                             <-- Paywalled Chapter
    #                               <span><svg></svg></span>    <-- Chapter Cost
    #                               <div>
    #                                   <div></div>             <-- Chapter Title
    #                                   <span></span>           <-- Chapter Posted At
    #                               </div>
    #                           </a>
    #                           <a>                             <-- Free Chapter
    #                               <div>
    #                                   <div></div>             <-- Chapter Title
    #                                   <span></span>           <-- Chapter Posted At
    #                               </div>
    #                           </a>
    #                       </div>
    #                   </div>
    #               </div>
    #           </div>
    #       </div>
    #   </section>
    # </main>
    title_selector = Selector("main > section:first-child > div:nth-child(2) > div:nth-child(2) h1 ")
    genre_selector = Selector("main > section:nth-child(2) > div:first-child > div:first-child > a")
    summary_selector = Selector("div[x-show=\"tab === 'about'\"] > div:first-of-type")
    cover_image_url_selector = Selector(
        "main > section:first-child > div:nth-child(2) > div:first-child > div > img",
        attribute="src",
    )

    status_map = {}

    def get_author(self, page: BeautifulSoup) -> None:
        """No 'author' is listed."""
        return None

    def get_status(self, page):
        """Return "unknown" status as site doesn't have this info available."""
        return NovelStatus.UNKNOWN

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances for NovelBin.net."""
        chapters = []
        chapter_list_elements = page.select("div[x-show=\"tab === 'releases'\"] > div:first-of-type > div > a")

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


class ChapterScraper(ChapterScraperBase):
    """Scraper for ReadHive.org Chapters."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"readhive.org/series/(?P<NovelID>\d+)/(?P<ChapterID>\d+)/?"
    content_selector = Selector("main > div:nth-child(3) > div:first-child")

    @classmethod
    def get_chapter_slug(cls, url: str) -> str | None:
        """Generate a chapter slug from the ChapterID and NovelID."""
        if not cls.supports_url(url):
            raise ValueError(f"Not a valid chapter url for {cls.site_name}: {url}")
        if match := re.match(cls.url_pattern, url):
            return "-".join(
                [
                    "novel",
                    match.group("NovelID"),
                    "chapter",
                    match.group("ChapterID"),
                ]
            )
        return None
