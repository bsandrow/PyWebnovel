"""WuxiaRealm.com scrapers and utilities."""

import logging
import re
from typing import Union

from bs4 import BeautifulSoup, Comment

from webnovel import data
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraper, NovelScraper, Selector

SITE_NAME = "WuxiaRealm.com"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class ScribbleHubScraper(NovelScraper):
    """Novel Scraper for WuxiaRealm.com."""

    url_pattern = HTTPS_PREFIX + r"wuxiarealm\.com/novel/(?P<NovelID>[\w\d-]+)/"
    url_cache: dict
    status_map = {
        "ongoing": data.NovelStatus.ONGOING,
        "completed": data.NovelStatus.COMPLETED,
        "hiatus": data.NovelStatus.HIATUS,
    }

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
        return list(BeautifulSoup(series_json["content"]["rendered"], "html.parser").children)[0]

    def get_genres(self, page):
        """Extract genres."""
        url = self.get_series_json_url(page)
        series_json = self.get_series_json(url)
        series_id = series_json["id"]
        genre_url = f"https://wuxiarealm.com/wp-json/wp/v2/genre?post={series_id}"
        genres_json = self.get_series_json(genre_url)
        return [genre["name"] for genre in genres_json]

    def get_tags(self, page):
        """
        Extract tags.

        For now, trying to use this method to access the tags list results in a
        401, so just do nothing.
        """
        # url = self.get_series_json_url(page)
        # series_json = self.get_series_json(url)
        # series_id = series_json["id"]
        # tags_url = f"https://wuxiarealm.com/wp-json/wp/v2/tags?post={series_id}"
        # tags_json = self.get_series_json(tags_url)
        # return [tag["name"] for genre in tags_url]
        return None

    def get_author(self, page):
        """Return the author."""
        for elem in page.select("div.mb-4"):
            h3 = elem.find("h3")
            if h3 and h3.text.strip() == "Author":
                li = elem.find("li")
                if li and li.text.strip().lower() != "n/a":
                    return data.Person(name=li.text.strip())
        return None

    def get_status(self, page):
        """Extract the status of the series."""
        for elem in page.select("div.mb-4"):
            h3 = elem.find("h3")
            if h3 and h3.text.strip() == "Status":
                li = elem.find("li")
                return self.status_map.get(li.text.strip().lower()) if li else data.NovelStatus.UNKNOWN
        return data.NovelStatus.UNKNOWN

    def get_cover_image(self, page):
        """Extract the cover image."""
        comment = page.find(
            text=lambda text: isinstance(text, Comment) and comment.string.strip().lower() == "novel thumbnail"
        )
        img = comment.next_sibling.find("img") if comment else None
        return data.Image(url=img["href"]) if img else None

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
