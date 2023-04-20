"""NovelCool.com scrapers and utils."""

import datetime
import re

from webnovel.data import Chapter, Image, NovelStatus, Person
from webnovel.html import remove_element
from webnovel.scraping import HTTPS_PREFIX, ChapterScraper, NovelScraper, Selector

SITE_NAME = "NovelCool.com"


class NovelCoolScraper(NovelScraper):
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
        return self.status_map.get(elem.text.lower().strip(), NovelStatus.UNKNOWN)

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

    def post_process_content(self, chapter, content):
        """Remove chapter title."""
        ch_title = content.select_one(".chapter-title")
        if ch_title:
            remove_element(ch_title)

    def get_content(self, page):
        """Extract the section of the HTML from page that contains the chapter's content."""
        content_element = None

        # TODO Move these to HTML filters
        chapter_report = page.select_one(".chapter-section-report")
        if chapter_report:
            remove_element(chapter_report)

        chapter_start_mark = page.select_one(".chapter-start-mark")
        if chapter_start_mark:
            content_element = chapter_start_mark.parent
            remove_element(chapter_start_mark)

        chapter_end_mark = page.select_one(".chapter-end-mark")
        if chapter_end_mark:
            if not content_element:
                content_element = chapter_end_mark.parent
            remove_element(chapter_end_mark)

        if content_element:
            return content_element

        raise ValueError("Unable to find .chapter-start-mark / .chapter-end-mark")
