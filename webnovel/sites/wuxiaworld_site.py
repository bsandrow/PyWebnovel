import re

from webnovel.data import NovelStatus, Chapter
from webnovel.scraping import NovelScraper, Selector, HTTPS_PREFIX

NOVEL_URL_PATTERN = HTTPS_PREFIX + r"wuxiaworld\.site/novel/([\w-]+)/"


def validate_url(url: str) -> bool:
    return re.match(NOVEL_URL_PATTERN, url) is not None


class WuxiaWorldDotSiteScraper(NovelScraper):
    site_name = "WuxiaWorld.site"

    title_selector = Selector("div.post-title > h1")
    summary_selector = Selector("div.description-summary > div.summary__content")
    status_selector = Selector("div.post-status > div:nth-child(2) > .summary-content")
    status_map = {
        "OnGoing": NovelStatus.ONGOING, "Ongoing": NovelStatus.ONGOING, "Completed": NovelStatus.COMPLETED
    }
    author_name_selector = Selector("div.author-content > a")
    author_url_selector = Selector("div.author-content > a", attribute="href")
    genre_selector = Selector("div.genres-content > a")
    cover_image_url_selector = Selector("div.summary_image img", attribute="data-src")

    chapter_content_selector = Selector("div.reading-content > div:nth-child(2)")

    @staticmethod
    def get_novel_id(url: str) -> str:
        match = re.match(NOVEL_URL_PATTERN, url)
        return match.group(1) if match is not None else None

    def get_chapters(self, page, url: str) -> list:
        url = url if url.endswith("/") else f"{url}/"
        chapter_list_url = f"{url}ajax/chapters/"
        chapter_list_page = self.get_page(chapter_list_url, method="post")

        def get_chapter_no(title: str):
            match = re.match(r"^\s*Chapter\s*(\d+)\s*", title, re.IGNORECASE)
            return match.group(1) if match is not None else None

        return [
            Chapter(
                url=chapter_li.select_one("a").get("href"),
                title=(title := chapter_li.select_one("a").text.strip()),
                chapter_no=get_chapter_no(title),
            )
            for chapter_li in chapter_list_page.select("li.wp-manga-chapter")
        ]
