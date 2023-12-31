"""ReaperScans scrapers and utilities."""

import logging
import re
import urllib.parse

from bs4 import BeautifulSoup, Tag
from pyrate_limiter import Limiter, RequestRate
from requests import Response

from webnovel import html, http
from webnovel.data import Chapter, NovelStatus
from webnovel.livewire import LiveWireAPI
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector

SITE_NAME = "ReaperScans.com"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)

LIMITER = Limiter(RequestRate(3, 7))  # 3 requests per 7 seconds


def get_csrf_token(element: Tag) -> str:
    """Return the CSRF token from the page."""
    results = element.select("[name=csrf-token]")
    return results[0]["content"] if len(results) else None


def get_wire_id(element: Tag) -> str:
    """Return the LiveWire ID in the passed-in DOM."""
    if "wire:id" in element.attrs:
        return element["wire:id"]
    results = element.select(r"[wire\:id]")
    if len(results) > 1:
        raise ValueError("Found multiple LiveWire IDs.")
    return results[0]["wire:id"] if results else None


def build_chapter_list_request(page: int, path: str, wire_id: str, locale: str = "en"):
    """
    Build a LiveWire/Laravel API request for the novel's chapter list.

    :param page: The page number being requested.
    :param path: The story (e.g. "novel/{novel-slug}")
    :param wire_id: The id generated for this "function" call. Found in "wire:id" attribute in HTML DOM.
    :param locale: The locale. I don't have any reason to change this, but I added it as an optional param anyways.
    """
    return {
        "fingerprint": {
            "id": wire_id,
            "locale": locale,
            "method": "GET",
            "name": "frontend.novel-chapters-list",
            "path": path,
            "v": "acj",
        },
        "serverMemo": {
            "checksum": None,  # TODO
            "children": [],
            "data": {"novel": [], "page": page, "paginators": {"page": page}},
            "dataMeta": {
                "models": {
                    "novel": {
                        "class": "App\\Models\\Novel",
                        "collectionClass": None,
                        "connection": "pgsql",
                        "id": None,  # TODO  novel id can pull from cover image URL
                        "relations": [],
                    }
                }
            },
            "errors": [],
            "htmlHash": None,  # TODO
        },
        "updates": [
            {
                "payload": {
                    "id": None,  # TODO
                    "method": "gotoPage",
                    "params": [1, "page"],
                },
                "type": "callMethod",
            }
        ],
    }


class ChapterListAPI(LiveWireAPI):
    """
    The livewire.js API wrapper for the chapter list.

    Just adds some methods around the supported calls in the chapter list component. Each of these methods are just
    wrappers around LiveWireAPI.make_call with specific parameters and extracting the part of the response that we care
    about.
    """

    page_history: dict = {}

    @property
    def current_page(self) -> int:
        """
        Return the page that the current state is on.

        Since the serverMemo for this component is required to be stored to make the next request, we can access this
        to return the "current" page of the component (which is useful since we have next/previous page calls).
        """
        memo = self.most_recent_server_memo()
        return memo.get("data", {}).get("page")

    @LIMITER.ratelimit("lwapi", delay=True)
    def get_page(self, page_no: int) -> str:
        """Move the chapter list to a specific page (in the list) and return the HTML."""
        response = self.make_call("gotoPage", page_no, "page")
        return self.update_page_history(response)

    @LIMITER.ratelimit("lwapi", delay=True)
    def next_page(self) -> str:
        """Move the chapter list to the next page (in the list) and return the HTML."""
        response = self.make_call("nextPage", "page")
        return self.update_page_history(response)

    @LIMITER.ratelimit("lwapi", delay=True)
    def previous_page(self) -> str:
        """Move the chapter list to the previous page (in the list) and return the HTML."""
        response = self.make_call("prevPage", "page")
        return self.update_page_history(response)

    @LIMITER.ratelimit("lwapi", delay=True)
    def update_page_history(self, response: Response):
        """Update the page_history to store the HTML content of the returned page."""
        response_json = response.json()
        page_no: int = response_json["serverMemo"]["data"]["page"]
        html = response_json.get("effects", {}).get("html")
        if page_no in self.page_history and not html:
            html = self.page_history[page_no]
        else:
            self.page_history[page_no] = html
        return html


@html.register_html_filter(name="remove_trailing_hrs")
def trailing_hrs_filter(element: Tag) -> None:
    """
    Reverse iterate over the children removing all "blank" elements and "----" content elements from the end of the chapter.

    Break out of the loop the first time we find something different. Technically these sections should have some
    text between the bars, but another filter should be removing those leaving just "empty" <p> elements and the
    "manual" horizontal bars.
    """
    for child in reversed(tuple(element.children)):
        child_text = child.text.strip()
        if child_text == "" or re.match(r"^[-—–_—⸺﹘⸻]+$", child_text) is not None:
            html.remove_element(child)
            continue
        else:
            break


@html.register_html_filter(name="remove_reaperscans_banner")
def banner_filter(element: Tag) -> None:
    """
    Remove the "REAPERSCANS" at the top of each chapter.

    Remove 'blank' elements and the REAPERSCANS banner. Bail the first time
    we find something else.  We don't need attribution at the top of each
    chapter. We'll put it in the front of the ebook.
    """
    for child in element.find_all(recursive=False):
        child_text = child.text.strip().lower()
        if re.match(r"reaper\s*scans", child_text, re.IGNORECASE):
            html.remove_element(child)
            break


class ReaperScansScraper(NovelScraperBase):
    """Scraper for ReaperScans.com."""

    site_name = SITE_NAME
    url_pattern = r"https?://(?:www\.)?reaper(?:scans|comics)\.com/novels/(?P<NovelID>\d+-[\w-]+)"
    title_selector = Selector("main > div > div > div:nth-child(1) h1")
    summary_selector = Selector("main > div > section > div:first-child > div > p")
    chapter_selector = Selector(r"main div[wire\:id]")
    cover_image_url_selector = Selector("main > div > div img", attribute="src")
    chapter_title_selector = Selector("ARTICLE > P:nth-child(7)")
    status_map = {
        "ongoing": NovelStatus.ONGOING,
        # I haven't seen any with this on the site, so I'm only guessing that
        # the status would be "Complete" when they finish the novel.
        "completed": NovelStatus.COMPLETED,
        "dropped": NovelStatus.DROPPED,
        "on hold": NovelStatus.HIATUS,
    }

    @staticmethod
    def _get_section_value(page: BeautifulSoup, title: str) -> str | None:
        """Find the <dt>/<dd> pairs by the text value of the <dt> element."""
        section = page.select_one("main > div > section")
        title_el = section.find("dt", text=re.compile(title))
        if not title_el:
            return None
        value_el = title_el.parent.find("dd")
        return value_el.text.strip() if value_el else None

    def get_limiter(self):
        """Return rate limiter for ReaperScans."""
        return LIMITER

    def get_status(self, page: BeautifulSoup) -> NovelStatus:
        """Get the release status."""
        status_value = self._get_section_value(page, "Release Status")
        if not status_value:
            return NovelStatus.UNKNOWN
        return self.status_map.get(status_value.lower())

    def get_genres(self, page):
        """Return empty list since ReaperScans doesn't have genres listed on the novel page."""
        return []

    def get_author(self, page):
        """Return None because ReaperScans.com doesn't list the author other than in the cover image for the novel."""
        # Note: The only place I can find the author on their page is in the cover image, which
        #       obviously isn't scrape-able.
        return None

    @timer("Fetch list of chapters")
    def get_chapters(self, page, url) -> list[Chapter]:
        """
        Return the list of Chapter instances for ReaperScans.com.

        :param page: The BeautifulSoup instance for the novel page.
        :param url: Not used here, but part of the api so we need to accept it.
        """

        def log_page(chapter_count, current_page):
            logger.debug("Fetched %02d chapter(s) from Chapter List API [page=%d]", chapter_count, current_page)

        chapters = []
        chapter_list = self.chapter_selector.parse_one(page, use_attribute=False)
        csrf_token = get_csrf_token(page)
        wire_id = get_wire_id(chapter_list)
        # print(f"wire_id={wire_id!r} . csrf_token={csrf_token!r}")

        _url = urllib.parse.urlparse(url)
        api = ChapterListAPI(
            app_url=f"{_url.scheme}://{_url.netloc}/",
            wire_id=wire_id,
            element=chapter_list,
            csrf_token=csrf_token,
        )
        chapter_list_items = chapter_list.select(r"LI[wire\:key]")
        log_page(len(chapter_list_items), api.current_page)

        while chapter_list_items:
            chapter_item = chapter_list_items.pop()
            if not chapter_item.select_one("i.fa-coins"):
                chapter_slug = chapter_item["wire:key"]
                url = chapter_item.select_one("a")["href"]
                title = Chapter.clean_title(chapter_item.select_one("p").text)
                chapter_no = Chapter.extract_chapter_no(title)
                chapter = Chapter(url=url, title=title, chapter_no=int(chapter_no), slug=chapter_slug)
                chapters.append(chapter)

            if len(chapter_list_items) < 1:
                # NOTE: next_page() will always return content, but after the last page extracting chapter_list_items
                #       will end up with and empty list which will break the loop.
                page_html = api.next_page()
                chapter_list = self.get_soup(page_html)
                chapter_list_items = chapter_list.select(r"LI[wire\:key]")
                log_page(len(chapter_list_items), api.current_page)
                # time.sleep(2)

        return sorted(chapters, key=lambda ch: ch.chapter_no)


class ReaperScansChapterScraper(ChapterScraperBase):
    """Scraper for ReaperScans.com chapter content."""

    site_name = SITE_NAME
    url_pattern = (
        HTTPS_PREFIX + r"reaper(?:scans|comics).com/novels/(?P<NovelID>[\w\d-]+)/chapters/(?P<ChapterID>[\d\w-]+)"
    )
    content_selector = Selector("ARTICLE.prose")
    content_filters = html.DEFAULT_FILTERS + ["remove_trailing_hrs"]  # + ["remove_reaperscans_banner"]

    def get_limiter(self):
        """Return rate limiter for ReaperScans."""
        return LIMITER
