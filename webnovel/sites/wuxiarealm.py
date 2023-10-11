"""WuxiaRealm.com scrapers and utilities."""

import datetime
import logging
import re
from typing import Union

from bs4 import BeautifulSoup, Tag

from webnovel import data, errors, html
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraper, NovelScraperBase, Selector

SITE_NAME = "WuxiaRealm.com"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class WuxiaRealmScraper(NovelScraperBase):
    """Novel Scraper for WuxiaRealm.com."""

    url_pattern = HTTPS_PREFIX + r"wuxiarealm\.com/novel/(?P<NovelID>[\w\d-]+)/"
    site_name = "WuxiaRealm.com"
    url_cache: dict
    status_map = {
        "ongoing": data.NovelStatus.ONGOING,
        "complete": data.NovelStatus.COMPLETED,
        "hiatus": data.NovelStatus.HIATUS,
    }

    @staticmethod
    def build_chapter_list_url(novel_id: str, page_size: int = 100, order: str = "ASC", page_no: int = 1):
        """Build the chapter list API URL based on the passed parameters."""
        assert order in ("ASC", "DESC"), "Only valid values to order are: ASC and DESC"
        assert page_size <= 100, "The API limits page size to 100. Larger values are ignored."
        params = f"category={novel_id}&perpage={page_size}&order={order}&paged={page_no}"
        return f"https://wuxiarealm.com/wp-json/novel-id/v1/dapatkan_chapter_dengan_novel?{params}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_cache = {}

    def get_series_json(self, url: str) -> Union[dict, list]:
        """Fetch the series JSON, but use a cache to prevent multiple look-ups."""
        if url not in self.url_cache:
            self.url_cache[url] = self.get_json(url)
        return self.url_cache[url]

    def get_series_json_url(self, page) -> str:
        """Extract the series json URL from the series page."""
        head = page.find("head")
        link = head.select_one('link[rel="alternate"][type="application/json"]')
        return link.get("href").strip()

    def get_title(self, page):
        """Extract the series title."""
        url = self.get_series_json_url(page)
        series_json = self.get_series_json(url)
        return series_json["title"]["rendered"]

    def get_summary(self, page):
        """Extract the series summary."""
        url = self.get_series_json_url(page)
        series_json = self.get_series_json(url)
        return next(BeautifulSoup(series_json["content"]["rendered"], "html.parser").children)

    def get_genres(self, page):
        """Extract genres."""
        url = self.get_series_json_url(page)
        series_json = self.get_series_json(url)
        series_id = series_json["id"]
        genre_url = f"https://wuxiarealm.com/wp-json/wp/v2/genre?post={series_id}"
        genres_json = self.get_series_json(genre_url)
        return [genre["name"] for genre in genres_json]

    def get_tags(self, page):
        """Extract tags."""
        tags_list = page.select_one("#tagku")
        return [list_item.text.strip() for list_item in tags_list.find_all("li", recursive=False)]

    def get_author(self, page):
        """Return the author."""
        for elem in page.select("div.mb-4"):
            h3 = elem.find("h3")
            if h3 and h3.text.strip() == "Author":
                li = elem.find("li")
                if li and li.text.strip().lower() != "n/a":
                    return data.Person(name=li.text.strip())
        return None

    def get_chapters(self, page, url):
        """Iterate over the paginated chapter list API to build the list of chapters."""
        url = self.get_series_json_url(page)
        series_json = self.get_series_json(url)
        series_id = series_json["id"]
        page_no = 1
        chapter_list = []

        while chapter_json := self.get_json(self.build_chapter_list_url(novel_id=series_id, page_no=page_no)):
            if not isinstance(chapter_json, list):
                raise errors.ParseError("Expect chapter json response to be a list.")

            for idx, chapter_data in enumerate(chapter_json, start=len(chapter_list)):
                pub_date_str = chapter_data["post_date"]
                chapter = data.Chapter(
                    url=chapter_data["permalink"],
                    chapter_no=idx,
                    slug=chapter_data["post_name"],
                    title=chapter_data["post_title"],
                    pub_date=datetime.datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S") if pub_date_str else None,
                )
                chapter_list.append(chapter)

            page_no += 1

        return chapter_list

    def get_status(self, page):
        """Extract the status of the series."""
        for elem in page.select("div.mb-4"):
            h3 = elem.find("h3")
            if h3 and h3.text.strip() == "Status":
                li = elem.find("li")
                value = li.text.strip().lower() if li else None
                return self.status_map[value] if value in self.status_map else data.NovelStatus.UNKNOWN
        return data.NovelStatus.UNKNOWN

    def get_cover_image(self, page):
        """Extract the cover image."""
        cover_image = page.find("img", alt=lambda alt: alt and alt.startswith("Thumbnail "))
        return data.Image(url=cover_image["data-src"]) if cover_image else None

    def post_processing(self, page, url, novel):
        """Post-process novel-scraping."""
        novel.extras = novel.extras or {}
        component_map = {
            h3.text.strip(): component for component in page.select("div.mb-4") if (h3 := component.find("h3"))
        }

        added_el = page.select_one("#js-current-pustaka")
        if added_el:
            novel.extras["Added to Library Count"] = added_el.text.strip()

        eye_icon = page.select_one(".fa-eye")
        eye_icon_parent = eye_icon.parent if eye_icon else None
        if eye_icon_parent:
            novel.extras["View Count"] = eye_icon_parent.text.strip()

        for title in ("Country", "Year"):
            if title in component_map:
                value = component_map[title].find("li").text.strip()
                if value.lower() != "n/a":
                    novel.extras[title] = value

        ratings_el = page.select_one(".post-ratings > p")
        ratings_text = ratings_el.text.strip() if ratings_el else ""
        match = re.match(r"\((?P<votes>\d+)\s+votes?,\s+(?P<score>\d+\.\d+)\s*\)", ratings_text)
        if match:
            ratings_votes = match.group("votes")
            ratings_score = match.group("score")
            novel.extras["Rating"] = f"{ratings_score} ({ratings_votes} vote(s))"


@html.register_html_filter(name="wuxiarealm.remove_chapter_controls")
def chapter_controls_filter(html_tree: Tag) -> None:
    """Html Filter to Remove Chapter Controls Mixed with Chapter Content."""
    for selector in (
        ".chapternav",
        ".code-block-1",
        ".code-block-2",
        ".code-block-3",
        "[title='Edited Translated']",
    ):
        for element in html_tree.select(selector):
            html.remove_element(element)


class WuxiaRealmChapterScraper(ChapterScraper):
    """Chapter Scraper for WuxiaRealm.com."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"wuxiarealm.com/(?P<NovelID>[\w\d-]+)/(?P<ChapterID>[\w\d-]+)/"
    content_selector = Selector("#soop")
    content_filters = ChapterScraper.content_filters + ["wuxiarealm.remove_chapter_controls"]
