"""Base Functionality for Scraping Webnovel Content."""

import logging
import re
from typing import Optional, Union

from apptk.html import Selector
from bs4 import BeautifulSoup, Tag
from pyrate_limiter import Duration, Limiter, RequestRate

from webnovel import html, http
from webnovel.data import Chapter, Image, Novel, NovelStatus, ParsingOptions, Person
from webnovel.logs import LogTimer

HTTPS_PREFIX = r"https?://(?:www\.)?"
DEFAULT_LIMITER = Limiter(RequestRate(5, Duration.SECOND))

logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class ScraperBase:
    """Base class for Novel/Chapter scrapers."""

    url_pattern: Union[re.Pattern, str]
    site_name: str
    http_client: http.HttpClient
    limiter: Limiter
    options: ParsingOptions

    def __init__(
        self, options: Optional[Union[dict, ParsingOptions]] = None, http_client: http.HttpClient = None
    ) -> None:
        self.http_client = http_client or http.get_client()
        self.limiter = self.get_limiter()
        self.options = (
            options
            if isinstance(options, ParsingOptions)
            else ParsingOptions.from_dict(options)
            if isinstance(options, dict)
            else ParsingOptions()
        )
        assert self.site_name is not None

    def get_limiter(self):
        """Return the Limiter instance for this scraper."""
        return DEFAULT_LIMITER

    def get_soup(self, content):
        """
        Return a BeautifulSoup instance for HTML content passed in.

        :param content: The HTML content to pass to the parser.
        """
        return BeautifulSoup(content, self.options.html_parser)

    def get_page(self, url, method: str = "get", data: dict = None) -> BeautifulSoup:
        """Fetch the page at the url and return it as a BeautifulSoup instance."""
        client_method = getattr(self.http_client, method)
        with self.limiter.ratelimit("get_page", delay=True):
            response = client_method(url, data=data)
            if response.elapsed.total_seconds() > 1:
                logger.debug("Took %f second(s) to fetch url=%s", response.elapsed.total_seconds(), repr(url))
        response.raise_for_status()
        return self.get_soup(response.text)

    @classmethod
    def supports_url(cls, url: str) -> bool:
        """Return True if scraper should support scraping the provided URL."""
        if isinstance(cls.url_pattern, re.Pattern):
            return cls.url_pattern.match(url) is not None
        return re.match(cls.url_pattern, url) is not None


class NovelScraper(ScraperBase):
    """Base Class for Webnovel Scrapers."""

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

    # Additional CSS to add to the novel based on the site that this was scraped
    # from.
    extra_css: Optional[str] = None

    @classmethod
    def get_novel_id(cls, url) -> str:
        """Return the novel id from the URL."""
        return match.group("NovelID") if (match := re.match(cls.url_pattern, url)) else None

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

    def get_summary(self, page: BeautifulSoup) -> Union[str, Tag]:
        """Extract the novel's summary/description from the novel page."""
        assert self.summary_selector is not None, "summary_selector is not defined. Define it or override get_summary."
        return self.summary_selector.parse_one(page, use_attribute=False)

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

    def post_processing(self, page: BeautifulSoup, url: str, novel: Novel):
        """Additional scraper-specific code to add things to or modify the Novel before returning from scrape()."""

    def scrape(self, url: str) -> Novel:
        """Scrape URL to return a Novel instance populated from extracted information."""
        page = self.get_page(url)
        novel_id = self.get_novel_id(url)
        novel = Novel(
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
            extra_css=self.extra_css,
        )
        self.post_processing(page, url, novel)
        return novel


class ChapterScraper(ScraperBase):
    """Base scraper for chapter information."""

    content_selector: Selector = None
    content_filters: tuple[html.HtmlFilter] = html.DEFAULT_FILTERS
    extra_css: Optional[str] = None

    @classmethod
    def get_chapter_slug(cls, url: str) -> Optional[str]:
        """
        Extract the chapter's slug from the chapter url.

        :param url: The URL of a chapter.
        """
        if not cls.supports_url(url):
            raise ValueError("Not a valid chapter url for {cls.site_name}: {url}")

        if match := re.match(cls.url_pattern, url):
            return match.group("ChapterID")
        return None

    def post_processing(self, chapter: Chapter) -> None:
        """
        Post-processing of the chapter after html has been filled in.

        By default, this will run the
        """
        html.run_filters(chapter.html, filters=self.content_filters)

    def get_content(self, page: BeautifulSoup) -> Tag:
        """Extract the section of the HTML from page that contains the chapter's content."""
        return self.content_selector.parse_one(page, use_attribute=False)

    def process_chapter(self, chapter: Chapter) -> None:
        """
        Populate the html of a Chapter.

        Use content_selector to extract chapter content, then pass to post_processing
        a Chapter fetched via Chapter.url.
        """
        page = self.get_page(chapter.url)
        chapter.html = self.get_content(page)
        self.post_processing(chapter)
