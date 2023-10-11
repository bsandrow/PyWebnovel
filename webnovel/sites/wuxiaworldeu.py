"""WuxiaWorld.eu scrapers and utilities."""

import json
import logging
import re

from bs4 import BeautifulSoup

from webnovel.data import Chapter, NovelStatus, Person
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector

SITE_NAME = "WuxiaWorld.eu"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class WuxiaWorldEuChapterScraper(ChapterScraperBase):
    """Scraper for WuxiaWorld.eu chapter content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"wuxiaworld.eu/chapter/(?P<ChapterId>[\w\d-]+)"

    @staticmethod
    def get_json_data(page: BeautifulSoup) -> dict | None:
        """Extract that chapter json data from the page."""
        json_element = page.select_one("#__NEXT_DATA__")
        return json.loads(json_element.text.strip())

    def get_content(self, page):
        """Extract chapter content from page."""
        json_data = self.get_json_data(page)
        queries = json_data["props"]["pageProps"]["dehydratedState"]["queries"]
        if len(queries) < 1:
            raise ValueError("No data for chapter.")
        chapter_text = queries[0]["state"]["data"]["text"]
        paragraphs = chapter_text.split("\n")
        return BeautifulSoup("<div>" + "".join(f"<p>{para}</p>" for para in paragraphs) + "</div>", "html.parser")


class WuxiaWorldEuNovelScraper(NovelScraperBase):
    """Scraper for WuxiaWorld.eu."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"wuxiaworld.eu/novel/(?P<NovelID>[\w\d-]+)"
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED}
    summary_selector = Selector("div.tab-content div.desc-text")
    # cover_image_url_selector = Selector("#novel div.book > img", attribute="src")

    def get_title(self, page):
        """Extract the title."""
        title_element = page.select("H5")[0]
        return title_element.text

    def get_status(self, page):
        """Extract novel status from page."""
        title_element = page.select("H5")[0]
        block = title_element.parent.parent.select_one(".mantine-Group-root")
        block_children = list(block.children)
        status_text = block_children[0].text.lower().strip()
        return self.status_map.get(status_text, NovelStatus.UNKNOWN)

    def get_author(self, page):
        """Extract the author."""
        title_element = page.select("H5")[0]
        author_element = title_element.parent.find("div")
        author_name = author_element.text.strip()
        author_name = re.sub(r"^By\s+", "", author_name, re.IGNORECASE)
        return Person(name=author_name)

    def get_genres(self, page):
        """Extract genres from page."""
        return [a.text.strip() for a in page.select("h5")[2].parent.select(".mantine-Badge-root")]

    def get_tags(self, page):
        """Extract tags from page."""
        return [a.text.strip() for a in page.select("h5")[1].parent.select(".mantine-Badge-root")]

    def get_summary(self, page):
        """Extract the summary from the page."""
        return page.select_one(".mantine-Spoiler-content").text.strip()

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Extract chapter list from page."""
        novel_id = self.get_novel_id(url)
        response = self.http_client.get(
            f"https://wuxiaworld.eu/api/chapters/{novel_id}/", headers={"Accept": "application/json, text/plain, */*"}
        )
        json_data = json.loads(response.text)
        assert isinstance(json_data, list)
        return [
            Chapter(
                url="https://www.wuxiaworld.eu/chapter/" + chapter["novSlugChapSlug"],
                title=chapter["title"],
                chapter_no=chapter["index"],
                slug=chapter["novSlugChapSlug"],
            )
            for chapter in json_data
        ]
