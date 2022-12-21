from typing import Optional

from apptk.html import Selector
from apptk.http import HttpClient
from bs4 import BeautifulSoup

from webnovel.data import Novel, NovelStatus, Person


http_client = HttpClient()


class NovelScraper:
    http_client: HttpClient
    parser: str = "html.parser"
    status_map: dict[str, NovelStatus] = None
    title_selector: Selector = None
    status_selector: Selector = None
    genre_selector: Selector = None
    tag_selector: Selector = None
    author_name_selector: Selector = None
    author_email_selector: Selector = None
    author_url_selector: Selector = None
    summary_selector: Selector = None

    def __init__(self):
        """Initialize the HttpClient."""
        self.http_client = HttpClient()

    def get_soup(self, content, parser: str = None):
        parser = parser or self.parser
        return BeautifulSoup(content, parser)

    def get_page(self, url) -> BeautifulSoup:
        """Fetch the page at the url and return it as a BeautifulSoup instance."""
        response = self.http_client.get(url)
        response.raise_for_status()
        return self.get_soup(response.text)

    def get_title(self, page: BeautifulSoup) -> str:
        """Extract the title of the Novel from the page."""
        assert self.title_selector is not None, "title_selector is not defined. Define it, or override get_title."
        return self.title_selector.parse_one(page)

    def get_status(self, page: BeautifulSoup) -> NovelStatus:
        """Extract the status of the Novel from the page."""
        assert self.status_selector is not None, "status_selector is not defined. Define it or override get_status."
        assert self.status_map is not None, "status_map is not defined."
        status = self.status_selector.parse_one(page)
        return self.status_map.get(status, NovelStatus.UNKNOWN)

    def get_genres(self, page: BeautifulSoup) -> list[str]:
        """Extract the list of genres for the Novel from the page."""
        return self.genre_selector.parse(page) if self.genre_selector is not None else None

    def get_tags(self, page: BeautifulSoup) -> list[str]:
        """Extract the list of tags for the Novel from the page."""
        return self.tag_selector.parse(page) if self.tag_selector is not None else None

    def get_author(self, page: BeautifulSoup) -> Person:
        assert self.author_name_selector is not None, \
            "author_name_selector is not defined. Define it or override get_author."
        return Person(
            name=self.author_name_selector.parse_one(page),
            email=self.author_email_selector.parse_one(page) if self.author_email_selector is not None else None,
            url=self.author_url_selector.parse_one(page, use_attribute=True) if self.author_url_selector is not None else None,
        )

    def get_summary(self, page: BeautifulSoup) -> str:
        assert self.summary_selector is not None, "summary_selector is not defined. Define it or override get_summary."
        return "\n".join(self.summary_selector.parse(page))

    def scrape(self, url) -> Novel:
        page = self.get_page(url)
        return Novel(
            url=url,
            title=self.get_title(page),
            status=self.get_status(page),
            genres=self.get_genres(page),
            tags=self.get_tags(page),
            author=self.get_author(page),
            summary=self.get_summary(page),
        )


class ChapterScraper:
    pass
