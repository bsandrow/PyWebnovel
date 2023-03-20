"""ReaperScans scrapers and utilities."""

import logging
import re
import time

from bs4 import Tag
from requests import Response

from webnovel import html
from webnovel.data import Chapter, NovelStatus
from webnovel.livewire import LiveWireAPI
from webnovel.logs import LogTimer
from webnovel.scraping import NovelScraper, Selector

URL_PATTERN = r"https?://(?:www\.)?reaperscans\.com/novels/(\d+-[\w-]+)"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


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

    def get_page(self, page_no: int) -> str:
        """Move the chapter list to a specific page (in the list) and return the HTML."""
        response = self.make_call("gotoPage", page_no, "page")
        return self.update_page_history(response)

    def next_page(self) -> str:
        """Move the chapter list to the next page (in the list) and return the HTML."""
        response = self.make_call("nextPage", "page")
        return self.update_page_history(response)

    def previous_page(self) -> str:
        """Move the chapter list to the previous page (in the list) and return the HTML."""
        response = self.make_call("prevPage", "page")
        return self.update_page_history(response)

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


class RemoveTrailingHorizontalBarsFilter(html.HtmlFilter):
    """Remove the trailing '----' bars and 'blank' <p> elements at the end of the chapter."""

    def filter(self, element: Tag) -> None:
        """
        Reverse iterate over the children removing all "blank" elements and "----" content elements.

        Break out of the loop the first time we find something different. Technically these sections should have some
        text between the bars, but another filter should be removing those leaving just "empty" <p> elements and the
        "manual" horizontal bars.
        """
        for child in reversed(tuple(element.children)):
            if child.text.strip() == "" or re.match(r"^[-—–_—⸺﹘⸻]+$", child.text.strip()) is not None:
                html.remove_element(child)
                continue
            else:
                break


class RemoveStartingBannerFilter(html.HtmlFilter):
    """
    Remove the "REAPERSCANS" at the top of each chapter.

    We don't need attribution at the top of each chapter. We'll put it in the front of the ebook.
    """

    def filter(self, element: Tag) -> None:
        """Remove 'blank' elements and the REAPERSCANS banner. Bail the first time we find something else."""
        for child in element.find_all(recursive=False):
            if child.text.strip().lower() in ("reaperscans", "reaper scans"):
                html.remove_element(child)
                break


class ReaperScansScraper(NovelScraper):
    """Scraper for ReaperScans.com."""

    site_name = "ReaperScans.com"

    title_selector = Selector("MAIN > DIV:nth-child(2) > DIV > DIV:first-child H1")
    status_selector = Selector("MAIN > DIV:nth-child(2) > SECTION > DIV:first-child DL > DIV:nth-child(4) DD")
    summary_selector = Selector("MAIN > DIV:nth-child(2) > SECTION > DIV:first-child > DIV > P")
    chapter_selector = Selector(r"MAIN > DIV:nth-child(2) > DIV DIV[wire\:id]")
    cover_image_url_selector = Selector("main > div:nth-child(2) > div img", attribute="src")
    chapter_title_selector = Selector("ARTICLE > P:nth-child(7)")
    # next_chapter_selector = Selector(
    #     "MAIN > DIV:nth-child(2) > NAV:nth-child(2) > DIV:nth-child(3) > A:nth-child(2)", attribute="href"
    # )
    # first_chapter_link = Selector(
    #     "MAIN > DIV:nth-child(2) > DIV > DIV:first-child > DIV A:first-child", attribute="href"
    # )
    chapter_content_selector = Selector("ARTICLE.prose")
    chapter_content_filters = html.DEFAULT_FILTERS + [
        # RemoveStartingBannerFilter(),
        RemoveTrailingHorizontalBarsFilter()
    ]
    status_map = {
        "Ongoing": NovelStatus.ONGOING,
        # I haven't seen any with this on the site, so I'm only guessing that the status would be "Complete" when they
        # finish the novel.
        "Completed": NovelStatus.COMPLETED,
        "Dropped": NovelStatus.DROPPED,
        "On hold": NovelStatus.HIATUS,
    }

    @staticmethod
    def get_novel_id(url: str) -> str:
        """Return the id of the novel that ReaperScans uses."""
        match = re.match(URL_PATTERN, url)
        return match.group(1) if match is not None else None

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate that a URL matches something that works for ReaperScans.com and the scraper should support."""
        return re.match(URL_PATTERN, url) is not None

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
        api = ChapterListAPI(
            app_url="https://reaperscans.com/",
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
                time.sleep(2)

        return sorted(chapters, key=lambda ch: ch.chapter_no)
