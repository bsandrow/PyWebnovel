"""LightNovelBastion scrapers."""

import datetime
import itertools
import logging
import re

from bs4 import BeautifulSoup, Tag

from webnovel.data import Chapter, NovelStatus, Person
from webnovel.html import remove_element
from webnovel.logs import LogTimer
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector

from .divinedaolibrary import Volume

SITE_NAME = "LightNovelBastion"
logger = logging.getLogger(__name__)
timer = LogTimer(logger)


def is_empty_paragraph(tag: Tag) -> bool:
    """Test if the tag is a <p> and has no content."""
    return tag.name == "p" and tag.text.strip() == ""


class ChapterScraper(ChapterScraperBase):
    """Scraper for LightNovelBastion.com chapter content."""

    site_name = SITE_NAME
    url_pattern = (
        HTTPS_PREFIX
        + r"lightnovelbastion.com/novel/(?P<NovelID>[\w\d-]+)/(?P<VolumeID>[\w\d-]+)/(?P<ChapterID>[\w\d-]+)/?"
    )
    content_selector = Selector(".reading-content div.text-left")

    def post_process_content(self, chapter, content):
        """Post-Process Chapter Content."""
        # Remove all of the ads and their elements. Even if the ads are just
        # blank, the elements should still be removed lest they affect the
        # layout of the page.
        for tag in itertools.chain(
            content.select(".reportline"),
            content.select(".ezoic-adpicker-ad"),
            content.select(".ezoic-adpicker-ad"),
            content.select(".ezoic-ad"),
            content.select(".ezoic-autoinsert-ad"),
            content.select(".lnbad-tag"),
            content.select("span[data-ez-ph-id]"),
        ):
            remove_element(tag)


class NovelScraper(NovelScraperBase):
    """Scraper for LightNovelBastion.com."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"lightnovelbastion.com/novel/(?P<NovelID>[\w\d-]+)/"
    title_selector = Selector(".profile-manga .post-title h3")
    status_map = {"ongoing": NovelStatus.ONGOING, "completed": NovelStatus.COMPLETED}
    cover_image_url_selector = Selector(".summary_image img", attribute="data-src")
    extra_css = """
    blockquote {
        max-width: 750px;
        margin: 15px;
        padding: 15px;
        font-size: 16px;
        /*
         * Originally, the background was #eee, but that doesn't work when the
         * surrounding background is dark. Since some readers will do this,
         * switching this to rgba() so that I can define the alpha channel
         * works.  So this is #eee converted to rgba() with a 50% alpha channel
         * defined.
         */
        background: rgba(238, 238, 238, .5);
        border-left: 5px solid #428bca;
    }
    """

    def get_title(self, page: BeautifulSoup) -> str:
        """Extract the novel's title."""
        title_el = page.select_one(".profile-manga .post-title h3")
        for badge in title_el.select(".manga-title-badges"):
            remove_element(badge)
        return title_el.text.strip()

    def get_genres(self, page: BeautifulSoup) -> list[str]:
        """Extract genres listed for this novel."""
        return [genre.text for genre in page.select(".genres-content > a")]

    def get_summary(self, page: BeautifulSoup) -> str | Tag:
        """Extract the Novel's summary."""
        content = page.select_one(".summary__content")

        for tag in content.select(".lnbad-tag"):
            remove_element(tag)

        return content

    def get_author(self, page):
        """Extract the author from the page content."""
        author_content = page.select_one(".author-content")
        author_text = author_content.text.strip()
        return Person(name=author_text)
        # return [Person(name=author_name) for author_name in re.split(r"\s*,\s*", author_text)]

    def get_status(self, page):
        """Extract the novel's status."""
        status_heading = page.find("h5", text=re.compile("Status"))
        if not status_heading:
            return NovelStatus.UNKNOWN
        status_text = status_heading.parent.find_next_sibling("div")
        if not status_text:
            return NovelStatus.UNKNOWN
        return self.status_map.get(status_text.text.strip().lower(), NovelStatus.UNKNOWN)

    def get_novel_id(self, url: str) -> str:
        """Extract the novel's id from the url."""
        return match.group("NovelID") if (match := re.match(self.url_pattern, url)) else ""

    @staticmethod
    def _date(release_date_el: Tag) -> datetime.datetime | None:
        """Extract a datetime from the release date element."""
        if not release_date_el or not (date_string := release_date_el.text.strip()):
            return None

        if match := re.search(r"(\d+) hours? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(hours=int(match.group(1)))

        if match := re.search(r"(\d+) minutes? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(minutes=int(match.group(1)))

        if match := re.search(r"(\d+) seconds? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(seconds=int(match.group(1)))

        if match := re.search(r"(\d+) days? ago", date_string):
            return datetime.datetime.now() - datetime.timedelta(days=int(match.group(1)))

        return datetime.datetime.strptime(date_string, "%B %d, %Y")

    @timer("fetching chapters list")
    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances."""
        volumes = []
        chapters = []
        next_chapter_no = 0

        # TODO put in work to do something with the parsed volumes

        for chapter_list_el in reversed(page.select("ul.sub-chap")):
            volume_name_el = chapter_list_el.parent.find_previous_sibling("a")
            volume = Volume(name=volume_name_el.text if volume_name_el else None, insert_before=next_chapter_no)
            volume_chapters = [
                Chapter(
                    url=(url := chapter_li.select_one("A").get("href")),
                    title=Chapter.clean_title(chapter_li.select_one("A").text.strip()),
                    chapter_no=idx,
                    pub_date=self._date(release_date_el=chapter_li.select_one(".chapter-release-date")),
                    slug=ChapterScraper.get_chapter_slug(url),
                )
                for idx, chapter_li in enumerate(
                    reversed(chapter_list_el.select(".wp-manga-chapter")), start=next_chapter_no
                )
            ]
            volumes.append(volume)
            next_chapter_no += len(volume_chapters)
            chapters += volume_chapters

        return chapters
