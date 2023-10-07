"""ScribbleHub.com scrapers and utilities."""

import datetime
import json
import logging
import re

from bs4 import BeautifulSoup, NavigableString, Tag

from webnovel import html
from webnovel.data import Chapter, NovelStatus
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraper, NovelScraper, Selector

SITE_NAME = "ScribbleHub.com"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)

IMGUR_REPLACE_MAP = {
    "https://imgur.com/a/vTB9v0N.png": "https://i.imgur.com/Ngn3XDw.png",
    "https://imgur.com/a/Kfi2vTV": "https://i.imgur.com/cJ2MmA0.jpeg",
}


@html.register_html_filter(name="replace_bad_imgur_urls")
def replace_bad_imgur_urls_filter(element: Tag) -> None:
    """
    Fix some bad imgur image links.

    They are album image links with a file extension appended. They seem to only
    have a single image in the album, so maybe this worked at one point in time,
    but doesn't any longer?

    Just use manual replacement for now to get things working, but in the future
    make this automatic by going to the imgur page and finding the image url in
    code.
    """
    for item in element.find_all("img"):
        src = item.get("src")
        replacement = IMGUR_REPLACE_MAP.get(src)
        if src and replacement:
            item["src"] = replacement


@html.register_html_filter(name="transform_authors_notes.scribblehub")
def authors_notes_filter(html_block: html.Tag) -> None:
    """Transform the author's notes into something better for ebooks."""
    for authors_notes_block in html_block.select(".wi_authornotes"):
        # author = authors_notes_block.select_one(".an_username a").text
        content = authors_notes_block.select_one(".wi_authornotes_body")

        # If there is no content that we're going to display in the block, then
        # there's no point to generating an empty block. An example of this
        # would be an author's notes that only contains an image or a table even
        # though we've turned of images or tables. The only content there would
        # be to display in the original, is content that we've stripped due to
        # ebook building options.
        if content.text.strip() == "":
            html.remove_element(authors_notes_block)
            return

        new_block = BeautifulSoup(
            f'<div class="pywn_authorsnotes">'
            f'   <div class="pywn_authorsnotes-title"> Author\'s Note </div>'
            f'   <div class="pywn_authorsnotes-body">{content}</div>'
            f"</div>",
            "html.parser",
        ).find("div")
        authors_notes_block.replace_with(new_block)


@html.register_html_filter(name="transform_announcements.scribblehub")
def announcements_filter(html_block: html.Tag) -> None:
    """Reformat ScribbleHub "Announcement" blocks."""
    for announcement_block in html_block.select(".wi_news"):
        content = announcement_block.select_one(".wi_news_body")

        if not content.text.strip():
            html.remove_element(announcement_block)
            return

        new_block = BeautifulSoup(
            f'<div class="pywn_announcement">'
            f'   <div class="pywn_announcement-title">-⚠️- Announcement -⚠️-</div>'
            f'   <div class="pywn_announcement-body">{content}</div>'
            f"</div>",
            "html.parser",
        ).find("div")
        announcement_block.replace_with(new_block)


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
            if date_string and (match := re.search(r"(\d+) (?:minute|min)s? ago", date_string.lower())):
                minutes = int(match.group(1))
                return datetime.datetime.now() - datetime.timedelta(seconds=minutes * 60)

            if date_string and (match := re.search(r"(\d+) hours? ago", date_string.lower())):
                hours = int(match.group(1))
                return datetime.datetime.now() - datetime.timedelta(hours=hours)

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
        .pywn_chapter td { padding: 0px !important; }
        .pywn_chapter td p { padding: 5px; }
    """
    content_selector = Selector("#chp_raw")
    author_notes_filter = "transform_authors_notes.scribblehub"

    # Create a default filters list with "remove_blank_elements" excluded
    DEFAULT_FILTERS: list[str] = list(set(html.DEFAULT_FILTERS) - {"remove_blank_elements"})
    content_filters: list[str] = DEFAULT_FILTERS + [
        "transform_announcements.scribblehub",
        "replace_bad_imgur_urls",
    ]

    def post_process_content(self, chapter, content):
        """Post-Processing to remove tables (for now)."""
        for td in content.find_all("td"):
            for p in td.find_all("p"):
                is_after_string = all(
                    isinstance(sibling, NavigableString) and len(sibling.strip()) > 0 for sibling in p.previous_siblings
                )
                if is_after_string:
                    p.insert_before(content.new_tag("p"))

        # Table Notes:
        # -- center tables on page
        # -- need padding around cell contents
        # -- check table complexity before converting to image / prior to support replace with "COMING SOON TABLES!" stub
        # -- look into cell alignment css. Is same for all tables? Author customize it?
        # -- don't remove empty <p> from within tables.
        # -- make font size inside tables smaller?
