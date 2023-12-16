"""Base Functionality for Scraping Webnovel Content."""

import datetime
import itertools
import logging
import re
from typing import Callable, Union
import urllib.parse

from apptk.html import Selector
from bs4 import BeautifulSoup, Tag
from pyrate_limiter import Duration, Limiter, RequestRate

from webnovel import conf, html, http
from webnovel.data import Chapter, Image, Novel, NovelStatus, Person
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
    options: conf.ParsingOptions

    def __init__(
        self, options: Union[dict, conf.ParsingOptions] | None = None, http_client: http.HttpClient = None
    ) -> None:
        self.http_client = http_client or http.get_client()
        self.limiter = self.get_limiter()
        self.options = (
            options
            if isinstance(options, conf.ParsingOptions)
            else conf.ParsingOptions.from_dict(options)
            if isinstance(options, dict)
            else conf.ParsingOptions()
        )
        assert self.site_name is not None

    def get_limiter(self):
        """Return the Limiter instance for this scraper."""
        return DEFAULT_LIMITER

    @staticmethod
    def _text(tag: Tag) -> str | None:
        """Turn an element into text."""
        return tag.text.strip() if tag else None

    @staticmethod
    def _date(date_string: str, date_format: str = "%B %d, %Y") -> datetime.datetime | None:
        """Extract a datetime from the release date element."""
        if match := re.search(r"(\d+) hours? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(hours=int(match.group(1)))

        if match := re.search(r"(\d+) minutes? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(minutes=int(match.group(1)))

        if match := re.search(r"(\d+) seconds? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(seconds=int(match.group(1)))

        if match := re.search(r"(\d+) days? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(days=int(match.group(1)))

        try:
            return datetime.datetime.fromisoformat(date_string)
        except ValueError:
            pass

        try:
            return datetime.datetime.strptime(date_string, date_format)
        except ValueError:
            pass

        return None

    def get_soup(self, content):
        """
        Return a BeautifulSoup instance for HTML content passed in.

        :param content: The HTML content to pass to the parser.
        """
        return BeautifulSoup(content, self.options.html_parser)

    def get_json(self, url, method: str = "get", data: dict = None) -> Union[dict, list]:
        """Fetch the JSON at the URL and return it."""
        client_method = getattr(self.http_client, method)
        with self.limiter.ratelimit("get_page", delay=True):
            response = client_method(url, data=data)
            if response.elapsed.total_seconds() > 1:
                logger.debug("Took %f second(s) to fetch url=%s", response.elapsed.total_seconds(), repr(url))
        response.raise_for_status()
        return response.json()

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


class NovelScraperBase(ScraperBase):
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
    extra_css: str | None = None

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

    def get_cover_image(self, page: BeautifulSoup) -> Image | None:
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


class ChapterScraperBase(ScraperBase):
    """Base scraper for chapter information."""

    content_selector: Selector = None
    content_filters: tuple[str] = html.DEFAULT_FILTERS
    extra_css: str | None = None
    supports_author_notes: bool = False
    author_notes_filter: str = None

    @classmethod
    def get_chapter_slug(cls, url: str) -> str | None:
        """
        Extract the chapter's slug from the chapter url.

        :param url: The URL of a chapter.
        """
        if not cls.supports_url(url):
            raise ValueError(f"Not a valid chapter url for {cls.site_name}: {url}")

        if match := re.match(cls.url_pattern, url):
            return match.group("ChapterID")
        return None

    def post_process_content(self, chapter: Chapter, content: Tag) -> None:
        """Process Chapter Content After Defined Filters/Tranformations Are Run."""

    def post_processing(self, chapter: Chapter) -> None:
        """
        Post-Processing of Chapter HTML.

        Take the HTML in Chapter.original_html and process it into the HTML in
        Chapter.html which will be saved into the ebook.

        The method post_process_content can be defined to hook into this after
        all of the main processing.
        """
        chapter.populate_html(callback=self.post_process_content)

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
        content = self.get_content(page)
        content_string = str(content)

        if content is None or content_string.strip() == "":
            logger.error(
                "Unable to scrape any content from the chapter page (title=%r | url=%r | scraper=%r)",
                chapter.url,
                chapter.title,
                self.__class__,
            )

        chapter.original_html = content_string
        chapter.html = content_string
        chapter.filters = self.content_filters
        if self.author_notes_filter:
            chapter.filters += [self.author_notes_filter]

        self.post_processing(chapter)
        if chapter.html is None or chapter.html.strip() == "":
            logger.error(
                "Chapter HTML content is empty after post-processing! (title=%r | url=%r | scraper=%r)",
                chapter.url,
                chapter.title,
                self.__class__,
            )


class WpMangaNovelInfoMixin(NovelScraperBase):
    """
    A mixin for getting novel info from sites that use "wp-manga" WordPress plugin.

    There seems to be a "wp-manga" WordPress plugin that a lot of sites use to
    display parts of novels. Using this mixin reduces the duplication of code
    when sites using this plugin have commonalities for the novel information
    section (i.e. they haven't modified it too heavily)
    """

    # <div class="summary_content">
    #   <div class="post-status">
    #     <div class="post-content_item">
    #       <div class="summary-heading"><h5>Project</h5></div>
    #       <div class="summary-content"><a href="$URL$" rel="tag">Active</a></div>
    #     </div>
    #     <div class="post-content_item">
    #       <div class="summary-heading"><h5>Novel</h5></div>
    #       <div class="summary-content">OnGoing</div>
    #     </div>
    #     <div class="manga-action">
    # </div>
    post_content_classes = ["post-content", "post-status"]
    post_content_item_class = "post-content_item"
    post_content_item_heading_class = "summary-heading"
    post_content_item_content_class = "summary-content"

    #: The date format (past to strptime) used to parse the post date from
    #: chapter list entries.
    chapter_date_format: str | None = None

    status_section_name = "Status"
    author_section_name = "Author(s)"
    tags_section_name = "Tag(s)"
    genres_section_name = "Genre(s)"

    #: CSS Selector for the <li> elements in the ajax response containing the
    #: full list of chapters.  Usually .wp-manga-chapter works, but needs the
    #: .free-chap selector when a site has paid / free chapters.
    chapter_selector = ".wp-manga-chapter.free-chap"

    #: The mapping of status values on the page, to NovelStatus values.
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED}

    #: The function used to exctract the slug for the chapter.
    get_chapter_slug: None | Callable = None

    def get_title(self, page: BeautifulSoup) -> str:
        """Extract the title from the wp-manga Header."""
        title_html = page.select_one(".post-title h1")
        if title_html:
            return title_html.text.strip()
        return None

    def post_processing(self, page: BeautifulSoup, url: str, novel: Novel):
        """
        Process extra information and use it to modify the novel.

        In this case, add additional things to Novel.extras that can be scraped
        from the site.
        """
        super().post_processing(page, url, novel)
        novel.extras = novel.extras or {}
        new_extras = self.get_extras(page)

        # Before overwriting any pre-existing data where key collisions happen,
        # do a quick check if any collisions exist, and log a warning. There's
        # no point in completely bailing out of the operation over these
        # collisions, but this way they aren't just being silently ignored
        # either.
        previous_keys = set(novel.extras.keys())
        new_keys = set(new_extras.keys())
        if collisions := previous_keys & new_keys:
            logger.warn("Key collisions while building extras: %s", collisions)

        novel.extras.update(new_extras)

    def get_author(self, page: BeautifulSoup) -> Person | None:
        """Extract the author."""
        sections = self.get_status_section(page)
        author_section = sections.get(self.author_section_name)
        if author_section:
            authors = [
                Person(name=author.text.strip(), url=author.get("href")) for author in author_section.select("a")
            ]
            # !! Warn about this until multiple authors are supported
            if len(authors) > 1:
                logger.warn("Found multiple authors: %s", authors)

            return authors[0] if len(authors) > 0 else None

        # Some sites don't bother to put the authors on there. It's unfortunate,
        # but there's no way to automatically remedy this.
        return None

    def get_tags(self, page: BeautifulSoup) -> list[str]:
        """Extract tags from page."""
        tags = None
        sections = self.get_status_section(page)
        tags_section = sections.get(self.tags_section_name)
        if tags_section:
            tags = [tag.text.strip() for tag in tags_section.select("a")]
        return tags

    def get_genres(self, page: BeautifulSoup) -> list[str] | None:
        """Extract genres from page."""
        genres = None
        sections = self.get_status_section(page)
        genres_section = sections.get(self.genres_section_name)
        if genres_section:
            genres = [genre.text.strip() for genre in genres_section.select("a")]
        return genres

    def get_summary(self, page: BeautifulSoup) -> str | Tag:
        """Extract the summary from the page."""
        return page.select_one(".c-page__content > .description-summary > .summary__content")

    def get_cover_image(self, page: BeautifulSoup) -> Image | None:
        """Extract the cover image from the wp-manga header."""
        img = page.select_one(".summary_image img")
        if img:
            image_url = img.get("data-src") or img.get("src")
            return Image(url=image_url)
        return None

    def get_status_section(self, page: Tag) -> dict[str, Tag]:
        """
        Extract the items on the right side of the novel summary section.

        These items are usually: Status, Release (release year), Project
        (active, dropped, etc).

        Returns a mapping of the section title to the HTML tree that holds the
        section content. Some sections are just text, but others could contain
        links. Returning the section's HTML tree allows the caller to decide
        what to do with the information.

        :params page: The HTML tree to parse for this section.
        """
        sections = {}
        post_status_sections = [page.select_one(f"div.{_class}") for _class in self.post_content_classes]
        post_content_items = itertools.chain.from_iterable(
            post_status_section.select(f"div.{self.post_content_item_class}")
            for post_status_section in post_status_sections
        )

        for post_content_item in post_content_items:
            if (heading := post_content_item.select_one(f"div.{self.post_content_item_heading_class}")) and (
                content := post_content_item.select_one(f"div.{self.post_content_item_content_class}")
            ):
                sections[heading.text.strip()] = content

        return sections

    def get_extras(self, page: Tag) -> dict:
        """Extract any extra (i.e. non-core) information."""
        extras = {}

        for heading, section in self.get_status_section(page).items():
            if section not in (
                self.status_section_name,
                self.author_section_name,
                self.genres_section_name,
                self.tags_section_name,
            ):
                extras[heading] = self._text(section)
                if link := section.find("a"):
                    extras[heading] = {"link": link.get("href"), "text": self._text(section)}

        return extras

    def get_status(self, page: Tag) -> NovelStatus:
        """Extract the novel's status from the page."""
        status_sections = self.get_status_section(page)
        status_content = status_sections.get(self.status_section_name)
        status_text = self._text(status_content) or ""
        return self.status_map.get(status_text.lower(), NovelStatus.UNKNOWN)

    def get_chapters(self, page: BeautifulSoup, url: str) -> list:
        """Get the list of chapters from the novel page."""
        novel_id = self.get_novel_id(url)
        ajax_url = urllib.parse.urljoin(url, f"/novel/{novel_id}/ajax/chapters/")
        ajax_page = self.get_page(ajax_url, method="post")
        assert self.chapter_date_format is not None
        return [
            Chapter(
                url=(url := chapter_li.select_one("A").get("href")),
                title=Chapter.clean_title(chapter_li.select_one("A").text.strip()),
                chapter_no=idx,
                pub_date=self._date(
                    self._text(chapter_li.select_one(".chapter-release-date")),
                    date_format=self.chapter_date_format,
                ),
                slug=(self.get_chapter_slug(url) if self.get_chapter_slug else None),
            )
            for idx, chapter_li in enumerate(reversed(ajax_page.select(self.chapter_selector)))
        ]
