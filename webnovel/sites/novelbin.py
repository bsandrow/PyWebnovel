"""NovelBin scrapers and utilities."""

import logging
import re

from pyrate_limiter import Limiter, RequestRate

from webnovel import data, errors
from webnovel.data import Chapter, NovelStatus
from webnovel.html import DEFAULT_FILTERS, register_html_filter, remove_element
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraper, NovelScraperBase, Selector

SITE_NAME = "NovelBin.net"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)
CHAPTER_LIMITER = Limiter(RequestRate(10, 60))  # 10 per minute

DOMAINS = [
    r"novel-?bin\.com",
    r"novel-?bin\.net",
    r"novel-?bin\.org",
]

DOMAIN_RE = r"(?:www\.)(?:" + "|".join(DOMAINS) + r")"


@register_html_filter(name="remove_check_back_soon_msg")
def check_back_soon_filter(html):
    """
    Remove the 'Check back soon for more chapters' message.

    When you reach the most recent chapter, NovelBin adds a message:

        The Novel will be updated first on this website. Come back and continue
        reading tomorrow, everyone!

    Remove this, as it's not part of the chapter's content.
    """
    for element in html.select(".schedule-text"):
        remove_element(element)


class NovelBinChapterScraper(ChapterScraper):
    """Scraper for NovelBin.net chapter content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + DOMAIN_RE + r"/(?:n|novel-?bin)/(?P<NovelID>[\w\d-]+)/(?P<ChapterID>[\w\d-]+)"
    content_selector = Selector("#chr-content")
    content_filters = DEFAULT_FILTERS + ["remove_check_back_soon_msg"]

    def get_limiter(self):
        """Return custom rate limiter."""
        return CHAPTER_LIMITER

    def post_process_content(self, chapter, content) -> None:
        """Do extra chapter title processing."""
        direct_descendants = content.find_all(recursive=False)

        while len(direct_descendants) == 1:
            content = direct_descendants[0]
            direct_descendants = content.find_all(recursive=False)

        title_header = content.find(["h4", "h3", "p"])
        if title_header and (match := Chapter.is_title_ish(title_header.text)):
            chapter.title = Chapter.clean_title(match.group(0))
            remove_element(title_header)

        if chapter.title is not None:
            chapter.title = re.sub(r"Side Story  (\d+):", r"Side Story Chapter \1:", chapter.title, re.IGNORECASE)
            chapter.title = re.sub(r"(Chapter \d+)- ", r"\1: ", chapter.title, re.IGNORECASE)


class NovelBinScraper(NovelScraperBase):
    """Scraper for NovelBin.net."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + DOMAIN_RE + r"/(?:n|novel-?bin)/(?P<NovelID>[\w\d-]+)"
    title_selector = Selector(".col-novel-main > .col-info-desc > .desc > .title")
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED}
    genre_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(3) > a")
    summary_selector = Selector("div.tab-content div.desc-text")
    cover_image_url_selector = Selector("#novel div.book > img", attribute="src")
    chapter_list_api_url = "https://novelbin.net/ajax/chapter-archive?novelId={novel_id}"

    extra_css = ".desc-text { white-space: pre-line; }"

    def get_author(self, page):
        """Extract the author from the page content."""
        metainfo = page.select_one("UL.info-meta")
        for infoitem in metainfo("li"):
            if "Author" in infoitem.text:
                author_link = infoitem.find("a")
                author_name = author_link.text.strip()
                author_url = author_link.get("href")
                return data.Person(name=author_name, url=author_url)
        return None

    @classmethod
    def get_novel_id(cls, url: str) -> str:
        """Return the novel id from the URL."""
        novel_id = match.group("NovelID") if (match := re.match(cls.url_pattern, url)) else None
        if novel_id:
            novel_id = re.sub(r"-nov-?\d+$", "", novel_id)
        return novel_id

    def get_status(self, page):
        """
        Get novel status.

        Can't get status with selectors alone, so need to override.
        """
        items = page.select(".col-novel-main > .col-info-desc > .desc > .info-meta > li")
        for item in items:
            section = item.find("h3").text.strip()
            if section.lower() in ("status", "status:"):
                return self.status_map.get(item.find("a").text.strip().lower(), NovelStatus.UNKNOWN)
        return NovelStatus.UNKNOWN

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances for NovelBin.net."""
        novel_id = self.get_novel_id(url)

        # This ajax requests also returns the list, but as a <select> with
        # <option>s so parsing will be different.
        # page = self.get_page(f"https://novelbin.net/ajax/chapter-option?novelId={novel_id}")

        page = self.get_page(self.chapter_list_api_url.format(novel_id=novel_id))

        return [
            Chapter(
                url=(url := chapter_li.select_one("A").get("href")),
                title=(title := Chapter.clean_title(chapter_li.select_one("A").get("title"))),
                chapter_no=idx,
                slug=NovelBinChapterScraper.get_chapter_slug(url),
            )
            for idx, chapter_li in enumerate(page.select("UL.list-chapter > LI"))
        ]

    def post_processing(self, page, url, novel):
        """Parse out additional Novel metadata."""
        novel.extras = novel.extras or {}

        info_metas = page.select(".info-meta")
        if len(info_metas) < 1:
            raise errors.ParseError("Unable to find any elements for selector: .info-meta")
        if len(info_metas) > 1:
            raise errors.ParseError("Found multiple elements for selector when only one was expected: .info-meta")
        info_meta = info_metas[0]

        for li in info_meta.find_all("li", recursive=False):
            children = list(li.children)
            title = children[0].text.strip() if children and children[0] else ""

            if title.lower() == "alternative names:":
                novel.extras["Alternative Titles"] = re.split(r"\s*,\s+", children[1].text.strip())

            if title.lower() == "source:":
                novel.extras["'Source'"] = children[1].text.strip()

        rating_control = page.select_one("[itemprop='aggregateRating']")
        if rating_control:
            rating_value = rating_control.select_one("[itemprop='ratingValue']")
            rating_max = rating_control.select_one("[itemprop='bestRating']")
            votes = rating_control.select_one("[itemprop='reviewCount']")
            novel.extras["Rating"] = f"{rating_value.text} out of {rating_max.text} [{votes.text} vote(s)]"
