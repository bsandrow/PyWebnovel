"""NovelCool.com scrapers and utils."""

import datetime
import re

from webnovel import errors
from webnovel.data import Chapter, Image, NovelStatus, Person
from webnovel.html import register_html_filter, remove_element
from webnovel.scraping import HTTPS_PREFIX, ChapterScraper, NovelScraperBase, Selector

SITE_NAME = "NovelCool.com"


@register_html_filter(name="remove_title.novelcool")
def title_filter(html) -> None:
    """
    Remove duplicated title.

    NotelCool doesn't seem to have the same issue where the title embedded in
    the content differs from the listing / heading title for chapters, so we
    only need to remove it to prevent a duplicate title from showing up on the
    page.
    """
    title = html.select_one(".chapter-title")
    if title:
        remove_element(title)


@register_html_filter(name="remove_controls.novelcool")
def control_filter(html) -> None:
    """Remove page controls from the content."""
    for element in (
        html.select_one(".chapter-section-report"),
        html.select_one(".chapter-start-mark"),
        html.select_one(".chapter-end-mark"),
    ):
        if element:
            remove_element(element)


class NovelCoolScraper(NovelScraperBase):
    """Scraper for NovelCool.com novels."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"novelcool.com/novel/(?P<NovelID>[\w\d_-]+).html"
    status_map = {"ongoing": NovelStatus.ONGOING}

    def get_title(self, page):
        """Return the novel title."""
        novel_data_el = page.find("script", string=lambda t: t and "BOOK_ID" in t)
        if novel_data_el and (match := re.search(r'var BOOK_NAME = "(?P<title>[^"]+)"', novel_data_el.text)):
            return match.group("title")
        return None

    def get_author(self, page):
        """Return the novel author."""
        elem = page.select_one("[itemprop='creator']")
        return Person(name=elem.text)

    def get_status(self, page):
        """Return the novel status."""
        elem = page.select_one(".bk-cate-type1")
        return self.status_map.get(elem.text.lower().strip(), NovelStatus.UNKNOWN) if elem else NovelStatus.UNKNOWN

    def get_cover_image(self, page):
        """Return the cover image."""
        novel_data_el = page.find("script", string=lambda t: t and "BOOK_ID" in t)
        if novel_data_el and (match := re.search(r'var BOOK_COVER = "(?P<cover_url>[^"]+)"', novel_data_el.text)):
            return Image(url=match.group("cover_url"))
        return None

    def get_genres(self, page):
        """Return a list of genres."""
        genre_els = page.select(".bk-cate-item:not(.bk-cate-type1)")
        return list({genre_el.text.strip() for genre_el in genre_els})

    def get_summary(self, page):
        """Return the summary of the novel if there is one."""
        summary_el = page.select_one(".bk-summary-txt.all")
        return summary_el.text if summary_el else None

    def get_chapters(self, page, url):
        """Return the list of chapters."""
        chapter_els = page.select(".chp-item")
        chapters = []

        for idx, element in enumerate(reversed(chapter_els), 1):
            time = element.select_one(".chapter-item-time")
            ch = Chapter(
                url=(url := element.find("a").get("href")),
                title=element.find("a").get("title"),
                chapter_no=idx,
                slug=NovelCoolChapterScraper.get_chapter_slug(url),
                pub_date=datetime.datetime.strptime(time.text.strip(), "%b %d, %Y").date() if time else None,
            )
            chapters.append(ch)

        return chapters


class NovelCoolChapterScraper(ChapterScraper):
    """Scraper for NovelCool.com chapters."""

    site_name = SITE_NAME
    url_pattern = re.compile(HTTPS_PREFIX + r"novelcool.com/chapter/(?P<ChapterID>[\w\d-]+)/\d+/")
    content_filters = ["remove_controls.novelcool"] + ChapterScraper.content_filters + ["remove_title.novelcool"]

    def get_content(self, page):
        """Extract the section of the HTML from page that contains the chapter's content."""
        for element in [page.select_one(".chapter-start-mark"), page.select_one(".chapter-end-mark")]:
            if element:
                return element.parent
        raise errors.ChapterContentNotFound("Unable to find .chapter-start-mark / .chapter-end-mark")
