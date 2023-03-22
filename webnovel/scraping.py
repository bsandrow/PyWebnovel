"""Base Functionality for Scraping Webnovel Content."""

from typing import Optional

from apptk.html import Selector
from apptk.http import HttpClient
from bs4 import BeautifulSoup

from webnovel import html
from webnovel.data import Chapter, Image, Novel, NovelStatus, Person

HTTPS_PREFIX = r"https?://(?:www\.)?"
http_client = HttpClient()


class NovelScraper:
    """Base Class for Webnovel Scrapers."""

    site_name: str
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
    cover_image_url_selector: Selector = None
    chapter_content_selector: Selector = None
    chapter_content_filters: list[html.HtmlFilter] = None

    def __init__(self):
        """Initialize the HttpClient."""
        self.http_client = HttpClient(use_cloudscraper=True)
        assert self.site_name is not None

    def get_soup(self, content, parser: str = None):
        """
        Return a BeautifulSoup instance for HTML content passed in.

        :param content: The HTML content to pass to the parser.
        :param parser: (optional) The specific parser for BeautifulSoup to use.
                       Defaults to the class-level parser value.
        """
        parser = parser or self.parser
        return BeautifulSoup(content, parser)

    def get_page(self, url, method: str = "get", data: dict = None) -> BeautifulSoup:
        """Fetch the page at the url and return it as a BeautifulSoup instance."""
        client_method = getattr(self.http_client, method)
        response = client_method(url, data=data)
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
        """Extract the author from the page."""
        assert (
            self.author_name_selector is not None
        ), "author_name_selector is not defined. Define it or override get_author."
        return Person(
            name=self.author_name_selector.parse_one(page),
            email=self.author_email_selector.parse_one(page) if self.author_email_selector is not None else None,
            url=self.author_url_selector.parse_one(page, use_attribute=True)
            if self.author_url_selector is not None
            else None,
        )

    def get_summary(self, page: BeautifulSoup) -> str:
        """Extract the novel's summary/description from the novel page."""
        assert self.summary_selector is not None, "summary_selector is not defined. Define it or override get_summary."
        return "\n".join(self.summary_selector.parse(page))

    def get_cover_image(self, page: BeautifulSoup) -> Optional[Image]:
        """Extract an Image() for the cover image of the novel from the novel's page."""
        if self.cover_image_url_selector is not None:
            # a = self.cover_image_url_selector.parse_one(html=page)
            return Image(url=self.cover_image_url_selector.parse_one(html=page, use_attribute=True))
        return None

    def get_chapters(self, page: BeautifulSoup, url: str) -> list:
        """
        Return the list of Chapters for a webnovel.

        The URL option is required to be passed in, but only a few scrapers will
        probably need to use it.  Some scrapers might need that URL to call a separate
        API that returns the chapter list, while most are probably able to just use the
        content of the novel's page itself to extract said list.

        Extraction of this list will be different from site to site, and there doesn't seem
        to be enough commonalities for there to be a general implemenation that will only
        need to have a specific version in special cases. It really seems like this will just
        have to be custom most of the time.

        :param page: The novel page's HTML content.
        :param url: The url of the novel's page.
        """

    def chapter_extra_processing(self, chapter: Chapter) -> None:
        """Extra per-chapter processing that can be defined per-scraper."""

    def process_chapters(self, chapters: list[Chapter]) -> None:
        """
        Populate html_content attribute of a list of Chapters.

        Use chapter_content_selector / chapter_content_filters to process the content of
        a Chapter fetched via Chapter.url.
        """
        for chapter in chapters:
            page = self.get_page(chapter.url)
            chapter.html_content = self.chapter_content_selector.parse_one(page, use_attribute=False)
            html.run_filters(chapter.html_content, filters=self.chapter_content_filters)
            self.chapter_extra_processing(chapter)

    def scrape(self, url: str) -> Novel:
        """Scrape URL to return a Novel instance populated from extracted information."""
        page = self.get_page(url)
        novel_id = self.get_novel_id(url)
        return Novel(
            url=url,
            site_id=self.site_name,
            novel_id=novel_id,
            title=self.get_title(page),
            status=self.get_status(page),
            genres=self.get_genres(page),
            tags=self.get_tags(page),
            author=self.get_author(page),
            summary=self.get_summary(page),
            chapters=self.get_chapters(page, url=url),
            cover_image=self.get_cover_image(page),
        )
