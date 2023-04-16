"""ScribbleHub.com scrapers and utilities."""

import datetime
import json
import logging
import re

from bs4 import BeautifulSoup

from webnovel.data import Chapter, Novel, NovelStatus
from webnovel.html import DEFAULT_FILTERS, remove_element
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraper, NovelScraper, Selector

SITE_NAME = "ScribbleHub.com"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class ScribbleHubScraper(NovelScraper):
    """Scraper for ScribbleHub.com."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"scribblehub\.com/series/(?P<NovelID>\d+)/(?P<novel_title_slug>[\w\d-]+)/"
    title_selector = Selector("div.fic_title")
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED, "hiatus": NovelStatus.HIATUS}
    genre_selector = Selector("a.fic_genre")
    tag_selector = Selector(".wi_fic_showtags .wi_fic_showtags_inner a.stag")
    author_name_selector = Selector("div[property='author'] span.auth_name_fic")
    author_url_selector = Selector("div[property='author'] [property='name'] a", attribute="href")
    summary_selector = Selector(".wi_fic_desc")
    cover_image_url_selector = Selector(".novel-cover .fic_image img", attribute="src")

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

        def parse_date(date_string):
            if date_string:
                return datetime.datetime.strptime(date_string, "%b %d, %Y %I:%M %p")
            return None

        return [
            Chapter(
                url=(url := chapter_li.select_one("A").get("href")),
                title=Chapter.clean_title(chapter_li.select_one("A").text),
                chapter_no=idx + 1,
                slug=ScribbleHubChapterScraper.get_chapter_slug(url),
                # pub_date format: Mar 30, 2020 04:46 AM
                pub_date=parse_date(chapter_li.select_one(".fic_date_pub").get("title")),
            )
            for idx, chapter_li in enumerate(reversed(page.select("LI")))
        ]

    def post_processing(self, page, url, novel):
        """Scrape extra information from the novel page."""
        novel.extras = {}

        content_warnings = [li.text for li in page.select("li.mature_contains")]
        if content_warnings:
            novel.extras["Content Warning"] = content_warnings

        rankings = page.select("a.rank-link span.catname")
        if rankings:
            novel.extras["Rankings"] = ["Ranked " + r.text.strip() for r in rankings]

        user_stats = page.select("ul.statUser li")
        if user_stats:
            novel.extras["User Stats"] = [stat.text.strip().replace("\n", " ") for stat in user_stats]

        ld_json_content = page.select("script[type='application/ld+json']")
        for ld_json in ld_json_content:
            _json = json.loads(ld_json.text)
            if _json.get("@type") == "Book":
                pub_date_str = _json.get("datePublished")
                if pub_date_str:
                    novel.published_on = datetime.datetime.strptime(pub_date_str, "%Y-%m-%d")

        chapter_pub_dates = [ch.pub_date for ch in novel.chapters if ch.pub_date is not None]
        has_chapter_pub_dates = len(chapter_pub_dates) == len(
            novel.chapters
        )  # don't do this if we only have some pub dates
        if has_chapter_pub_dates:
            novel.last_updated_on = max(chapter_pub_dates)

        fic_stats = page.select_one(".fic_stats")
        if fic_stats:
            for stat in fic_stats.select("span.st_item"):
                for check, key in {
                    "Views": "Views",
                    "Favorites": "Favourites",
                    "Chapters/Week": "Chapters per Week",
                    "Readers": "Readers",
                }.items():
                    if check in stat.text:
                        novel.extras[key] = f"{stat.text.strip()} (as of {datetime.date.today():%Y-%b-%d})"

        return super().post_processing(page, url, novel)


class ScribbleHubChapterScraper(ChapterScraper):
    """Scraper for ScribbleHub.com Chapters."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"scribblehub\.com/read/(?P<NovelID>\d+)-[\d\w-]+/chapter/(?P<ChapterID>\d+)/"
    extra_css: str = """\
        .wi_authornotes {border: 2px solid black; padding: 10px;}
        .wi_authornotes .p-avatar-wrap {float: left;}
        .wi_authornotes .wi_authornotes_body {padding-top: 10px;}
    """
    content_selector = Selector("#chp_raw")

    def post_processing(self, chapter):
        """Post-Processing to Transform Author's Notes Block."""
        super().post_processing(chapter)

        for authors_notes_block in chapter.html.select(".wi_authornotes"):
            parent = authors_notes_block.parent
            new_block = BeautifulSoup(
                """
                <div class="pywn_authors-notes">
                    <b><i>Author's Note</i></b>
                    <p>Author: X</p>
                </div>
                """
                "html.parser",
            )
