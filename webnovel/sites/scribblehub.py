"""ScribbleHub.com scrapers and utilities."""

import logging
import re

from webnovel.data import Chapter, NovelStatus
from webnovel.html import DEFAULT_FILTERS, remove_element
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraper, NovelScraper, Selector

SITE_NAME = "ScribbleHub.com"
NOVEL_URL_PATTERN = HTTPS_PREFIX + r"scribblehub\.com/series/(?P<novel_id>\d+)/(?P<novel_title_slug>[\w\d-]+)/"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class ScribbleHubScraper(NovelScraper):
    """Scraper for ScribbleHub.com."""

    site_name = SITE_NAME
    title_selector = Selector("div.fic_title")
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED, "hiatus": NovelStatus.HIATUS}
    genre_selector = Selector("a.fic_genre")
    tag_selector = Selector(".wi_fic_showtags .wi_fic_showtags_inner a.stag")
    author_name_selector = Selector("div[property='author'] span.auth_name_fic")
    author_url_selector = Selector("div[property='author'] [property='name'] a", attribute="href")
    summary_selector = Selector(".wi_fic_desc")
    cover_image_url_selector = Selector(".novel-cover .fic_image img", attribute="src")

    @staticmethod
    def get_novel_id(url: str) -> str:
        """Return the novel id from the URL."""
        return match.group("novel_id") if (match := re.match(NOVEL_URL_PATTERN, url)) else None

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate that a URL matches something that works for NovelBin.net and the scraper should support."""
        return re.match(NOVEL_URL_PATTERN, url) is not None

    def get_status(self, page):
        """
        Get novel status.

        Can't get status with selectors alone, so need to override.
        """
        items = page.select("ul.widget_fic_similar li")
        for item in items:
            if item.select("span > i.status"):
                status_span = item.find_all("span")[1]
                status_text = status_span.text if status_span else ""
                status_key = status_text.lower().strip()
                if match := re.match(r"(?P<status>.*?)\s+-\s+", status_text):
                    status_key = match.group("status").lower().strip()
                break
        return self.status_map[status_key] if status_key in self.status_map else NovelStatus.UNKNOWN

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances for NovelBin.net."""
        novel_id = self.get_novel_id(url)
        page = self.get_page(
            "https://www.scribblehub.com/wp-admin/admin-ajax.php",
            method="post",
            data={"action": "wi_getreleases_pagination", "pagenum": "-1", "mypostid": str(novel_id)},
        )
        return [
            Chapter(
                url=chapter_li.select_one("A").get("href"),
                title=Chapter.clean_title(chapter_li.select_one("A").text),
                chapter_no=idx + 1,
                # pub_date = chapter_li.select_one(".fic_date_pub").get("title"),
            )
            for idx, chapter_li in enumerate(reversed(page.select("LI")))
        ]


class ScribbleHubChapterScraper(ChapterScraper):
    """Scraper for ScribbleHub.com Chapters."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"scribblehub\.com/read/(?P<NovelId>\d+)-[\d\w-]+/chapter/(?P<ChapterId>\d+)/"
    extra_css: str = """\
        .wi_authornotes {border: 2px solid black; padding: 10px;}
        .wi_authornotes .p-avatar-wrap {float: left;}
        .wi_authornotes .wi_authornotes_body {padding-top: 10px;}
    """
    content_selector = Selector("#chp_raw")
